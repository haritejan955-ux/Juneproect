"""Clause/section-boundary chunking — never fixed-token-window splitting.

Fixed-size chunking is explicitly called out in the spec as a failure mode
("token splits, lost structure") because it can split a CPT code or a policy
section number across chunk boundaries. This chunker splits on structural
markers (markdown headers, numbered clauses, form section labels) and only
falls back to paragraph breaks when no structural marker is present.
"""

import re
from dataclasses import dataclass, field
from uuid import uuid4

CPT_CODE_PATTERN = re.compile(r"\b\d{5}\b")
ICD10_CODE_PATTERN = re.compile(r"\b[A-TV-Z][0-9][0-9AB](?:\.[0-9A-TV-Z]{1,4})?\b")
SECTION_NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3})+\b")

_HEADER_PATTERN = re.compile(
    r"^(?:#{1,6}\s+.+|(?:SECTION|ARTICLE|CLAUSE)\s+[\dIVXLC]+.*|\d{1,3}(?:\.\d{1,3})*\s+[A-Z].+)$",
    re.MULTILINE,
)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    section: str | None
    preserved_codes: list[str] = field(default_factory=list)


def extract_preserved_codes(text: str) -> list[str]:
    codes = set(CPT_CODE_PATTERN.findall(text))
    codes.update(ICD10_CODE_PATTERN.findall(text))
    codes.update(SECTION_NUMBER_PATTERN.findall(text))
    return sorted(codes)


def chunk_by_clause(text: str, doc_type: str = "generic") -> list[Chunk]:
    """Split `text` into clause-level chunks, preserving structural headers."""
    text = text.strip()
    if not text:
        return []

    header_matches = list(_HEADER_PATTERN.finditer(text))

    if header_matches:
        boundaries = [m.start() for m in header_matches] + [len(text)]
        raw_sections: list[tuple[str | None, str]] = []
        for i in range(len(header_matches)):
            start = boundaries[i]
            end = boundaries[i + 1]
            section_text = text[start:end].strip()
            if not section_text:
                continue
            header_line = header_matches[i].group(0).strip()
            raw_sections.append((header_line, section_text))
        if header_matches[0].start() > 0:
            preamble = text[: header_matches[0].start()].strip()
            if preamble:
                raw_sections.insert(0, (None, preamble))
    else:
        raw_sections = [
            (None, para.strip()) for para in re.split(r"\n\s*\n", text) if para.strip()
        ]

    chunks: list[Chunk] = []
    for section, section_text in raw_sections:
        chunks.append(
            Chunk(
                chunk_id=str(uuid4()),
                text=section_text,
                section=section,
                preserved_codes=extract_preserved_codes(section_text),
            )
        )
    return chunks
