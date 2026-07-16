from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Auth
    api_keys: list[str] = []

    # LLM
    llm_provider: str = "openai"  # "openai" | "anthropic"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-5"
    embedding_model: str = "text-embedding-3-small"

    # Retry / graph
    max_synthesis_retries: int = 2

    # Storage
    database_url: str = f"sqlite+aiosqlite:///{BACKEND_ROOT}/data/app.db"
    interaction_index_dir: Path = BACKEND_ROOT / "app" / "data" / "indices" / "interactions"
    interaction_corpus_dir: Path = BACKEND_ROOT / "app" / "data" / "interaction_corpus"

    # App
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
