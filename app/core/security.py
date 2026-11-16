from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a password against its stored hash."""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str | None:
    """Verify a JWT and return its subject, or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.strip():
            return None

        return subject

    except jwt.InvalidTokenError:
        return None
