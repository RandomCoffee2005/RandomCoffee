import asyncio
import datetime as dt
from pathlib import Path
import os
import subprocess
import sys
from typing import Any
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status as http_status
from fastapi.responses import JSONResponse

from fastAPI.auth import get_current_user_context, require_admin
from fastAPI.jwt_utils import issue_jwt
from fastAPI.schemas import (
    ConfirmRequest,
    EmptyResponse,
    LoginStartRequest,
    LoginStartResponse,
    NotificationView,
    ProfileView,
    SignInRequest,
    SignInResponse,
    UserUpdateRequest,
)
from db.sql import (
    consume_otp_and_get_user,
    connect,
    fetch_user_by_id,
    issue_otp,
    list_pairings_for_user,
    mark_pairing_met,
    get_user_interests
)
from emailsender import send_email
from interest_names import interest_list

router = APIRouter()
LOGIN_START_LIMIT = 5
LOGIN_START_WINDOW = dt.timedelta(hours=1)
SRC_ROOT = Path(__file__).resolve().parents[1]


def ensure_active_user(context: dict[str, Any]) -> None:
    if not bool(context["is_active"]):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Forbidden")


def to_profile_view(row: dict[str, Any], interests: list[int] | None = None) -> ProfileView:
    return ProfileView(
        id=str(row["id"]),
        name=row["name"],
        contact_info=row["contact_info"],
        about_me=row["about_me"],
        interests=sorted(interests or []),
    )

def pairing_to_notification(row: Any, current_user_id: str) -> NotificationView:
    pair_id = str(row["pair_id"])
    created_at = str(row["created_at"])
    week_key = dt.datetime.fromisoformat(created_at).strftime("%G-W%V")
    partner_user_id = str(row["id2"] if str(row["id1"]) == current_user_id else row["id1"])
    return NotificationView(
        id=pair_id,
        user_id=current_user_id,
        partner_user_id=partner_user_id,
        partner_name=row["partner_name"],
        met=bool(row["meeting_happened"]),
        week_key=week_key,
        created_at=created_at,
    )


def normalize_interests(interests: list[int] | None) -> list[int] | None:
    if interests is None:
        return None

    for interest_id in interests:
        if interest_id < 0 or interest_id >= len(interest_list):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"interest ID must be between 0 and {len(interest_list) - 1}",
            )

    return list(dict.fromkeys(interests))


def replace_user_interests(conn: Any, user_id: str, interests: list[int]) -> None:
    conn.execute("DELETE FROM user_interests WHERE id = ?", (user_id,))
    if interests:
        conn.executemany(
            "INSERT INTO user_interests (id, interest_id) VALUES (?, ?)",
            [(user_id, interest_id) for interest_id in interests],
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

    email = payload.email.strip().lower()
    with connect() as conn:
        code, expires_at = issue_otp(conn, email)
        conn.commit()

    subject = "Random Coffee OTP"
    body = (
        f"Your Random Coffee login code is {code}.\n"
        f"It expires at {expires_at}.\n\n"
        "If you did not request this code, you can ignore this email."
    )
    try:
        sent = asyncio.run(send_email(email, subject, body))
    except Exception:
        sent = False

    if not sent:
        with connect() as conn:
            conn.execute("DELETE FROM otps WHERE email = ?", (email,))
            conn.commit()
        raise HTTPException(
            status_code=http_status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send OTP email",
        )

    return LoginStartResponse()


@router.post("/login", response_model=SignInResponse)
def sign_in(payload: SignInRequest, request: Request) -> SignInResponse:
    with connect() as conn:
        row = consume_otp_and_get_user(conn, payload.email, payload.otp)
        conn.commit()
    if row is None:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = issue_jwt(str(row["id"]), request.app.state.jwt_secret)
    return SignInResponse(jwt=token)


@router.get("/myprofile", response_model=ProfileView)
def get_myprofile(context: dict[str, Any] = Depends(get_current_user_context)) -> ProfileView:
    user_id = str(context["id"])
    with connect(readonly=True) as conn:
        interests = get_user_interests(conn, user_id)
    return to_profile_view(context, interests)


@router.patch("/myprofile", response_model=EmptyResponse)
def update_me(
    payload: UserUpdateRequest,
    request: Request,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> EmptyResponse:
    user_id = str(context["id"])
    updates: list[tuple[str, object]] = []
    for field, value in (
        ("name", payload.name),
        ("contact_info", payload.contact_info),
        ("about_me", payload.about_me),
    ):
        if value is not None:
            updates.append((field, value))
    if payload.is_active is not None:
        updates.append(("active", int(payload.is_active)))

    normalized_interests = normalize_interests(payload.interests)

    if not updates and normalized_interests is None:
        return EmptyResponse()

    with connect() as conn:
        if updates:
            set_clause = ", ".join(f"{field} = ?" for field, _ in updates)
            values = [value for _, value in updates]
            values.append(user_id)
            cur = conn.execute(f"UPDATE users SET {set_clause} WHERE id = ? RETURNING 1", values)
            if cur.fetchone() is None:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND,
                                    detail="User not found")
        else:
            cur = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND,
                                    detail="User not found")

        if normalized_interests is not None:
            replace_user_interests(conn, user_id, normalized_interests)
        conn.commit()
    return EmptyResponse()


