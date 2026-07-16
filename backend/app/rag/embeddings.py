from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.core.config import get_settings


@lru_cache
def get_embeddings() -> Embeddings:
    settings = get_settings()
    api_key = SecretStr(settings.openai_api_key) if settings.openai_api_key else None
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=api_key)
