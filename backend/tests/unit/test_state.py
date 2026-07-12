"""Verifies the shared GraphState schema itself: every field the spec's
shared-state requirements name must exist, on the actual TypedDict, with a
concrete type — not just documented in prose."""

import operator
import typing

from app.state.graph_state import AuditLogEntry, ConversationTurn, GraphState

_REQUIRED_FIELDS = {
    "claim_id",
    "claim_document",
    "chunks",
    "retrieved_chunks",
    "intent",
    "coverage",
    "fraud_score",
    "fraud_signals",
    "citations",
    "confidence",
    "retry_count",
    "audit_log",
    "attorney_flag",
    "security_flag",
    "pii_detected",
    "self_critique",
    "decision",
    "conversation_history",
}


def test_graph_state_declares_every_required_field():
    annotations = GraphState.__annotations__
    missing = _REQUIRED_FIELDS - annotations.keys()
    assert not missing, f"GraphState is missing required fields: {missing}"


def test_graph_state_fields_are_concretely_typed_not_any():
    hints = typing.get_type_hints(GraphState, include_extras=True)
    for field in _REQUIRED_FIELDS:
        assert hints[field] is not typing.Any, f"{field} is untyped (Any)"


def test_audit_log_uses_operator_add_reducer():
    hints = typing.get_type_hints(GraphState, include_extras=True)
    metadata = typing.get_args(hints["audit_log"])[1:]
    assert operator.add in metadata


def test_conversation_history_uses_operator_add_reducer():
    """Same accumulation contract as audit_log — see graph_state.py's
    docstring on ConversationTurn for why this must append, not overwrite,
    across dispute messages."""
    hints = typing.get_type_hints(GraphState, include_extras=True)
    metadata = typing.get_args(hints["conversation_history"])[1:]
    assert operator.add in metadata


def test_audit_log_entry_is_fully_typed():
    hints = typing.get_type_hints(AuditLogEntry)
    assert hints.keys() == {"agent", "action", "details", "timestamp"}
    assert hints["agent"] is str
    assert hints["timestamp"] is str


def test_conversation_turn_is_fully_typed():
    hints = typing.get_type_hints(ConversationTurn)
    assert hints.keys() == {"role", "content", "timestamp"}
