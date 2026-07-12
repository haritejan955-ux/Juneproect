"""Scenario 1 — Full Approval. See test_scenarios/01_full_approval/README.md.

Runs the real, generated claim PDF through the actual production graph
end-to-end with a scripted chat model, and asserts the finalized decision
is a clean approval with no retry needed.
"""

from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult, _LineItemResult
from app.agents.nodes.intent_analyzer import IntentClassification
from tests.fakes import MultiSchemaFakeChatModel
from tests.langgraph.helpers import SCENARIOS_DIR, run_scenario, schema_placeholders

PDF_PATH = SCENARIOS_DIR / "01_full_approval" / "01_routine_office_visit.pdf"


async def test_full_approval_scenario_produces_a_clean_approval():
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="coverage_check",
                    confidence=0.96,
                    procedure_codes=["99213"],
                    diagnosis_codes=["J06.9"],
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="99213",
                            diagnosis_code="J06.9",
                            status="approved",
                            cited_clause=(
                                "ACA essential health benefits cover ambulatory patient "
                                "services, including established-patient office visits."
                            ),
                            amount_billed=150.0,
                            amount_covered=150.0,
                        )
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="approved",
                    justification=(
                        "The single billed line-item (CPT 99213) is a routine office visit "
                        "fully covered under the plan's ambulatory care benefit."
                    ),
                ),
            }
        )
    )

    result = await run_scenario(
        "scenario-full-approval",
        PDF_PATH,
        "Is my recent office visit covered?",
        chat_model,
    )

    decision = result["final_decision"]
    assert decision["status"] == "approved"
    assert decision["attorney_flag"] is False
    assert decision["low_confidence"] is False
    assert decision["retry_count"] == 0
    assert len(decision["coverage_map"]) == 1
    assert decision["coverage_map"][0]["status"] == "approved"
    assert decision["fraud_signals"] == []
    assert decision["disclaimer"], "the non-removable disclaimer must always be present"

    agents_that_ran = {entry["agent"] for entry in result["audit_log"]}
    assert "final_output" in agents_that_ran
    assert "blocked" not in agents_that_ran
