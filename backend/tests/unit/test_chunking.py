from app.vectorstore.chunking import chunk_by_clause, extract_preserved_codes


def test_extract_preserved_codes_finds_cpt_icd10_and_section_numbers():
    codes = extract_preserved_codes("Procedure 99213 for diagnosis M54.5, per section 2.1")
    assert "99213" in codes
    assert "M54.5" in codes
    assert "2.1" in codes


def test_chunk_by_clause_splits_on_section_headers():
    text = "SECTION 1 Overview\nSome introductory text.\n\nSECTION 2 Coverage\nMore text here."
    chunks = chunk_by_clause(text)
    assert len(chunks) == 2
    assert chunks[0].section is not None
    assert chunks[1].section is not None


def test_chunk_by_clause_falls_back_to_paragraph_breaks_without_headers():
    text = "First paragraph with no structural marker.\n\nSecond distinct paragraph."
    chunks = chunk_by_clause(text)
    assert len(chunks) == 2


def test_chunk_by_clause_preserves_codes_per_chunk():
    text = "SECTION 1 Diagnosis\nPatient diagnosed with M54.5, billed under CPT 97110."
    chunks = chunk_by_clause(text)
    assert any("97110" in chunk.preserved_codes for chunk in chunks)
    assert any("M54.5" in chunk.preserved_codes for chunk in chunks)


def test_chunk_by_clause_handles_empty_text():
    assert chunk_by_clause("") == []
