from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_hashed_value():
    password = "StrongPassword123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2")


def test_verify_password_accepts_correct_password():
    password = "StrongPassword123!"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_password_rejects_wrong_password():
    hashed_password = hash_password(
        "StrongPassword123!"
    )

    assert verify_password(
        "WrongPassword123!",
        hashed_password,
    ) is False


def test_create_access_token_returns_valid_jwt():
    subject = "user-123"

    token = create_access_token(subject)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == subject
    assert "exp" in payload


def test_decode_access_token_returns_subject():
    subject = "user-123"

    token = create_access_token(subject)

    result = decode_access_token(token)

    assert result == subject


def test_decode_access_token_rejects_invalid_token():
    result = decode_access_token(
        "invalid.jwt.token"
    )

    assert result is None


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token("user-123")

    tampered_token = token[:-5] + "abcde"

    result = decode_access_token(tampered_token)

    assert result is None


def test_decode_access_token_rejects_expired_token():
    expired_token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc)
            - timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    result = decode_access_token(expired_token)

    assert result is None


def test_decode_access_token_rejects_empty_subject():
    token = create_access_token("")

    result = decode_access_token(token)

    assert result is None
