from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from envconfig import DBConfig

from .jwt_utils import decode_jwt
from db.sql import connect, fetch_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    secret = request.app.state.jwt_secret
    try:
        payload = decode_jwt(credentials.credentials, secret)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    with connect(readonly=True) as conn:
        user = fetch_user_by_id(conn, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user_context)) -> dict[str, Any]:
    if not DBConfig.instance().is_admin(user["email"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user
