"""Embedding model factory — fixed to OpenAI regardless of `LLM_PROVIDER`.

Anthropic does not offer an embeddings endpoint, so embedding choice is
decoupled from chat-model choice (see docs/design-decisions.md, decision #2).
"""

from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

from app.config.settings import Settings
from app.core.exceptions import LLMProviderError


def get_embeddings(settings: Settings) -> Embeddings:
    if not settings.openai_api_key:
        raise LLMProviderError(
            "OPENAI_API_KEY is required for embeddings even when LLM_PROVIDER=anthropic, "
            "because Anthropic has no embeddings endpoint."
        )
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=SecretStr(settings.openai_api_key),
    )
