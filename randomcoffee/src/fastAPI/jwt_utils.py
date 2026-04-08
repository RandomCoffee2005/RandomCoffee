import datetime as dt
import hashlib
from collections import OrderedDict

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError


class JWTPayload(BaseModel):
    user_id: str
    expiration: int
    hash: str


def issue_jwt(user_id: str, secret: str, ttl_minutes: int = 30) -> str:
    now = dt.datetime.now(dt.UTC)
    expiration = now + dt.timedelta(minutes=ttl_minutes)
    hash = hashlib.sha256(f"{user_id}{now.isoformat()}".encode("utf-8")).hexdigest()

    payload = OrderedDict()
    payload["hash"] = hash
    payload["user_id"] = user_id
    payload["expiration"] = int(expiration.timestamp())

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str):
    try:
        payload = JWTPayload(**jwt.decode(token, secret, algorithms=["HS256"]))
    except (JWTError, TypeError, ValidationError) as exc:
        raise ValueError("Invalid token payload") from exc
    return payload
