import datetime as dt
import hashlib
from collections import OrderedDict

from jose import JWTError, jwt


def issue_jwt(user_id: str, secret: str, ttl_minutes: int = 30) -> str:
    now = dt.datetime.now(dt.UTC)
    expiration = now + dt.timedelta(minutes=ttl_minutes)
    claim_hash = hashlib.sha256(f"{user_id}{now.isoformat()}".encode("utf-8")).hexdigest()

    payload = OrderedDict()
    payload["hash"] = claim_hash
    payload["userID"] = user_id
    payload["exp"] = int(expiration.timestamp())

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> dict[str, str | int]:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    user_id = payload.get("userID")
    expiration = payload.get("exp")
    claim_hash = payload.get("hash")

    if not isinstance(user_id, str) or not isinstance(expiration, int) or not isinstance(claim_hash, str):
        raise ValueError("Invalid token payload")

    return {
        "hash": claim_hash,
        "userID": user_id,
        "exp": expiration,
    }
