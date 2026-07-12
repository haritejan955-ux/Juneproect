"""Regex + field-label-proximity PII detection and redaction.

No NER model dependency: CMS-1500/EOB/accident-report/denial-letter
documents have PII in structurally predictable, labeled positions, so a
bare number is only flagged when a recognized field label appears nearby
(e.g. a 9-digit number near "Patient's SSN" is flagged; a bare 9-digit
number elsewhere is not, since it is likely a claim/policy number). See
docs/security-architecture.md section 4.
"""

import re
from typing import Literal, TypedDict

from app.state.graph_state import DocumentChunk

PIIType = Literal["SSN", "DOB", "EIN"]


class PIIFlag(TypedDict):
    """Per-chunk detection detail. Not a GraphState field — the node that calls `flag_pii`
    reduces this to a single `pii_detected: bool` for state and writes this full list into its
    audit_log entry's `details` instead, since no downstream node branches on which specific
    chunk/field was flagged (see docs/security-architecture.md section 4)."""

    chunk_id: str
    pii_type: PIIType
    field_label: str | None


SSN_DASHED_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SSN_BARE_PATTERN = re.compile(r"\b\d{9}\b")
EIN_PATTERN = re.compile(r"\b\d{2}-\d{7}\b")
DATE_PATTERN = re.compile(r"\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:\d{4}|\d{2})\b")

_LABEL_WINDOW = 40
_SSN_LABELS = ("ssn", "social security")
_DOB_LABELS = ("dob", "date of birth", "birth date")
_EIN_LABELS = ("ein", "employer identification", "tax id")


def _label_nearby(text: str, match_start: int, labels: tuple[str, ...]) -> str | None:
    window = text[max(0, match_start - _LABEL_WINDOW) : match_start].lower()
    return next((label for label in labels if label in window), None)


def flag_pii(chunks: list[DocumentChunk]) -> list[PIIFlag]:
    flags: list[PIIFlag] = []
    for chunk in chunks:
        text = chunk["text"]

        for match in SSN_DASHED_PATTERN.finditer(text):
            flags.append(
                PIIFlag(
                    chunk_id=chunk["chunk_id"],
                    pii_type="SSN",
                    field_label=_label_nearby(text, match.start(), _SSN_LABELS),
                )
            )
        for match in SSN_BARE_PATTERN.finditer(text):
            label = _label_nearby(text, match.start(), _SSN_LABELS)
            if label:
                flags.append(PIIFlag(chunk_id=chunk["chunk_id"], pii_type="SSN", field_label=label))

        for match in EIN_PATTERN.finditer(text):
            flags.append(
                PIIFlag(
                    chunk_id=chunk["chunk_id"],
                    pii_type="EIN",
                    field_label=_label_nearby(text, match.start(), _EIN_LABELS),
                )
            )

        for match in DATE_PATTERN.finditer(text):
            label = _label_nearby(text, match.start(), _DOB_LABELS)
            if label:
                flags.append(PIIFlag(chunk_id=chunk["chunk_id"], pii_type="DOB", field_label=label))

    return flags


def redact_pii(text: str) -> str:
    text = SSN_DASHED_PATTERN.sub("[REDACTED-SSN]", text)
    text = EIN_PATTERN.sub("[REDACTED-EIN]", text)
    return text
