"""Chat model factory — the one place `LLM_PROVIDER` is switched on.

Every agent node depends on a `BaseChatModel` injected through this factory
(never instantiates `ChatOpenAI`/`ChatAnthropic` directly), so swapping
providers is a config change, not a code change, and tests can inject a fake
model without touching node code.
"""

from langchain_core.language_models import BaseChatModel

from app.config.settings import Settings
from app.core.exceptions import LLMProviderError


def get_chat_model(settings: Settings) -> BaseChatModel:
    api_key = settings.resolved_llm_api_key()
    if not api_key:
        raise LLMProviderError(
            f"No API key configured for LLM_PROVIDER={settings.llm_provider!r}. "
            "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment."
        )

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=api_key,
            temperature=settings.llm_temperature,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=settings.anthropic_chat_model,
            api_key=api_key,
            temperature=settings.llm_temperature,
            timeout=60,
            stop=None,
        )

    raise LLMProviderError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}")
