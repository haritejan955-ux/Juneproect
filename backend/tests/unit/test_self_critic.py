import app.agents.nodes.self_critic as critic_node
from app.schemas.models import CritiqueResult


def test_approved_report_clears_critique(monkeypatch, fake_llm):
    monkeypatch.setattr(critic_node, "get_chat_model", lambda: fake_llm)
    fake_llm.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    result = critic_node.run({"report": {"overall_severity": "none"}})

    assert result["critique_approved"] is True
    assert result["critique"] is None


def test_rejected_report_carries_critique_forward(monkeypatch, fake_llm):
    monkeypatch.setattr(critic_node, "get_chat_model", lambda: fake_llm)
    fake_llm.queue(
        CritiqueResult(
            approved=False,
            critique="Missing the digoxin-furosemide interaction.",
            missed_considerations=["digoxin_furosemide"],
        )
    )

    result = critic_node.run({"report": {"overall_severity": "none"}})

    assert result["critique_approved"] is False
    assert "digoxin" in result["critique"]
