from app.agents.graph import build_safety_graph, initial_state
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification


def test_warfarin_aspirin_major_interaction_detected_with_citation(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[
                Medication(raw_name="Warfarin", dose_value=5, dose_unit="mg", frequency="daily", route="oral"),
                Medication(raw_name="Aspirin", dose_value=81, dose_unit="mg", frequency="daily", route="oral"),
            ]
        )
    )
    graph_fakes.queue(
        SafetyReportOutput(
            overall_severity="major",
            summary="Major bleeding risk from concurrent warfarin and aspirin.",
            findings=[
                {
                    "category": "interaction",
                    "drugs": ["warfarin", "aspirin"],
                    "severity": "major",
                    "citation_doc_id": "warfarin_aspirin",
                    "citation_title": "Warfarin + Aspirin",
                }
            ],
        )
    )
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state(
        "Patient takes Warfarin 5mg daily and Aspirin 81mg daily.", {"age": 68, "renal_function": "normal"}
    )
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["pharmacist_review_flag"] is True
    assert len(result["interaction_findings"]) == 1
    finding = result["interaction_findings"][0]
    assert finding["citation_doc_id"] == "warfarin_aspirin"
    assert finding["severity"] == "major"
    assert result["report"]["overall_severity"] == "major"
