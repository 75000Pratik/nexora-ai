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


def test_settings_rejects_non_positive_token_expiration():
    with pytest.raises(
        ValidationError,
        match="greater than zero",
    ):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            access_token_expire_minutes=0,
        )


def test_settings_rejects_unsupported_environment():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            environment="prodution",
        )


def test_settings_rejects_placeholder_jwt_secret_in_production():
    with pytest.raises(
        ValidationError,
        match="placeholder",
    ):
        Settings(
            _env_file=None,
            jwt_secret_key="your-secret-key-change-me-123456",
            database_url="sqlite://",
            environment="production",
        )


def test_settings_rejects_short_jwt_secret_in_production():
    with pytest.raises(
        ValidationError,
        match="43 characters",
    ):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            environment="production",
        )


@pytest.mark.parametrize(
    "invalid_score",
    [float("nan"), float("inf"), float("-inf")],
)
def test_settings_rejects_non_finite_reranking_min_score(invalid_score):
    with pytest.raises(
        ValidationError,
        match="finite number",
    ):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            reranking_min_score=invalid_score,
        )

@pytest.mark.parametrize(
    "field_name",
    ["ask_rate_limit", "search_rate_limit", "upload_rate_limit"],
)
def test_settings_rejects_invalid_rate_limit(field_name):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            jwt_secret_key="a" * 32,
            database_url="sqlite://",
            **{field_name: "invalid-rate-limit"},
        )