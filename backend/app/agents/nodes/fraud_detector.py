"""[6] Fraud Detector — scores all 4 required signal types with severity +
evidence; a high-severity signal sets `attorney_flag`. See
docs/agent-architecture.md."""

from collections.abc import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.core.audit import audit_update
from app.prompts.fraud_detector_prompt import build_fraud_detector_prompt
from app.state.graph_state import FraudSignal, GraphState

AGENT_NAME = "fraud_detector"


class _FraudSignalResult(BaseModel):
    signal_type: str
    severity: str = Field(description="'low', 'medium', or 'high'")
    evidence: str = Field(min_length=1)


class _FraudDetectionResult(BaseModel):
    signals: list[_FraudSignalResult]


def build_fraud_detector_node(chat_model: BaseChatModel) -> Callable[[GraphState], Awaitable[dict]]:
    detector = chat_model.with_structured_output(_FraudDetectionResult)

    async def fraud_detector(state: GraphState) -> dict:
        result = await detector.ainvoke(
            build_fraud_detector_prompt(
                list(state.get("coverage_map", [])), list(state.get("document_chunks", []))
            )
        )
        assert isinstance(result, _FraudDetectionResult)

        fraud_signals: list[FraudSignal] = [
            FraudSignal(
                signal_type=signal.signal_type,  # type: ignore[typeddict-item]
                severity=signal.severity,  # type: ignore[typeddict-item]
                evidence=signal.evidence,
            )
            for signal in result.signals
        ]
        attorney_flag = any(signal["severity"] == "high" for signal in fraud_signals)

        return {
            "fraud_signals": fraud_signals,
            "attorney_flag": attorney_flag,
            **audit_update(
                AGENT_NAME,
                "scored_fraud_signals",
                {"signal_count": len(fraud_signals), "attorney_flag": attorney_flag},
            ),
        }

    return fraud_detector
