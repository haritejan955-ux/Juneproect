from app.agents.graph import build_safety_graph, initial_state
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification


def test_penicillin_allergy_blocks_amoxicillin(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[
                Medication(raw_name="Amoxicillin", dose_value=500, dose_unit="mg", frequency="every 8 hours", route="oral")
            ]
        )
    )
    graph_fakes.queue(
        SafetyReportOutput(
            overall_severity="contraindicated",
            summary="Amoxicillin is contraindicated given the patient's documented penicillin allergy.",
            findings=[
                {
                    "category": "allergy",
                    "drug": "Amoxicillin",
                    "severity": "contraindicated",
                    "description": "Patient has a documented penicillin allergy.",
                }
            ],
        )
    )
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    graph = build_safety_graph()
    state = initial_state(
        "Prescribe Amoxicillin 500mg every 8 hours for sinusitis.",
        {"age": 34, "allergies": ["penicillin"], "renal_function": "normal"},
    )
    result = graph.invoke(state)

    assert result["status"] == "complete"
    assert result["pharmacist_review_flag"] is True
    assert len(result["allergy_findings"]) == 1
    assert result["allergy_findings"][0]["severity"] == "contraindicated"
    assert result["report"]["overall_severity"] == "contraindicated"
