import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
import bcrypt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def generate_enrollment_code() -> str:
    return secrets.token_urlsafe(16)


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


def generate_sms_secret() -> str:
    return secrets.token_urlsafe(24)


def sign_command(command_id: UUID, device_id: UUID, cmd_type: str, expires_at: datetime) -> str:
    settings = get_settings()
    canonical = f"{command_id}|{device_id}|{cmd_type}|{expires_at.isoformat()}"
    return hmac.new(
        settings.command_hmac_secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_command_signature(
    command_id: UUID,
    device_id: UUID,
    cmd_type: str,
    expires_at: datetime,
    signature: str,
) -> bool:
    expected = sign_command(command_id, device_id, cmd_type, expires_at)
    return hmac.compare_digest(expected, signature)


def verify_sms_hmac(secret: str, message: str, provided: str) -> bool:
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.lower(), provided.lower())


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
