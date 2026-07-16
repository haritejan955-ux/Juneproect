from app.agents.graph import build_safety_graph, initial_state
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification


def test_self_critic_rejection_triggers_one_retry_then_succeeds(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[
                Medication(raw_name="Digoxin", dose_value=0.125, dose_unit="mg", frequency="daily", route="oral"),
                Medication(raw_name="Furosemide", dose_value=40, dose_unit="mg", frequency="daily", route="oral"),
            ]
        )
    )
    # First synthesis attempt: incomplete.
    graph_fakes.queue(
        SafetyReportOutput(overall_severity="none", summary="No risks identified.", findings=[])
    )
    graph_fakes.queue(
        CritiqueResult(
            approved=False,
            critique="You missed the digoxin-furosemide hypokalemia interaction.",
            missed_considerations=["digoxin_furosemide"],
        )
    )
    # Second synthesis attempt, after the critique: complete.
    graph_fakes.queue(
        SafetyReportOutput(
            overall_severity="moderate",
            summary="Digoxin toxicity risk from furosemide-induced hypokalemia.",
            findings=[
                {
                    "category": "interaction",
                    "drugs": ["digoxin", "furosemide"],
                    "severity": "moderate",
                    "citation_doc_id": "digoxin_furosemide",
                    "citation_title": "Digoxin + Loop diuretic",
                }
            ],
        )
    )
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state(
        "Patient takes Digoxin 0.125mg daily and Furosemide 40mg daily.", {"age": 74, "renal_function": "normal"}
    )
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["retry_count"] == 1
    assert result["report"]["overall_severity"] == "moderate"

    agents_run = [entry["agent"] for entry in result["audit_log"]]
    assert agents_run.count("risk_synthesizer") == 2
    assert agents_run.count("self_critic") == 2
    assert "prepare_retry" in agents_run


def test_retry_guard_stops_after_max_retries(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(ParsedPrescription(medications=[Medication(raw_name="Acetaminophen")]))
    # Every synthesis attempt is rejected; the guard must still terminate.
    for _ in range(3):
        graph_fakes.queue(SafetyReportOutput(overall_severity="none", summary="incomplete", findings=[]))
        graph_fakes.queue(CritiqueResult(approved=False, critique="still incomplete", missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state("Patient takes Tylenol.", {"age": 30})
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["retry_count"] == 2  # max_synthesis_retries default
