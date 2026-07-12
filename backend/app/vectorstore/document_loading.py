"""Multi-format document loading for ingestion — supports more than one
kind of document source, not just hand-written markdown. A real policy
corpus is realistically going to include scanned/exported PDFs alongside
authored markdown notes, so ingestion needs to handle both without the
caller caring which it's looking at.

Also used by `app.agents.nodes.document_preprocessor` for the exact same
PDF-extraction logic, so there's one implementation of "how do we get text
out of a PDF," not two that could quietly drift apart.
"""

import hashlib
from pathlib import Path

import fitz  # PyMuPDF

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".md", ".txt"})


def load_document_text(path: Path) -> str:
    """Dispatches on file extension. Raises `ValueError` for anything not
    in `SUPPORTED_EXTENSIONS` rather than silently guessing — an ingestion
    script should fail loudly on an unsupported file, not skip it quietly
    and produce a corpus with an inexplicable gap."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as doc:
            return "\n\n".join(page.get_text() for page in doc)
    if suffix in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    raise ValueError(
        f"Unsupported document type '{suffix}' for {path.name}. "
        f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
    )


def content_hash(text: str) -> str:
    """Stable identity for a chunk of text, independent of *where* it came
    from — the basis for incremental indexing's dedup check (see
    scripts/build_policy_index.py and scripts/generate_synthetic_claims.py):
    if a chunk with this hash is already indexed, re-embedding it on a
    re-run would be wasted API cost for an identical vector."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
