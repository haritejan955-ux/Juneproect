from app.agents.graph import build_safety_graph, initial_state
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification


def test_metformin_contraindicated_in_severe_renal_impairment(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[
                Medication(raw_name="Metformin", dose_value=1000, dose_unit="mg", frequency="twice daily", route="oral")
            ]
        )
    )
    graph_fakes.queue(
        SafetyReportOutput(
            overall_severity="contraindicated",
            summary="Metformin is contraindicated given the patient's severe renal impairment.",
            findings=[
                {
                    "category": "dosage",
                    "drug": "Metformin",
                    "severity": "contraindicated",
                    "description": "Contraindicated with severe renal impairment; risk of lactic acidosis.",
                }
            ],
        )
    )
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state(
        "Prescribe Metformin 1000mg twice daily for type 2 diabetes.",
        {"age": 81, "renal_function": "severe"},
    )
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["pharmacist_review_flag"] is True
    assert len(result["dosage_findings"]) == 1
    assert result["dosage_findings"][0]["severity"] == "contraindicated"