@router.get("/profile/{user_id}", response_model=ProfileView)
def get_profile(user_id: str, request: Request) -> ProfileView:
    with connect(readonly=True) as conn:
        user = fetch_user_by_id(conn, user_id)
        if user is None or not bool(user["is_active"]):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        interests = get_user_interests(conn, user_id)
    return to_profile_view(user, interests)


@router.get("/profile_interests/{user_id}", response_model=list[int])
def get_profile_interests(user_id: str, request: Request) -> list[int]:
    with connect(readonly=True) as conn:
        user = fetch_user_by_id(conn, user_id)
        if user is None or not bool(user["is_active"]):
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND,
                                detail="User not found")
        interests = get_user_interests(conn, user_id)
    return sorted(interests)


# PLEASE do not use this in the frontend. Just import "interest_names"
@router.get("/interest_str/en", response_model=str)
def get_interest_str_en(request: Request, id: int) -> str:
    if id < 0 or id >= len(interest_list):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"interest ID must be between 0 and {len(interest_list) - 1}"
        )
    return interest_list[id]


@router.get("/notifications", response_model=list[NotificationView])
def get_notifications(
    request: Request,
    status: Literal["attended", "not-attended", "all"] | None = None,
    n: int | None = None,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> list[NotificationView]:
    if n is not None and n < 1:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="n must be positive"
        )

    current_user = context
    ensure_active_user(current_user)
    current_user_id = str(current_user["id"])
    met_filter: bool | None = None
    if status == "attended":
        met_filter = True
    elif status == "not-attended":
        met_filter = False
    with connect(readonly=True) as conn:
        rows = list_pairings_for_user(conn, current_user_id, met_filter, n)

    return [pairing_to_notification(row, current_user_id) for row in rows]


@router.post("/confirm", response_model=EmptyResponse)
def confirm_notification(
    payload: ConfirmRequest,
    request: Request,
    context: dict[str, Any] = Depends(get_current_user_context),
) -> EmptyResponse:
    current_user = context
    ensure_active_user(current_user)
    current_user_id = str(current_user["id"])
    with connect() as conn:
        updated = mark_pairing_met(conn, payload.notification_id, current_user_id)
        conn.commit()
    if not updated:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return EmptyResponse()


@router.post("/admin/pairing", response_model=EmptyResponse)
def trigger_pairings(context: dict[str, Any] = Depends(require_admin)) -> EmptyResponse:
    ensure_active_user(context)
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_ROOT}:{python_path}" if python_path else str(SRC_ROOT)

    try:
        subprocess.Popen(
            [sys.executable, "-m", "pairalgo"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start pairing process",
        )

    return EmptyResponse()
