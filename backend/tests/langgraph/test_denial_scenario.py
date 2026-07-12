"""Scenario 3 — Denial. See test_scenarios/03_denial/README.md."""

from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult, _LineItemResult
from app.agents.nodes.intent_analyzer import IntentClassification
from tests.fakes import MultiSchemaFakeChatModel
from tests.langgraph.helpers import SCENARIOS_DIR, run_scenario, schema_placeholders

PDF_PATH = SCENARIOS_DIR / "03_denial" / "01_lapsed_coverage.pdf"


async def test_denial_scenario_denies_for_lapsed_coverage_without_attorney_flag():
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="denial_appeal",
                    confidence=0.9,
                    procedure_codes=["99214"],
                    diagnosis_codes=["M25.561"],
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="99214",
                            diagnosis_code="M25.561",
                            status="denied",
                            cited_clause=(
                                "Policy coverage terminated 12/31/2025 per policy section 2.1; "
                                "the date of service falls outside the active coverage period."
                            ),
                            amount_billed=220.0,
                            amount_covered=0.0,
                        )
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="denied",
                    justification=(
                        "This claim is denied because the date of service falls after the "
                        "policy's termination date; no active coverage was in force."
                    ),
                ),
            }
        )
    )

    result = await run_scenario(
        "scenario-denial",
        PDF_PATH,
        "Why was this claim denied?",
        chat_model,
    )

    decision = result["final_decision"]
    assert decision["status"] == "denied"
    assert len(decision["coverage_map"]) == 1
    assert decision["coverage_map"][0]["status"] == "denied"
    assert decision["coverage_map"][0]["cited_clause"]
    assert decision["fraud_signals"] == []
    # A plain lapsed-coverage denial is not, by itself, grounds for attorney review — that flag
    # is reserved for high-severity fraud or high-risk legal interpretation (see the fraud
    # scenario, which contrasts directly with this one).
    assert decision["attorney_flag"] is False
