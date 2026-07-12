"""Scenario 2 — Partial Approval. See test_scenarios/02_partial_approval/README.md."""

from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult, _LineItemResult
from app.agents.nodes.intent_analyzer import IntentClassification
from tests.fakes import MultiSchemaFakeChatModel
from tests.langgraph.helpers import SCENARIOS_DIR, run_scenario, schema_placeholders

PDF_PATH = SCENARIOS_DIR / "02_partial_approval" / "01_therapy_plus_cosmetic_procedure.pdf"


async def test_partial_approval_scenario_approves_one_line_item_and_denies_the_other():
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="coverage_check",
                    confidence=0.92,
                    procedure_codes=["97110", "15780"],
                    diagnosis_codes=["M54.5", "L70.0"],
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="97110",
                            diagnosis_code="M54.5",
                            status="approved",
                            cited_clause=(
                                "Physical therapy for a physician-documented medical necessity "
                                "is covered under the plan's rehabilitative services benefit."
                            ),
                            amount_billed=90.0,
                            amount_covered=90.0,
                        ),
                        _LineItemResult(
                            cpt_code="15780",
                            diagnosis_code="L70.0",
                            status="denied",
                            cited_clause=(
                                "Cosmetic procedures performed for appearance rather than "
                                "medical necessity are excluded under policy section 4.2."
                            ),
                            amount_billed=800.0,
                            amount_covered=0.0,
                        ),
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="partial_approved",
                    justification=(
                        "The physical therapy line-item is approved as medically necessary. "
                        "The cosmetic dermabrasion line-item is denied as an excluded benefit."
                    ),
                ),
            }
        )
    )

    result = await run_scenario(
        "scenario-partial-approval",
        PDF_PATH,
        "Why wasn't my whole visit covered?",
        chat_model,
    )

    decision = result["final_decision"]
    assert decision["status"] == "partial_approved"
    assert decision["attorney_flag"] is False
    assert len(decision["coverage_map"]) == 2

    statuses = {item["cpt_code"]: item["status"] for item in decision["coverage_map"]}
    assert statuses == {"97110": "approved", "15780": "denied"}

    denied_item = next(item for item in decision["coverage_map"] if item["status"] == "denied")
    assert denied_item["cited_clause"], "every denied line-item must still cite a clause"
