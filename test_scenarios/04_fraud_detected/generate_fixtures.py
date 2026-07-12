"""Generates the PDF fixture for the "fraud detected" scenario — a claim
exercising all four required fraud signal types (duplicate billing,
upcoding, date conflict, unbundling) in one submission, per the spec's
required test scenario list.

    cd backend && pip install -e ".[dev]"
    python ../test_scenarios/04_fraud_detected/generate_fixtures.py
"""

from pathlib import Path

import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent

FIXTURES: dict[str, str] = {
    "01_multiple_fraud_signals.pdf": """SECTION 1 Patient Information
Patient Name: Marcus Webb
Claimant ID: claimant-fraud-01
Policy Number: POL-51204-D
Date of Service: 05/01/2026
Policy Effective Date: 06/01/2026
Diagnosis: M54.5 (low back pain)

SECTION 2 Adjuster Notes
Documentation for this encounter supports a brief, low-complexity office
visit. The claim as submitted raises several concerns: the same visit code
appears twice for the identical date of service; the complexity level
billed is inconsistent with the clinical notes on file; the stated date of
service precedes the policy's effective date; and two component lab codes
were billed separately despite representing a single bundled panel under
standard coding edits.

SECTION 3 Procedure
CPT 99215 - Established patient office visit, high complexity. Billed
amount: $280.00.
CPT 99215 - Established patient office visit, high complexity (duplicate
entry, same date of service). Billed amount: $280.00.
CPT 36415 - Collection of venous blood by venipuncture. Billed amount:
$15.00.
CPT 80053 - Comprehensive metabolic panel. Billed amount: $45.00.
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
