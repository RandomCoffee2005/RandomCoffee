from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from envconfig import config

from .jwt_utils import decode_jwt
from .storage import fetch_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_dbpath(request: Request) -> str:
    return request.app.state.dbpath


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

    user = fetch_user_by_id(get_dbpath(request), payload["userID"])
    if user is None or not bool(user["is_active"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user_context)) -> dict[str, Any]:
    if not config.is_admin(user["email"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user
