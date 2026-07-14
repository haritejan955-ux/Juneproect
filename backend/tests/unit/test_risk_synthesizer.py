import app.agents.nodes.risk_synthesizer as synthesizer_node
from app.schemas.models import SafetyReportOutput


def test_synthesizes_report_from_findings(monkeypatch, fake_llm):
    monkeypatch.setattr(synthesizer_node, "get_chat_model", lambda: fake_llm)
    fake_llm.queue(
        SafetyReportOutput(
            overall_severity="major",
            summary="Major bleeding risk from warfarin + aspirin.",
            findings=[{"category": "interaction", "severity": "major"}],
        )
    )

    state = {
        "medications": [],
        "patient_profile": {},
        "interaction_findings": [{"severity": "major"}],
        "allergy_findings": [],
        "dosage_findings": [],
        "retry_count": 0,
    }
    result = synthesizer_node.run(state)

    assert result["report"]["overall_severity"] == "major"
    assert result["audit_log"][0]["agent"] == "risk_synthesizer"


def test_injects_critique_into_prompt_on_retry(monkeypatch, fake_llm):
    captured_messages = []

    class _CapturingRunnable:
        def invoke(self, messages):
            captured_messages.extend(messages)
            return SafetyReportOutput(overall_severity="none", summary="ok", findings=[])

    monkeypatch.setattr(synthesizer_node, "get_chat_model", lambda: fake_llm)
    monkeypatch.setattr(fake_llm, "with_structured_output", lambda schema: _CapturingRunnable())

    state = {
        "medications": [],
        "patient_profile": {},
        "interaction_findings": [],
        "allergy_findings": [],
        "dosage_findings": [],
        "retry_count": 1,
        "critique": "You missed the digoxin-furosemide interaction.",
    }
    synthesizer_node.run(state)

    human_message = captured_messages[-1]
    assert "digoxin-furosemide" in human_message.content
