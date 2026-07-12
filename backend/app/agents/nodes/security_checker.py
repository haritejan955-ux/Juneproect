"""[4] Security Checker — hybrid injection detection + PII redaction gate.

Hard block on confirmed injection: this node just sets the flag; the actual
halt is enforced by the conditional edge in agents/routing.py
(`route_after_security`), which routes to a terminal `blocked` node instead
of `coverage_validator`. See docs/security-architecture.md.
"""

from collections.abc import Awaitable, Callable

from app.core.audit import audit_update
from app.security.injection_detector import InjectionDetector
from app.security.pii_redactor import redact_pii
from app.state.graph_state import GraphState, RetrievedChunk

AGENT_NAME = "security_checker"


def build_security_checker_node(
    detector: InjectionDetector,
) -> Callable[[GraphState], Awaitable[dict]]:
    async def security_checker(state: GraphState) -> dict:
        document_chunks = state.get("document_chunks", [])
        combined_text = "\n\n".join(chunk["text"] for chunk in document_chunks)

        security_flags = await detector.detect(combined_text)

        redacted_chunks: list[RetrievedChunk] = [
            {**chunk, "text": redact_pii(chunk["text"])}
            for chunk in state.get("retrieved_chunks", [])
        ]

        return {
            "security_flags": security_flags,
            "injection_detected": security_flags["injection_detected"],
            "redacted_chunks": redacted_chunks,
            **audit_update(
                AGENT_NAME,
                "blocked_injection" if security_flags["injection_detected"] else "checked_security",
                {
                    "injection_detected": security_flags["injection_detected"],
                    "heuristic_matches": security_flags["heuristic_matched_patterns"],
                    "llm_confidence": security_flags["llm_confidence"],
                },
            ),
        }

    return security_checker
