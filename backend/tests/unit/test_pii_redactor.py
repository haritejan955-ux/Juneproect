from app.security.pii_redactor import flag_pii, redact_pii
from app.state.graph_state import DocumentChunk


def _chunk(text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id="c1", text=text, section=None, doc_type="cms_1500", preserved_codes=[]
    )


def test_flags_dashed_ssn_regardless_of_label():
    flags = flag_pii([_chunk("Patient identifier 123-45-6789 on file.")])
    assert any(f["pii_type"] == "SSN" for f in flags)


def test_flags_bare_ssn_only_when_label_nearby():
    with_label = flag_pii([_chunk("Patient SSN: 123456789 recorded.")])
    without_label = flag_pii([_chunk("Claim reference number 123456789 processed.")])
    assert any(f["pii_type"] == "SSN" for f in with_label)
    assert not any(f["pii_type"] == "SSN" for f in without_label)


def test_flags_dob_only_when_label_nearby():
    with_label = flag_pii([_chunk("Date of Birth: 04/12/1985")])
    without_label = flag_pii([_chunk("Service performed on 04/12/1985")])
    assert any(f["pii_type"] == "DOB" for f in with_label)
    assert not any(f["pii_type"] == "DOB" for f in without_label)


def test_redact_pii_masks_ssn_and_ein():
    redacted = redact_pii("SSN 123-45-6789, EIN 12-3456789")
    assert "123-45-6789" not in redacted
    assert "12-3456789" not in redacted
    assert "[REDACTED-SSN]" in redacted
    assert "[REDACTED-EIN]" in redacted
