"""Scenario 4 — Fraud Detected. See test_scenarios/04_fraud_detected/README.md.

`fraud_score` and `attorney_flag` are deliberately *not* part of the
scripted Fraud Detector response below — they're computed by
`fraud_detector.compute_fraud_score()` and its high-severity check, both
real and unmocked, from the four scripted signals. This test is proof
those two aggregation paths are wired correctly, not just that the
fixture "contains" the right words.
"""

from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult, _LineItemResult
from app.agents.nodes.fraud_detector import _FraudDetectionResult, _FraudSignalResult
from app.agents.nodes.intent_analyzer import IntentClassification
from tests.fakes import MultiSchemaFakeChatModel
from tests.langgraph.helpers import SCENARIOS_DIR, run_scenario, schema_placeholders

PDF_PATH = SCENARIOS_DIR / "04_fraud_detected" / "01_multiple_fraud_signals.pdf"

_ALL_FOUR_SIGNAL_TYPES = {"duplicate_billing", "upcoding", "date_conflict", "unbundling"}


async def test_fraud_detected_scenario_flags_all_four_signal_types_and_attorney_review():
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="fraud_check",
                    confidence=0.88,
                    procedure_codes=["99215", "99215", "36415", "80053"],
                    diagnosis_codes=["M54.5"],
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="99215",
                            diagnosis_code="M54.5",
                            status="denied",
                            cited_clause=(
                                "Billed complexity level is inconsistent with clinical "
                                "documentation on file."
                            ),
                            amount_billed=280.0,
                            amount_covered=0.0,
                        )
                    ]
                ),
                _FraudDetectionResult: _FraudDetectionResult(
                    signals=[
                        _FraudSignalResult(
                            signal_type="duplicate_billing",
                            severity="high",
                            evidence=(
                                "CPT 99215 billed twice for the identical date of service, "
                                "05/01/2026."
                            ),
                        ),
                        _FraudSignalResult(
                            signal_type="upcoding",
                            severity="medium",
                            evidence=(
                                "Clinical notes support a low-complexity visit (99213), not "
                                "the high-complexity code (99215) billed."
                            ),
                        ),
                        _FraudSignalResult(
                            signal_type="date_conflict",
                            severity="medium",
                            evidence=(
                                "Date of service (05/01/2026) precedes the policy's stated "
                                "effective date (06/01/2026)."
                            ),
                        ),
                        _FraudSignalResult(
                            signal_type="unbundling",
                            severity="low",
                            evidence=(
                                "CPT 36415 and 80053 were billed separately despite being "
                                "bundled under NCCI edits."
                            ),
                        ),
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="denied",
                    justification=(
                        "This claim exhibits multiple fraud indicators — duplicate billing, "
                        "upcoding, a date-of-service conflict, and unbundled component "
                        "billing — and is denied pending manual review."
                    ),
                ),
            }
        )
    )

    result = await run_scenario(
        "scenario-fraud-detected",
        PDF_PATH,
        "Please review this claim for accuracy.",
        chat_model,
    )

    decision = result["final_decision"]
    assert decision["status"] == "denied"
    assert decision["attorney_flag"] is True, "a high-severity fraud signal must set attorney_flag"

    signal_types = {signal["signal_type"] for signal in decision["fraud_signals"]}
    assert signal_types == _ALL_FOUR_SIGNAL_TYPES
    assert len(decision["fraud_signals"]) == 4

    severities = {
        signal["signal_type"]: signal["severity"] for signal in decision["fraud_signals"]
    }
    assert severities["duplicate_billing"] == "high"

    audit_entry = next(
        entry
        for entry in result["audit_log"]
        if entry["agent"] == "fraud_detector" and entry["action"] == "scored_fraud_signals"
    )
    assert audit_entry["details"]["fraud_score"] == 0.9, "high severity maps to a 0.9 fraud_score"
    assert audit_entry["details"]["attorney_flag"] is True
