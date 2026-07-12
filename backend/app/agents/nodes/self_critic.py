"""[8] Self-Critic — adversarial scoring of the draft decision.

`low_confidence` is set here, not in routing: this node already has both
the computed score and `retry_count` in scope, so it is the natural owner
of "retries are exhausted and the score is still low" as a fact about the
decision, even though the *next node to run* is decided separately by the
pure routing predicate in agents/routing.py. See
docs/langgraph-workflow.md section 3.
"""

from collections.abc import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.core.audit import audit_update
from app.core.llm_call import invoke_structured
from app.core.logging import get_logger
from app.prompts.self_critic_prompt import build_self_critic_prompt
from app.state.graph_state import GraphState

AGENT_NAME = "self_critic"

logger = get_logger(__name__)

_WEIGHTS = {"legal_accuracy": 0.4, "completeness": 0.3, "hallucination_risk": 0.3}


class _CritiqueResult(BaseModel):
    legal_accuracy: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    hallucination_risk: float = Field(ge=0.0, le=1.0)
    critique: str = Field(
        description="Specific, actionable critique; empty string if score is high"
    )


def build_self_critic_node(
    chat_model: BaseChatModel, score_threshold: float, max_retries: int
) -> Callable[[GraphState], Awaitable[dict]]:
    critic = chat_model.with_structured_output(_CritiqueResult)

    async def self_critic(state: GraphState) -> dict:
        claim_id = state["claim_id"]
        logger.info(f"{AGENT_NAME}.started", extra={"claim_id": claim_id})

        redacted_chunks = state.get("redacted_chunks") or state.get("retrieved_chunks", [])

        result = await invoke_structured(
            critic,
            build_self_critic_prompt(
                state.get("decision", ""),
                state.get("justification", ""),
                list(redacted_chunks),
            ),
            agent_name=AGENT_NAME,
            claim_id=claim_id,
            expected_type=_CritiqueResult,
        )

        overall_score = (
            result.legal_accuracy * _WEIGHTS["legal_accuracy"]
            + result.completeness * _WEIGHTS["completeness"]
            + result.hallucination_risk * _WEIGHTS["hallucination_risk"]
        )

        retry_count = state.get("retry_count", 0)
        passed = overall_score >= score_threshold
        low_confidence = (not passed) and retry_count >= max_retries

        logger.info(
            f"{AGENT_NAME}.completed",
            extra={
                "claim_id": claim_id,
                "overall_score": overall_score,
                "passed": passed,
                "low_confidence": low_confidence,
            },
        )

        return {
            "confidence": overall_score,
            "self_critique": result.critique,
            "low_confidence": low_confidence,
            **audit_update(
                AGENT_NAME,
                "scored_decision",
                {
                    "overall_score": overall_score,
                    "legal_accuracy": result.legal_accuracy,
                    "completeness": result.completeness,
                    "hallucination_risk": result.hallucination_risk,
                    "passed": passed,
                    "retry_count": retry_count,
                },
            ),
        }

    return self_critic
