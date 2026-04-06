import datetime as dt
import hashlib
from collections import OrderedDict

from jose import JWTError, jwt
from pydantic import BaseModel


class JWTPayload(BaseModel):
    user_id: str
    expiration: int
    claim_hash: str


def issue_jwt(user_id: str, secret: str, ttl_minutes: int = 30) -> str:
    now = dt.datetime.now(dt.UTC)
    expiration = now + dt.timedelta(minutes=ttl_minutes)
    claim_hash = hashlib.sha256(f"{user_id}{now.isoformat()}".encode("utf-8")).hexdigest()

    payload = OrderedDict()
    payload["hash"] = claim_hash
    payload["userID"] = user_id
    payload["exp"] = int(expiration.timestamp())

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str):
    try:
        payload = JWTPayload(**jwt.decode(token, secret, algorithms=["HS256"]))
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload
