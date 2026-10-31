from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nexora AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    reranking_min_score: float = 0.0

    database_url: str

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "nexora_documents"

    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:1.5b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
