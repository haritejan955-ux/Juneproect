"""Hybrid prompt-injection detector: heuristic layer OR LLM classifier layer.

The spec's evaluation test case is explicit that a keyword-only regex
solution fails it, so the two layers are OR'd, not AND'd — either flagging
above its threshold is sufficient to block. See
docs/security-architecture.md section 3 for the full rationale.
"""

import re

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.prompts.security_checker_prompt import build_security_checker_prompt
from app.state.graph_state import SecurityFlags

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

        classification = await self._classifier.ainvoke(build_security_checker_prompt(text))
        assert isinstance(classification, InjectionClassification)

        llm_flagged = (
            classification.is_injection and classification.confidence >= self._block_confidence
        )

        return SecurityFlags(
            injection_detected=bool(heuristic_matches) or llm_flagged,
            heuristic_matched_patterns=heuristic_matches,
            llm_confidence=classification.confidence,
            llm_reasoning=classification.reasoning,
        )
