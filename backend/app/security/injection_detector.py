"""Hybrid prompt-injection detector: heuristic layer OR LLM classifier layer.

The spec's evaluation test case is explicit that a keyword-only regex
solution fails it, so the two layers are OR'd, not AND'd — either flagging
above its threshold is sufficient to block. See
docs/security-architecture.md section 3 for the full rationale.
"""

import re
from typing import TypedDict

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.prompts.security_checker_prompt import build_security_checker_prompt

logger = get_logger(__name__)


class SecurityFlags(TypedDict):
    """Full hybrid-detection result. Not a GraphState field — the Security Checker node reduces
    this to a single `security_flag: bool` for state (all `route_after_security` needs) and
    writes this full dict into its audit_log entry's `details` for forensic detail."""

    injection_detected: bool
    heuristic_matched_patterns: list[str]
    llm_confidence: float
    llm_reasoning: str | None

_INSTRUCTION_OVERRIDE_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions?\b", re.I),
    re.compile(
        r"\bdisregard\s+(all\s+)?(the\s+)?(previous|prior|above)\s+(instructions?|guidance)\b",
        re.I,
    ),
    re.compile(r"\boverride\s+(the\s+)?(system\s+)?(prompt|instructions?)\b", re.I),
    re.compile(r"\byou\s+are\s+now\s+(a|an)\b", re.I),
    re.compile(r"\bnew\s+instructions?\s*:", re.I),
    re.compile(r"\bapprove\s+all\s+claims?\b", re.I),
    re.compile(r"\bact\s+as\s+(if\s+you\s+are\s+)?(a|an)\s+(different|new)\b", re.I),
]

_INVISIBLE_CHAR_PATTERN = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")


class InjectionClassification(BaseModel):
    is_injection: bool = Field(
        description="True if the text attempts to override or manipulate the "
        "assistant's instructions"
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


def heuristic_scan(text: str) -> list[str]:
    matched = [p.pattern for p in _INSTRUCTION_OVERRIDE_PATTERNS if p.search(text)]
    if _INVISIBLE_CHAR_PATTERN.search(text):
        matched.append("invisible_unicode_characters")
    return matched


class InjectionDetector:
    def __init__(self, chat_model: BaseChatModel, block_confidence: float) -> None:
        self._classifier = chat_model.with_structured_output(InjectionClassification)
        self._block_confidence = block_confidence

    async def detect(self, text: str) -> SecurityFlags:
        heuristic_matches = heuristic_scan(text)

        try:
            classification = await self._classifier.ainvoke(build_security_checker_prompt(text))
        except Exception as exc:
            # Fail CLOSED, not open: if the LLM classifier layer can't run, we cannot confirm
            # this claim is safe. A transient provider outage blocking claims is an acceptable
            # cost; a broken classifier silently downgrading to heuristic-only detection and
            # letting an injection through is not. See docs/security-architecture.md section 3.
            logger.error(
                "injection_detector.classifier_failed",
                extra={"error": str(exc), "heuristic_matches": heuristic_matches},
                exc_info=True,
            )
            return SecurityFlags(
                injection_detected=True,
                heuristic_matched_patterns=heuristic_matches,
                llm_confidence=1.0,
                llm_reasoning=(
                    f"LLM classifier layer failed ({exc}); failing closed and blocking as a "
                    "precaution rather than proceeding on heuristic-only detection."
                ),
            )

        if not isinstance(classification, InjectionClassification):
            logger.error(
                "injection_detector.unexpected_response_type",
                extra={"actual_type": type(classification).__name__},
            )
            return SecurityFlags(
                injection_detected=True,
                heuristic_matched_patterns=heuristic_matches,
                llm_confidence=1.0,
                llm_reasoning=(
                    "LLM classifier returned an unexpected response type; failing closed."
                ),
            )

        llm_flagged = (
            classification.is_injection and classification.confidence >= self._block_confidence
        )

        return SecurityFlags(
            injection_detected=bool(heuristic_matches) or llm_flagged,
            heuristic_matched_patterns=heuristic_matches,
            llm_confidence=classification.confidence,
            llm_reasoning=classification.reasoning,
        )
