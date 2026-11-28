from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nexora AI"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing","staging", "production"] = "development"
    reranking_min_score: float = 0.0
    ask_rate_limit: str = "10/minute"
    search_rate_limit: str = "20/minute"
    upload_rate_limit: str = "5/minute"
    jwt_secret_key: str
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "nexora_documents"

    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:1.5b"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str, info) -> str:
        if len(value) < 32:
            raise ValueError(
                "JWT secret key must be at least 32 characters long."
            )
        if info.data.get("environment") == "production":
            placeholders = {
                "your-secret-key-change-me-123456",
                "change-me",
                "secret",
                "your-secret-key",
            }

            if value.lower() in placeholders:
                raise ValueError(
                    "Production JWT secret cannot be a placeholder."
                )

        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_access_token_expire_minutes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "Access token expiration must be greater than zero."
            )

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
