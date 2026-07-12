"""Generates the PDF fixture for the "partial approval" scenario — a claim
where one line-item is covered and another is excluded, per the spec's
required test scenario list.

    cd backend && pip install -e ".[dev]"
    python ../test_scenarios/02_partial_approval/generate_fixtures.py
"""

from pathlib import Path

import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent

FIXTURES: dict[str, str] = {
    "01_therapy_plus_cosmetic_procedure.pdf": """SECTION 1 Patient Information
Patient Name: David Okafor
Claimant ID: claimant-partial-approval-01
Policy Number: POL-40217-B
Date of Service: 03/18/2026
Policy Effective Date: 06/01/2024
Diagnosis: M54.5 (low back pain); L70.0 (acne)

SECTION 2 Adjuster Notes
Patient was seen for two unrelated matters in the same visit: ongoing
physical therapy for chronic low back pain, and a separate request for
dermabrasion to treat acne scarring. The physical therapy is medically
necessary and supported by a physician referral; the dermabrasion was
requested for cosmetic improvement only, with no functional or medical
justification documented.

SECTION 3 Procedure
CPT 97110 - Therapeutic exercise, one unit. Billed amount: $90.00.
CPT 15780 - Dermabrasion, total face, cosmetic. Billed amount: $800.00.
""",
}


def _write_pdf(filename: str, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11)
    doc.save(str(FIXTURES_DIR / filename))
    doc.close()
    print(f"wrote {filename}")


def main() -> None:
    for filename, text in FIXTURES.items():
        _write_pdf(filename, text)


if __name__ == "__main__":
    main()
