import operator

from app.core.audit import audit_update


def test_audit_update_returns_single_entry_list():
    result = audit_update("test_agent", "did_something", {"key": "value"})
    assert "audit_log" in result
    assert len(result["audit_log"]) == 1
    entry = result["audit_log"][0]
    assert entry["agent"] == "test_agent"
    assert entry["action"] == "did_something"
    assert entry["details"] == {"key": "value"}
    assert entry["timestamp"]


def test_audit_update_defaults_details_to_empty_dict():
    result = audit_update("test_agent", "did_something")
    assert result["audit_log"][0]["details"] == {}


def test_audit_log_reducer_accumulates_instead_of_overwriting():
    """Mirrors GraphState's `Annotated[list[AuditLogEntry], operator.add]`
    reducer — this is what guarantees one agent's audit entry can never
    clobber another's."""
    log_a = audit_update("agent_a", "action_a")["audit_log"]
    log_b = audit_update("agent_b", "action_b")["audit_log"]
    combined = operator.add(log_a, log_b)
    assert len(combined) == 2
    assert combined[0]["agent"] == "agent_a"
    assert combined[1]["agent"] == "agent_b"
