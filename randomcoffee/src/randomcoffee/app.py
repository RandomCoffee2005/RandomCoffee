import datetime as dt
import random
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Any
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from envconfig import Config

from .auth import get_current_user_context, get_dbpath, require_admin
from .jwt_utils import issue_jwt
from .schemas import (
    LoginStartRequest,
    LoginStartResponse,
    NotificationWithJwtResponse,
    NotificationView,
    NotificationsWithJwtResponse,
    SignInRequest,
    SignInResponse,
    TriggerPairingResponse,
    UserUpdateRequest,
    UserWithJwtResponse,
    UserView,
)
from .storage import (
    connect,
    consume_otp_and_get_user,
    create_pairing,
    create_user,
    fetch_pairing_for_user,
    init_db,
    issue_otp,
    list_active_user_ids,
    list_pairings_for_user,
    mark_pairing_met,
)


def to_user_view(row: dict[str, Any]) -> UserView:
    return UserView(
        id=str(row["id"]),
        email=row["email"],
        full_name=row["full_name"],
        contact_info=row["contact_info"],
        is_active=bool(row["is_active"]),
        is_admin=bool(row["is_admin"]),
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
        status="MET" if int(row["meeting_happened"]) else "UNMET",
        week_key=week_key,
        created_at=created_at,
    )


