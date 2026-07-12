"""Shared wrapper around every structured-output LLM call a node makes.

Six of the nine nodes follow the identical pattern: build a prompt, call
`.ainvoke()` on a `with_structured_output(...)`-wrapped model, and trust the
result is the expected Pydantic type. Centralizing that call here means
every one of those six nodes gets the same logging and error-handling
guarantees for free, instead of six hand-rolled (and inevitably slightly
different) try/except blocks. Nodes with a different failure posture —
Security Checker's fail-closed classifier, Document Preprocessor's
LLM-free parsing — don't use this and handle their own risk explicitly;
see their own docstrings.
"""

from typing import TypeVar

from langchain_core.runnables import Runnable

from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def invoke_structured(
    structured_model: Runnable,
    prompt: str,
    *,
    agent_name: str,
    claim_id: str,
    expected_type: type[T],
) -> T:
    """Call `structured_model.ainvoke(prompt)`, logging start/success/failure
    with `claim_id` attached, and raising `LLMProviderError` (never the raw
    provider/network exception) on any failure — including a response that
    doesn't come back as `expected_type`, which `with_structured_output`
    should prevent but is worth verifying rather than assuming."""

    logger.info(f"{agent_name}.llm_call.started", extra={"claim_id": claim_id})

    try:
        result = await structured_model.ainvoke(prompt)
    except Exception as exc:
        logger.error(
            f"{agent_name}.llm_call.failed",
            extra={"claim_id": claim_id, "error": str(exc)},
            exc_info=True,
        )
        raise LLMProviderError(
            f"{agent_name}: LLM call failed: {exc}",
            claim_id=claim_id,
            agent=agent_name,
        ) from exc

    if not isinstance(result, expected_type):
        logger.error(
            f"{agent_name}.llm_call.unexpected_response_type",
            extra={"claim_id": claim_id, "actual_type": type(result).__name__},
        )
        raise LLMProviderError(
            f"{agent_name}: expected {expected_type.__name__}, "
            f"got {type(result).__name__} from structured output",
            claim_id=claim_id,
            agent=agent_name,
        )

    logger.info(f"{agent_name}.llm_call.completed", extra={"claim_id": claim_id})
    return result
