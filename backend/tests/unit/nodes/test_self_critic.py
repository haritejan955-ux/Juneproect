"""Unit tests for [8] Self-Critic."""

import pytest

from app.agents.nodes.self_critic import _CritiqueResult, build_self_critic_node
from app.core.exceptions import LLMProviderError
from app.state.graph_state import GraphState
from tests.fakes import FakeChatModel


def _state(retry_count: int = 0) -> GraphState:
    return {
        "claim_id": "c1",
        "decision": "approved",
        "justification": "All items covered under section 4.2.",
        "retrieved_chunks": [],
        "retry_count": retry_count,
    }


async def test_computes_weighted_overall_score():
    chat_model = FakeChatModel(
        _CritiqueResult(
            legal_accuracy=1.0, completeness=1.0, hallucination_risk=1.0, critique=""
        )
    )
    node = build_self_critic_node(chat_model, score_threshold=0.8, max_retries=2)

    result = await node(_state())

    assert result["confidence"] == 1.0
    assert result["low_confidence"] is False


async def test_low_score_within_retry_budget_is_not_low_confidence_yet():
    chat_model = FakeChatModel(
        _CritiqueResult(
            legal_accuracy=0.2,
            completeness=0.2,
            hallucination_risk=0.2,
            critique="Justification cites no policy clause.",
        )
    )
    node = build_self_critic_node(chat_model, score_threshold=0.8, max_retries=2)

    result = await node(_state(retry_count=0))

    assert result["confidence"] == pytest.approx(0.2)
    assert result["self_critique"] == "Justification cites no policy clause."
    # Retries remain (0 < 2), so this isn't the terminal low-confidence case yet — that's
    # decided by route_after_critic + this node together, see agents/routing.py.
    assert result["low_confidence"] is False


async def test_low_score_with_retries_exhausted_sets_low_confidence():
    chat_model = FakeChatModel(
        _CritiqueResult(
            legal_accuracy=0.1, completeness=0.1, hallucination_risk=0.1, critique="still bad"
        )
    )
    node = build_self_critic_node(chat_model, score_threshold=0.8, max_retries=2)

    result = await node(_state(retry_count=2))

    assert result["low_confidence"] is True


async def test_llm_failure_raises_llm_provider_error():
    chat_model = FakeChatModel(RuntimeError("boom"))
    node = build_self_critic_node(chat_model, score_threshold=0.8, max_retries=2)

    with pytest.raises(LLMProviderError):
        await node(_state())
