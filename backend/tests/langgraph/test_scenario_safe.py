from app.agents.graph import build_safety_graph, initial_state
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification


def test_safe_prescription_produces_no_findings(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[
                Medication(raw_name="Tylenol", dose_value=500, dose_unit="mg", frequency="every 6 hours", route="oral")
            ]
        )
    )
    graph_fakes.queue(
        SafetyReportOutput(overall_severity="none", summary="No significant risks identified.", findings=[])
    )
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state("Patient takes Tylenol 500mg every 6 hours.", {"age": 45, "renal_function": "normal"})
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["pharmacist_review_flag"] is False
    assert result["interaction_findings"] == []
    assert result["allergy_findings"] == []
    assert result["dosage_findings"] == []
    agents_run = [entry["agent"] for entry in result["audit_log"]]
    assert agents_run == [
        "prescription_parser",
        "drug_normalizer",
        "patient_profile_loader",
        "interaction_retriever",
        "allergy_checker",
        "dosage_validator",
        "risk_synthesizer",
        "self_critic",
        "final_output",
    ]
