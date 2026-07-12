from pathlib import Path

import fitz
import pytest

from app.vectorstore.document_loading import content_hash, load_document_text


def test_loads_markdown_directly(tmp_path: Path):
    path = tmp_path / "test.md"
    path.write_text("# Title\n\nSome content.", encoding="utf-8")

    assert load_document_text(path) == "# Title\n\nSome content."


def test_loads_txt_directly(tmp_path: Path):
    path = tmp_path / "test.txt"
    path.write_text("plain text content", encoding="utf-8")

    assert load_document_text(path) == "plain text content"


def test_loads_pdf_via_pymupdf(tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PDF extracted text")
    doc.save(str(pdf_path))
    doc.close()

    assert "PDF extracted text" in load_document_text(pdf_path)


def test_unsupported_extension_raises_value_error(tmp_path: Path):
    path = tmp_path / "test.docx"
    path.write_bytes(b"not really a docx")

    with pytest.raises(ValueError, match="Unsupported document type"):
        load_document_text(path)


def test_content_hash_is_stable_and_content_sensitive():
    hash_a = content_hash("some chunk text")
    hash_b = content_hash("some chunk text")
    hash_c = content_hash("different chunk text")

    assert hash_a == hash_b
    assert hash_a != hash_c
