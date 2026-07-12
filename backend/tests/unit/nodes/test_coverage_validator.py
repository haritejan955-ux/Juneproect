"""Unit tests for [5] Coverage Validator."""

import pytest

from app.agents.nodes.coverage_validator import (
    _CoverageValidationResult,
    _LineItemResult,
    build_coverage_validator_node,
)
from app.core.exceptions import LLMProviderError
from app.state.graph_state import GraphState
from tests.fakes import FakeChatModel


def _state() -> GraphState:
    return {
        "claim_id": "c1",
        "extracted_entities": {"procedure_codes": ["97110"], "diagnosis_codes": ["M54.5"]},
        "retrieved_chunks": [],
    }


async def test_maps_line_items_with_citations():
    chat_model = FakeChatModel(
        _CoverageValidationResult(
            line_items=[
                _LineItemResult(
                    cpt_code="97110",
                    diagnosis_code="M54.5",
                    status="approved",
                    cited_clause="Policy Section 4.2 — Physical Therapy",
                    amount_billed=150.0,
                    amount_covered=150.0,
                )
            ]
        )
    )
    node = build_coverage_validator_node(chat_model)

    result = await node(_state())

    assert len(result["coverage"]) == 1
    assert result["coverage"][0]["cited_clause"] == "Policy Section 4.2 — Physical Therapy"
    assert result["citations"][0]["excerpt"] == "Policy Section 4.2 — Physical Therapy"
    assert result["audit_log"][0]["details"]["line_item_count"] == 1


async def test_normalizes_non_approved_status_to_denied():
    chat_model = FakeChatModel(
        _CoverageValidationResult(
            line_items=[
                _LineItemResult(
                    cpt_code="99999",
                    diagnosis_code="Z00.0",
                    status="not_covered",  # anything other than exactly "approved"
                    cited_clause="Exclusion clause 9.1",
                )
            ]
        )
    )
    node = build_coverage_validator_node(chat_model)

    result = await node(_state())

    assert result["coverage"][0]["status"] == "denied"


async def test_no_procedure_codes_still_evaluates_claim_level():
    chat_model = FakeChatModel(_CoverageValidationResult(line_items=[]))
    node = build_coverage_validator_node(chat_model)

    state: GraphState = {"claim_id": "c1", "extracted_entities": {}, "retrieved_chunks": []}
    await node(state)

    prompt = chat_model.last_runnable.prompts_received[0]
    assert "no procedure codes extracted" in prompt


async def test_llm_failure_raises_llm_provider_error():
    chat_model = FakeChatModel(TimeoutError("upstream timeout"))
    node = build_coverage_validator_node(chat_model)

    with pytest.raises(LLMProviderError):
        await node(_state())
