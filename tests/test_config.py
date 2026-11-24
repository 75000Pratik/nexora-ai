import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_accepts_strong_jwt_secret():
    settings = Settings(
        _env_file=None,
        jwt_secret_key="a" * 32,
        database_url="sqlite://",
    )

    assert len(settings.jwt_secret_key) == 32


def test_settings_rejects_weak_jwt_secret():
    with pytest.raises(
        ValidationError,
        match="at least 32 characters",
    ):
        Settings(
            _env_file=None,
            jwt_secret_key="short-secret",
            database_url="sqlite://",
        )


def test_settings_accepts_hs256_algorithm():
    settings = Settings(
        _env_file=None,
        jwt_secret_key="a" * 32,
        database_url="sqlite://",
        jwt_algorithm="HS256",
    )

    assert settings.jwt_algorithm == "HS256"


def test_settings_rejects_unsupported_jwt_algorithm():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            jwt_algorithm="HS384",
        )
