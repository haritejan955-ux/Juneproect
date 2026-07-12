"""[4] Security Checker — hybrid injection detection + PII redaction gate.

Hard block on confirmed injection: this node just sets the flag; the actual
halt is enforced by the conditional edge in agents/routing.py
(`route_after_security`), which routes to a terminal `blocked` node instead
of `coverage_validator`. See docs/security-architecture.md.
"""

from collections.abc import Awaitable, Callable

from app.core.audit import audit_update
from app.core.logging import get_logger
from app.security.injection_detector import InjectionDetector
from app.security.pii_redactor import redact_pii
from app.state.graph_state import GraphState, RetrievedChunk

AGENT_NAME = "security_checker"

logger = get_logger(__name__)


def build_security_checker_node(
    detector: InjectionDetector,
) -> Callable[[GraphState], Awaitable[dict]]:
    async def security_checker(state: GraphState) -> dict:
        claim_id = state["claim_id"]
        logger.info(f"{AGENT_NAME}.started", extra={"claim_id": claim_id})

        try:
            chunks = state.get("chunks", [])
            combined_text = "\n\n".join(chunk["text"] for chunk in chunks)

            security_flags = await detector.detect(combined_text)
            injection_detected = security_flags["injection_detected"]

            redacted_chunks: list[RetrievedChunk] = [
                {**chunk, "text": redact_pii(chunk["text"])}
                for chunk in state.get("retrieved_chunks", [])
            ]
        except Exception as exc:
            # This node is a security gate, not an ordinary pipeline step: a bug here must
            # never silently pass a claim through unscreened. `InjectionDetector.detect()`
            # already fails closed internally on classifier failure (see its docstring); this
            # is the second, outer layer — anything else unexpected in this node (a redaction
            # bug, a malformed chunk) also fails closed rather than propagating an opaque
            # exception that could be mistaken for "nothing to block."
            logger.critical(
                f"{AGENT_NAME}.unexpected_error_failing_closed",
                extra={"claim_id": claim_id, "error": str(exc)},
                exc_info=True,
            )
            return {
                "security_flag": True,
                "redacted_chunks": [],
                **audit_update(
                    AGENT_NAME,
                    "blocked_injection",
                    {
                        "injection_detected": True,
                        "reason": f"security_checker raised an unexpected error: {exc}",
                    },
                ),
            }

        logger.info(
            f"{AGENT_NAME}.completed",
            extra={"claim_id": claim_id, "injection_detected": injection_detected},
        )

        return {
            # Routing only ever needs this boolean — the full hybrid-detection detail
            # (heuristic matches, LLM confidence/reasoning) goes into audit_log below,
            # not GraphState. See SecurityFlags' docstring in security/injection_detector.py.
            "security_flag": injection_detected,
            "redacted_chunks": redacted_chunks,
            **audit_update(
                AGENT_NAME,
                "blocked_injection" if injection_detected else "checked_security",
                {
                    "injection_detected": injection_detected,
                    "heuristic_matches": security_flags["heuristic_matched_patterns"],
                    "llm_confidence": security_flags["llm_confidence"],
                    "llm_reasoning": security_flags["llm_reasoning"],
                },
            ),
        }

    return security_checker
