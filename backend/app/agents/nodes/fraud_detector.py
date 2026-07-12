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

# Maps a signal's severity to a numeric contribution for the aggregate `fraud_score`. This is a
# deliberately simple, explainable mapping (not a learned model) — `fraud_score` is a single
# sortable/thresholdable value for the API and frontend; the itemized `fraud_signals` list is
# still the source of truth for *why* the score is what it is.
_SEVERITY_SCORE = {"low": 0.3, "medium": 0.6, "high": 0.9}


class _FraudSignalResult(BaseModel):
    signal_type: str
    severity: str = Field(description="'low', 'medium', or 'high'")
    evidence: str = Field(min_length=1)


class _FraudDetectionResult(BaseModel):
    signals: list[_FraudSignalResult]


def compute_fraud_score(fraud_signals: list[FraudSignal]) -> float:
    """Pure function so the aggregation rule is unit-testable without an LLM call."""
    return max((_SEVERITY_SCORE[s["severity"]] for s in fraud_signals), default=0.0)


def build_fraud_detector_node(chat_model: BaseChatModel) -> Callable[[GraphState], Awaitable[dict]]:
    detector = chat_model.with_structured_output(_FraudDetectionResult)

    async def fraud_detector(state: GraphState) -> dict:
        result = await detector.ainvoke(
            build_fraud_detector_prompt(
                list(state.get("coverage", [])), list(state.get("chunks", []))
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
        fraud_score = compute_fraud_score(fraud_signals)
        attorney_flag = any(signal["severity"] == "high" for signal in fraud_signals)

        return {
            "fraud_signals": fraud_signals,
            "fraud_score": fraud_score,
            "attorney_flag": attorney_flag,
            **audit_update(
                AGENT_NAME,
                "scored_fraud_signals",
                {
                    "signal_count": len(fraud_signals),
                    "fraud_score": fraud_score,
                    "attorney_flag": attorney_flag,
                },
            ),
        }

    return fraud_detector
