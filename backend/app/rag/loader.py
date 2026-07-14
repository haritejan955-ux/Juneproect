import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InteractionDoc:
    doc_id: str
    title: str
    severity: str
    drug_pair: list[str]
    text: str
    source_path: str


def load_interaction_corpus(corpus_dir: Path) -> list[InteractionDoc]:
    """Parse every `*.md` monograph in corpus_dir into an InteractionDoc.

    Each file starts with a `---`-delimited JSON frontmatter block (drug_pair,
    severity, title) followed by the monograph body.
    """
    docs: list[InteractionDoc] = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        _, frontmatter_raw, body = raw.split("---", 2)
        meta = json.loads(frontmatter_raw.strip())
        docs.append(
            InteractionDoc(
                doc_id=path.stem,
                title=meta["title"],
                severity=meta["severity"],
                drug_pair=meta["drug_pair"],
                text=body.strip(),
                source_path=str(path),
            )
        )
    return docs
