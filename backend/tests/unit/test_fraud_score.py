from app.agents.nodes.fraud_detector import compute_fraud_score
from app.state.graph_state import FraudSignal


def _signal(severity: str) -> FraudSignal:
    return FraudSignal(signal_type="duplicate_billing", severity=severity, evidence="e")  # type: ignore[typeddict-item]


def test_fraud_score_is_zero_with_no_signals():
    assert compute_fraud_score([]) == 0.0


def test_fraud_score_takes_the_highest_severity_present():
    signals = [_signal("low"), _signal("high"), _signal("medium")]
    assert compute_fraud_score(signals) == 0.9


def test_fraud_score_low_only():
    assert compute_fraud_score([_signal("low")]) == 0.3
