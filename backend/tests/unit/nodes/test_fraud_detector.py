"""Unit tests for [6] Fraud Detector."""

import pytest

from app.agents.nodes.fraud_detector import (
    _FraudDetectionResult,
    _FraudSignalResult,
    build_fraud_detector_node,
)
from app.core.exceptions import LLMProviderError
from app.state.graph_state import GraphState
from tests.fakes import FakeChatModel


def _state() -> GraphState:
    return {"claim_id": "c1", "coverage": [], "chunks": []}


async def test_no_signals_means_zero_fraud_score_and_no_attorney_flag():
    chat_model = FakeChatModel(_FraudDetectionResult(signals=[]))
    node = build_fraud_detector_node(chat_model)

    result = await node(_state())

    assert result["fraud_signals"] == []
    assert result["fraud_score"] == 0.0
    assert result["attorney_flag"] is False


async def test_high_severity_signal_sets_attorney_flag_and_fraud_score():
    chat_model = FakeChatModel(
        _FraudDetectionResult(
            signals=[
                _FraudSignalResult(
                    signal_type="upcoding", severity="high", evidence="CPT/diagnosis mismatch"
                )
            ]
        )
    )
    node = build_fraud_detector_node(chat_model)

    result = await node(_state())

    assert result["attorney_flag"] is True
    assert result["fraud_score"] == 0.9
    assert result["audit_log"][0]["details"]["attorney_flag"] is True


async def test_low_severity_alone_does_not_set_attorney_flag():
    chat_model = FakeChatModel(
        _FraudDetectionResult(
            signals=[
                _FraudSignalResult(
                    signal_type="date_conflict", severity="low", evidence="minor date mismatch"
                )
            ]
        )
    )
    node = build_fraud_detector_node(chat_model)

    result = await node(_state())

    assert result["attorney_flag"] is False
    assert result["fraud_score"] == 0.3


async def test_llm_failure_raises_llm_provider_error():
    chat_model = FakeChatModel(ConnectionError("network unreachable"))
    node = build_fraud_detector_node(chat_model)

    with pytest.raises(LLMProviderError):
        await node(_state())
