"""LangGraph control-flow test: the Self-Critic retry loop, exercised
through the real conditional edge (`route_after_critic`) and the real
`prepare_retry` node — not just the pure routing predicate in isolation
(see `tests/unit/test_routing.py` for that unit-level coverage).

Scripts a `_CritiqueResult` that scores low on the first pass (below the
0.8 threshold) and high on the second, using `MultiSchemaFakeChatModel`'s
per-call sequencing (`tests/fakes.py`) — the same schema, two different
responses, consumed in call order. If either the retry-count guard or the
re-entry edge back into Answer Synthesizer were wired wrong, this would
either loop forever (caught by LangGraph's own recursion limit) or exit
after the first, low-scoring pass instead of eventually succeeding.
"""

from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult, _LineItemResult
from app.agents.nodes.intent_analyzer import IntentClassification
from app.agents.nodes.self_critic import _CritiqueResult
from tests.fakes import MultiSchemaFakeChatModel
from tests.langgraph.helpers import SCENARIOS_DIR, run_scenario, schema_placeholders

PDF_PATH = SCENARIOS_DIR / "01_full_approval" / "01_routine_office_visit.pdf"

_LOW_SCORE_CRITIQUE = _CritiqueResult(
    legal_accuracy=0.5,
    completeness=0.5,
    hallucination_risk=0.5,
    critique="Justification does not cite a specific policy clause; add one before finalizing.",
)
_HIGH_SCORE_CRITIQUE = _CritiqueResult(
    legal_accuracy=0.95,
    completeness=0.95,
    hallucination_risk=0.95,
    critique="",
)


async def test_self_critic_retry_loop_recovers_on_second_pass():
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="coverage_check", confidence=0.9, procedure_codes=["99213"]
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="99213",
                            diagnosis_code="J06.9",
                            status="approved",
                            cited_clause=(
                                "Ambulatory office visits are a covered essential "
                                "health benefit."
                            ),
                            amount_billed=150.0,
                            amount_covered=150.0,
                        )
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="approved", justification="The office visit is covered."
                ),
                # Sequenced: first self_critic call gets the low score (triggers a retry),
                # second call gets the high score (passes) — see MultiSchemaFakeChatModel's
                # docstring for how a list value is consumed one-per-call.
                _CritiqueResult: [_LOW_SCORE_CRITIQUE, _HIGH_SCORE_CRITIQUE],
            }
        )
    )

    result = await run_scenario(
        "scenario-retry-loop", PDF_PATH, "Is my office visit covered?", chat_model
    )

    decision = result["final_decision"]
    assert decision["status"] == "approved"
    assert decision["retry_count"] == 1, "exactly one retry should have run before passing"
    assert decision["low_confidence"] is False, "the second pass passed — this isn't exhaustion"

    self_critic_entries = [
        entry for entry in result["audit_log"] if entry["agent"] == "self_critic"
    ]
    assert len(self_critic_entries) == 2
    assert self_critic_entries[0]["details"]["passed"] is False
    assert self_critic_entries[1]["details"]["passed"] is True

    synthesizer_entries = [
        entry for entry in result["audit_log"] if entry["agent"] == "answer_synthesizer"
    ]
    assert len(synthesizer_entries) == 2, "answer_synthesizer must run again on the retry branch"
    assert synthesizer_entries[0]["details"]["retry_count"] == 0
    assert synthesizer_entries[1]["details"]["retry_count"] == 1


async def test_self_critic_retry_loop_stops_at_max_retries_and_flags_low_confidence():
    """Both critique calls score low — after `max_retries=2` (see `helpers.build_test_graph`)
    is exhausted, routing must send the claim to `final_output` anyway rather than looping
    forever, and `low_confidence` must be set so the API/frontend surface that the decision
    is less trustworthy than usual."""
    chat_model = MultiSchemaFakeChatModel(
        schema_placeholders(
            {
                IntentClassification: IntentClassification(
                    intent="coverage_check", confidence=0.9, procedure_codes=["99213"]
                ),
                _CoverageValidationResult: _CoverageValidationResult(
                    line_items=[
                        _LineItemResult(
                            cpt_code="99213",
                            diagnosis_code="J06.9",
                            status="approved",
                            cited_clause=(
                                "Ambulatory office visits are a covered essential "
                                "health benefit."
                            ),
                            amount_billed=150.0,
                            amount_covered=150.0,
                        )
                    ]
                ),
                _SynthesisResult: _SynthesisResult(
                    decision="approved", justification="The office visit is covered."
                ),
                _CritiqueResult: _LOW_SCORE_CRITIQUE,  # every call scores low — never recovers
            }
        )
    )

    result = await run_scenario(
        "scenario-retry-exhausted", PDF_PATH, "Is my office visit covered?", chat_model
    )

    decision = result["final_decision"]
    assert decision["retry_count"] == 2, "must stop at max_retries, never exceed it"
    assert decision["low_confidence"] is True

    self_critic_entries = [
        entry for entry in result["audit_log"] if entry["agent"] == "self_critic"
    ]
    assert len(self_critic_entries) == 3, "initial pass + 2 retries = 3 self_critic runs"
    assert all(entry["details"]["passed"] is False for entry in self_critic_entries)
