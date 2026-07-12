from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for all environment-driven configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- LLM provider ---
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_chat_model: str = "gpt-4o"
    anthropic_chat_model: str = "claude-sonnet-5"
    llm_temperature: float = 0.0

    # --- Embeddings (independent of chat LLM provider; see docs/architecture.md) ---
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Storage ---
    database_url: str = "sqlite:///./data/claims.db"
    vector_index_dir: str = "./data/indices"
    policy_corpus_dir: str = "./data/policy_corpus"
    synthetic_claims_dir: str = "./data/synthetic_claims"
    upload_storage_dir: str = "./data/uploads"

    # --- RAG ---
    rag_similarity_threshold: float = 0.65
    rag_top_k: int = 5

    # --- Self-Critic retry loop ---
    self_critic_score_threshold: float = 0.80
    self_critic_max_retries: int = 2

    # --- Security ---
    security_block_confidence: float = 0.70
    upload_max_bytes: int = 15_000_000
    allowed_upload_content_types: list[str] = ["application/pdf"]

    def resolved_llm_api_key(self) -> str | None:
        if self.llm_provider == "openai":
            return self.openai_api_key
        return self.anthropic_api_key

    def resolved_llm_model_name(self) -> str:
        if self.llm_provider == "openai":
            return self.openai_chat_model
        return self.anthropic_chat_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
