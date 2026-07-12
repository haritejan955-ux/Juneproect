"""Unit tests for [1] Document Preprocessor.

No LLM involved, so these exercise the real PDF-parsing path against real
(tiny, generated) PDF files rather than mocking PyMuPDF — the risk in this
node is in the parsing/chunking logic itself, so faking that away would
test nothing.
"""

from pathlib import Path

import fitz
import pytest

from app.agents.nodes.document_preprocessor import build_document_preprocessor_node
from app.core.exceptions import InvalidUploadError
from app.state.graph_state import GraphState, RawDocument


def _make_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


def _raw_doc(path: Path, doc_type: str = "cms_1500") -> RawDocument:
    return RawDocument(
        filename=path.name,
        storage_path=str(path),
        doc_type=doc_type,
        content_type="application/pdf",
    )


@pytest.fixture
def node():
    return build_document_preprocessor_node()


async def test_parses_valid_pdf_into_chunks(tmp_path: Path, node):
    pdf_path = tmp_path / "claim.pdf"
    _make_pdf(pdf_path, "SECTION 1 Diagnosis\nPatient diagnosed with M54.5, CPT 97110.")

    state: GraphState = {
        "claim_id": "c1",
        "query": "is this covered",
        "claim_document": [_raw_doc(pdf_path)],
    }
    result = await node(state)

    assert len(result["chunks"]) >= 1
    assert result["document_metadata"]["document_count"] == 1
    assert result["document_metadata"]["failed_files"] == []
    assert result["audit_log"][0]["agent"] == "document_preprocessor"
    assert result["audit_log"][0]["action"] == "parsed_and_chunked_documents"


async def test_flags_pii_when_present(tmp_path: Path, node):
    pdf_path = tmp_path / "claim.pdf"
    _make_pdf(pdf_path, "Patient SSN: 123-45-6789 on file.")

    state: GraphState = {
        "claim_id": "c1",
        "query": "q",
        "claim_document": [_raw_doc(pdf_path)],
    }
    result = await node(state)

    assert result["pii_detected"] is True
    assert result["audit_log"][0]["details"]["pii_flag_count"] >= 1


async def test_no_pii_in_ordinary_claim_text(tmp_path: Path, node):
    pdf_path = tmp_path / "claim.pdf"
    _make_pdf(pdf_path, "Patient was seen for lower back pain.")

    state: GraphState = {
        "claim_id": "c1",
        "query": "q",
        "claim_document": [_raw_doc(pdf_path)],
    }
    result = await node(state)

    assert result["pii_detected"] is False


async def test_empty_claim_document_list_produces_no_chunks(node):
    state: GraphState = {"claim_id": "c1", "query": "q", "claim_document": []}
    result = await node(state)

    assert result["chunks"] == []
    assert result["pii_detected"] is False


async def test_one_corrupt_file_among_several_is_skipped_not_fatal(tmp_path: Path, node):
    good_pdf = tmp_path / "good.pdf"
    _make_pdf(good_pdf, "SECTION 1 Coverage\nSome real content here.")
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"not a real pdf")

    state: GraphState = {
        "claim_id": "c1",
        "query": "q",
        "claim_document": [_raw_doc(good_pdf), _raw_doc(bad_pdf)],
    }
    result = await node(state)

    assert len(result["chunks"]) >= 1
    assert result["document_metadata"]["failed_files"] == ["bad.pdf"]


async def test_all_files_failing_to_parse_raises_invalid_upload_error(tmp_path: Path, node):
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"not a real pdf")

    state: GraphState = {
        "claim_id": "c1",
        "query": "q",
        "claim_document": [_raw_doc(bad_pdf)],
    }

    with pytest.raises(InvalidUploadError):
        await node(state)
