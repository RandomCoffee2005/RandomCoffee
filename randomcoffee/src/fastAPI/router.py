import datetime as dt
from typing import Any
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status as http_status
from fastapi.responses import JSONResponse

from randomcoffee.auth import get_current_user_context, get_dbpath, require_admin
from randomcoffee.jwt_utils import issue_jwt
from randomcoffee.schemas import (
    ConfirmRequest,
    EmptyResponse,
    LoginStartRequest,
    LoginStartResponse,
    NotificationResponse,
    NotificationView,
    NotificationsResponse,
    SignInRequest,
    SignInResponse,
    UserResponse,
    UserUpdateRequest,
    UserView,
)
from randomcoffee.storage import (
    consume_otp_and_get_user,
    connect as storage_connect,
    fetch_pairing_for_user,
    fetch_user_by_id,
    issue_otp,
    list_pairings_for_user,
    mark_pairing_met,
)


router = APIRouter()
LOGIN_START_LIMIT = 5
LOGIN_START_WINDOW = dt.timedelta(hours=1)


def to_user_view(row: dict[str, Any]) -> UserView:
    return UserView(
        id=str(row["id"]),
        email=row["email"],
        full_name=row["full_name"],
        contact_info=row["contact_info"],
        is_active=bool(row["is_active"]),
    )


def pairing_to_notification(row: Any, current_user_id: str) -> NotificationView:
    pair_id = str(row["pair_id"])
    created_at = pair_id.split("|", maxsplit=1)[0] if "|" in pair_id else pair_id
    week_key = dt.datetime.fromisoformat(created_at).strftime("%G-W%V") if "|" in pair_id else ""
    partner_user_id = str(row["id2"] if str(row["id1"]) == current_user_id else row["id1"])
    return NotificationView(
        id=pair_id,
        user_id=current_user_id,
        partner_user_id=partner_user_id,
        partner_email=row["partner_email"],
        partner_full_name=row["partner_name"],
        met=bool(row["meeting_happened"]),
        week_key=week_key,
        created_at=created_at,
    )


@router.post("/login_start", response_model=LoginStartResponse)
def login_start(payload: LoginStartRequest, request: Request) -> LoginStartResponse:
    now = dt.datetime.now(dt.UTC)
    attempts_by_email: dict[str, list[dt.datetime]] = request.app.state.login_start_attempts
    attempts = attempts_by_email.get(payload.email, [])
    valid_attempts = [ts for ts in attempts if now - ts < LOGIN_START_WINDOW]
    if len(valid_attempts) >= LOGIN_START_LIMIT:
        return JSONResponse(status_code=421, content={"error": "too many requests"})
    valid_attempts.append(now)
    attempts_by_email[payload.email] = valid_attempts

    try:
        code, expires_at = issue_otp(get_dbpath(request), payload.email)
        # TODO: отправить OTP через email (payload.email, code, expires_at).
    except ValueError:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return LoginStartResponse()


@router.post("/login", response_model=SignInResponse)
def sign_in(payload: SignInRequest, request: Request) -> SignInResponse:
    row = consume_otp_and_get_user(get_dbpath(request), payload.email, payload.otp)
    if row is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = issue_jwt(str(row["id"]), request.app.state.jwt_secret)
    return SignInResponse(jwt=token)


@router.get("/myprofile", response_model=UserResponse)
def get_myprofile(context: dict[str, Any] = Depends(get_current_user_context)) -> UserResponse:
    return UserResponse(user=to_user_view(context))


@router.patch("/myprofile", response_model=UserResponse)
def update_me(
    payload: UserUpdateRequest,
    request: Request,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> UserResponse:
    current_user = context
    updates: dict[str, object] = {}
    if payload.full_name is not None:
        updates["name"] = payload.full_name
    if payload.contact_info is not None:
        updates["contact_info"] = payload.contact_info
    if payload.is_active is not None:
        updates["active"] = int(payload.is_active)

    if not updates:
        return UserResponse(user=to_user_view(current_user))

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(current_user["id"])

    with storage_connect(get_dbpath(request)) as conn:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        updated = conn.execute(
            """
            SELECT id, email, name AS full_name, contact_info, active AS is_active
            FROM users
            WHERE id = ?
            """,
            (current_user["id"],),
        ).fetchone()

    if updated is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(user=to_user_view(dict(updated)))


@router.get("/profile/{user_id}", response_model=UserResponse)
def get_profile(user_id: str, request: Request) -> UserResponse:
    user = fetch_user_by_id(get_dbpath(request), user_id)
    if user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(user=to_user_view(user))


@router.get("/notifications", response_model=NotificationsResponse)
def get_notifications(
    request: Request,
    status: Literal["attended", "not-attended", "all"] | None = None,
    n: int | None = None,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> NotificationsResponse:
    current_user = context
    current_user_id = str(current_user["id"])
    met_filter: bool | None = None
    if status == "attended":
        met_filter = True
    elif status == "not-attended":
        met_filter = False
    rows = list_pairings_for_user(get_dbpath(request), current_user_id, met_filter)
    if n is not None:
        if n < 1:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="n must be positive")
        rows = rows[:n]

    return NotificationsResponse(
        notifications=[pairing_to_notification(row, current_user_id) for row in rows],
    )


@router.post("/confirm", response_model=NotificationResponse)
def confirm_notification(
    payload: ConfirmRequest,
    request: Request,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> NotificationResponse:
    current_user = context
    current_user_id = str(current_user["id"])
    updated = mark_pairing_met(get_dbpath(request), current_user_id, payload.notification_id)
    if not updated:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Notification not found")

    row = fetch_pairing_for_user(get_dbpath(request), current_user_id, payload.notification_id)

    if row is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse(notification=pairing_to_notification(row, current_user_id))


@router.post("/admin/pairing", response_model=EmptyResponse)
def trigger_pairings(_: dict[str, Any] = Depends(require_admin)) -> EmptyResponse:
    # TODO: запускать генерацию пар в фоне
    # TODO: после генерации отправлять уведомления пользователям
    return EmptyResponse()