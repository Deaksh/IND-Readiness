"""Admin authentication: X-Admin-Key or JWT Bearer."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Header, HTTPException

from config import admin_jwt_signing_secret, get_settings


def _digest(s: str) -> bytes:
    return hashlib.sha256(s.encode("utf-8")).digest()


def verify_password(given: str, expected: str) -> bool:
    return hmac.compare_digest(_digest(given), _digest(expected))


def verify_api_key(given: str, expected: str | None) -> bool:
    if not expected or not given:
        return False
    return hmac.compare_digest(_digest(given), _digest(expected))


def create_admin_token(email: str) -> str:
    secret = admin_jwt_signing_secret()
    payload: dict[str, Any] = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_admin_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, admin_jwt_signing_secret(), algorithms=["HS256"])


def require_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    settings = get_settings()
    if x_admin_key and verify_api_key(x_admin_key, settings["admin_api_key"]):
        return {"auth": "api_key", "sub": "admin"}
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        try:
            payload = decode_admin_token(token)
            sub = str(payload.get("sub", "admin"))
            return {"auth": "jwt", "sub": sub}
        except jwt.PyJWTError:
            pass
    raise HTTPException(status_code=401, detail="Unauthorized")
