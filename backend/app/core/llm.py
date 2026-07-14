from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from app.core.config import get_settings


def get_chat_model() -> BaseChatModel:
    """Return the configured chat model. Tests monkeypatch this to a scripted fake."""
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if settings.anthropic_api_key:
            return ChatAnthropic(
                model_name=settings.anthropic_model,
                api_key=SecretStr(settings.anthropic_api_key),
                timeout=None,
                stop=None,
            )
        return ChatAnthropic(model_name=settings.anthropic_model, timeout=None, stop=None)

    from langchain_openai import ChatOpenAI

    if settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_model, api_key=SecretStr(settings.openai_api_key), temperature=0
        )
    return ChatOpenAI(model=settings.openai_model, temperature=0)
