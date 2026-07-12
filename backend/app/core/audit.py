from datetime import UTC, datetime

from app.state.graph_state import AuditLogEntry


def audit_update(agent: str, action: str, details: dict | None = None) -> dict:
    """Build a partial GraphState update appending one audit_log entry.

    Every node returns `{**own_updates, **audit_update(...)}` — because
    `audit_log` uses the `operator.add` reducer (see state/graph_state.py),
    this appends rather than overwrites what previous nodes wrote.
    """
    entry: AuditLogEntry = {
        "agent": agent,
        "action": action,
        "details": details or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return {"audit_log": [entry]}
