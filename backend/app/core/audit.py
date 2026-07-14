from datetime import datetime, timezone
from typing import Any


def audit_entry(agent: str, action: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a single timestamped audit_log entry for a GraphState-carrying agent."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "detail": detail or {},
    }
