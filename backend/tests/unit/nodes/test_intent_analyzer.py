"""Unit tests for [2] Intent Analyzer."""

import pytest

from app.agents.nodes.intent_analyzer import IntentClassification, build_intent_analyzer_node
from app.core.exceptions import LLMProviderError
from app.state.graph_state import GraphState
from tests.fakes import FakeChatModel


def _state() -> GraphState:
    return {
        "claim_id": "c1",
        "query": "Is my MRI covered?",
        "document_metadata": {"document_count": 1, "doc_types": ["cms_1500"]},
    }


async def test_classifies_intent_and_extracts_entities():
    chat_model = FakeChatModel(
        IntentClassification(
            intent="coverage_check",
            confidence=0.92,
            claimant_id="CL-1",
            date_of_service="2026-01-01",
            procedure_codes=["70551"],
            diagnosis_codes=["G89.29"],
        )
    )
    node = build_intent_analyzer_node(chat_model)

    result = await node(_state())

    assert result["intent"] == "coverage_check"
    assert result["intent_confidence"] == 0.92
    assert result["extracted_entities"]["procedure_codes"] == ["70551"]
    assert result["audit_log"][0]["action"] == "classified_intent"


async def test_omits_empty_entities_rather_than_fabricating_them():
    chat_model = FakeChatModel(
        IntentClassification(intent="obligation_lookup", confidence=0.4)
    )
    node = build_intent_analyzer_node(chat_model)

    result = await node(_state())

    assert result["extracted_entities"] == {}


async def test_prompt_includes_query_and_document_metadata():
    chat_model = FakeChatModel(IntentClassification(intent="fraud_check", confidence=0.7))
    node = build_intent_analyzer_node(chat_model)

    await node(_state())

    prompt = chat_model.last_runnable.prompts_received[0]
    assert "Is my MRI covered?" in prompt
    assert "cms_1500" in prompt


async def test_llm_failure_raises_llm_provider_error_not_raw_exception():
    chat_model = FakeChatModel(RuntimeError("provider is down"))
    node = build_intent_analyzer_node(chat_model)

    with pytest.raises(LLMProviderError) as excinfo:
        await node(_state())

    assert excinfo.value.context["claim_id"] == "c1"
    assert excinfo.value.context["agent"] == "intent_analyzer"