def create_app(dbpath: str | None = None) -> FastAPI:
    resolved_dbpath = dbpath or Config().dbpath
    login_start_limit = 5
    login_start_window = dt.timedelta(hours=1)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.dbpath = resolved_dbpath
        app.state.jwt_secret = secrets.token_urlsafe(48)
        app.state.login_start_attempts: dict[str, list[dt.datetime]] = {}
        init_db(app.state.dbpath)
        yield

    app = FastAPI(title="RandomCoffee API", lifespan=lifespan)

    @app.post("/login_start", response_model=LoginStartResponse)
    def login_start(payload: LoginStartRequest, request: Request) -> LoginStartResponse:
        now = dt.datetime.now(dt.UTC)
        attempts_by_email: dict[str, list[dt.datetime]] = request.app.state.login_start_attempts
        attempts = attempts_by_email.get(payload.email, [])
        valid_attempts = [ts for ts in attempts if now - ts < login_start_window]
        if len(valid_attempts) >= login_start_limit:
            return JSONResponse(status_code=421, content={"error": "too many requests"})
        valid_attempts.append(now)
        attempts_by_email[payload.email] = valid_attempts

        try:
            code, expires_at = issue_otp(get_dbpath(request), payload.email)
            # TODO: отправить OTP через email (payload.email, code, expires_at).
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return LoginStartResponse()

    @app.post("/login", response_model=SignInResponse)
    def sign_in(payload: SignInRequest, request: Request) -> SignInResponse:
        row = consume_otp_and_get_user(get_dbpath(request), payload.email, payload.otp)
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = issue_jwt(str(row["id"]), request.app.state.jwt_secret)
        return SignInResponse(jwt=token)

    @app.get("/myprofile", response_model=UserWithJwtResponse)
    def get_myprofile(
        request: Request,
        context: tuple[dict[str, Any], str] = Depends(get_current_user_context),
    ) -> UserWithJwtResponse:
        current_user, renewed_jwt = context
        return UserWithJwtResponse(user=to_user_view(current_user), jwt=renewed_jwt)

    @app.patch("/myprofile", response_model=UserWithJwtResponse)
    def update_me(
        payload: UserUpdateRequest,
        request: Request,
        context: tuple[dict[str, Any], str] = Depends(get_current_user_context),
    ) -> UserWithJwtResponse:
        current_user, renewed_jwt = context
        updates: dict[str, object] = {}
        if payload.full_name is not None:
            updates["name"] = payload.full_name
        if payload.contact_info is not None:
            updates["contact_info"] = payload.contact_info
        if payload.is_active is not None:
            updates["active"] = int(payload.is_active)

        if not updates:
            return UserWithJwtResponse(user=to_user_view(current_user), jwt=renewed_jwt)

        set_clause = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values())
        values.append(current_user["id"])

        with connect(get_dbpath(request)) as conn:
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        updated_data = dict(updated)
        updated_data["is_admin"] = int(updated_data["email"] == "admin@example.com" or Config().is_admin(updated_data["email"]))
        return UserWithJwtResponse(user=to_user_view(updated_data), jwt=renewed_jwt)

    @app.get("/profile/{user_id}")
    def get_profile(user_id: str, request: Request):
        from .storage import fetch_user_by_id
        user = fetch_user_by_id(get_dbpath(request), user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return {"user": to_user_view(user)}

    @app.get("/notifications", response_model=NotificationsWithJwtResponse)
    def get_notifications(
        request: Request,
        status: Literal["attended", "not-attended", "all"] | None = None,
        context: tuple[dict[str, Any], str] = Depends(get_current_user_context),
    ) -> NotificationsWithJwtResponse:
        current_user, renewed_jwt = context
        current_user_id = str(current_user["id"])
        status_filter = None
        if status == "attended":
            status_filter = "MET"
        elif status == "not-attended":
            status_filter = "UNMET"
        rows = list_pairings_for_user(get_dbpath(request), current_user_id, status_filter)

        return NotificationsWithJwtResponse(
            notifications=[pairing_to_notification(row, current_user_id) for row in rows],
            jwt=renewed_jwt,
        )

    @app.get("/notifications/last", response_model=NotificationWithJwtResponse)
    def get_last_notification(
        request: Request,
        context: tuple[dict[str, Any], str] = Depends(get_current_user_context),
    ) -> NotificationWithJwtResponse:
        current_user, renewed_jwt = context
        current_user_id = str(current_user["id"])
        rows = list_pairings_for_user(get_dbpath(request), current_user_id)
        row = rows[0] if rows else None

        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No notifications")
        return NotificationWithJwtResponse(notification=pairing_to_notification(row, current_user_id), jwt=renewed_jwt)

    @app.post("/notifications/{notification_id}/confirm", response_model=NotificationWithJwtResponse)
    def confirm_notification(
        notification_id: str,
        request: Request,
        context: tuple[dict[str, Any], str] = Depends(get_current_user_context),
    ) -> NotificationWithJwtResponse:
        current_user, renewed_jwt = context
        current_user_id = str(current_user["id"])
        updated = mark_pairing_met(get_dbpath(request), current_user_id, notification_id)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

        row = fetch_pairing_for_user(get_dbpath(request), current_user_id, notification_id)

        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        return NotificationWithJwtResponse(notification=pairing_to_notification(row, current_user_id), jwt=renewed_jwt)

    @app.post("/admin/pairing", response_model=TriggerPairingResponse)
    def trigger_pairings(
        request: Request,
        context: tuple[dict[str, Any], str] = Depends(require_admin),
    ) -> TriggerPairingResponse:
        _, renewed_jwt = context
        now = dt.datetime.now(dt.UTC)
        user_ids = list_active_user_ids(get_dbpath(request))

        # TODO: Реализовать алгоритм подбора пар
        # Временно: простой случайный алгоритм
        random.shuffle(user_ids)
        pairs: list[tuple[str, str]] = []
        for i in range(0, len(user_ids) - 1, 2):
            pairs.append((user_ids[i], user_ids[i + 1]))

        for first, second in pairs:
            pair_id = f"{now.isoformat()}|{uuid.uuid4()}"
            create_pairing(get_dbpath(request), first, second, pair_id)
            # TODO: отправить уведомления пользователям о новой встрече.

        return TriggerPairingResponse(pairs_created=len(pairs), notifications_created=len(pairs), jwt=renewed_jwt)

    return app


app = create_app()
