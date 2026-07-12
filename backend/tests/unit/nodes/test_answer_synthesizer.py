"""Unit tests for [7] Answer Synthesizer."""

import pytest

from app.agents.nodes.answer_synthesizer import (
    DISCLAIMER,
    _SynthesisResult,
    build_answer_synthesizer_node,
)
from app.core.exceptions import LLMProviderError
from app.state.graph_state import GraphState
from tests.fakes import FakeChatModel


def _state(**overrides) -> GraphState:
    base: GraphState = {
        "claim_id": "c1",
        "coverage": [],
        "fraud_signals": [],
        "retrieved_chunks": [],
        "retry_count": 0,
    }
    # TypedDict.update() requires its argument to be statically provable as shape-compatible;
    # `overrides` is deliberately a free-form **kwargs bag of whichever GraphState fields a
    # given test wants to set, which mypy can't verify field-by-field here.
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


async def test_appends_disclaimer_via_code_not_the_model():
    chat_model = FakeChatModel(
        _SynthesisResult(decision="approved", justification="All line-items were covered.")
    )
    node = build_answer_synthesizer_node(chat_model)

    result = await node(_state())

    assert result["decision"] == "approved"
    assert result["disclaimer"] == DISCLAIMER
    # The model's structured schema has no `disclaimer` field at all — there is no way for the
    # LLM to have supplied or omitted it; it can only ever be the constant appended below.


async def test_retry_injects_self_critique_into_the_prompt():
    chat_model = FakeChatModel(
        _SynthesisResult(decision="denied", justification="Revised justification.")
    )
    node = build_answer_synthesizer_node(chat_model)

    state = _state(self_critique="Line-item 2 was never addressed.", retry_count=1)
    await node(state)

    prompt = chat_model.last_runnable.prompts_received[0]
    assert "Line-item 2 was never addressed." in prompt


async def test_audit_entry_records_retry_count():
    chat_model = FakeChatModel(_SynthesisResult(decision="approved", justification="ok"))
    node = build_answer_synthesizer_node(chat_model)

    result = await node(_state(retry_count=2))

    assert result["audit_log"][0]["details"]["retry_count"] == 2


async def test_llm_failure_raises_llm_provider_error():
    chat_model = FakeChatModel(RuntimeError("provider down"))
    node = build_answer_synthesizer_node(chat_model)

    with pytest.raises(LLMProviderError):
        await node(_state())
