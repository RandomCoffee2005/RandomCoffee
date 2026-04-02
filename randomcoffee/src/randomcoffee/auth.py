from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_utils import decode_jwt, issue_jwt
from .storage import fetch_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_dbpath(request: Request) -> str:
    return request.app.state.dbpath


def get_current_user_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> tuple[dict[str, Any], str]:
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

    renewed_jwt = issue_jwt(str(user["id"]), secret)
    return user, renewed_jwt
def require_admin(context: tuple[dict[str, Any], str] = Depends(get_current_user_context)) -> tuple[dict[str, Any], str]:
    user, renewed_jwt = context
    if not bool(user["is_admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user, renewed_jwt
