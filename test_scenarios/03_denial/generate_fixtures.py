"""Generates the PDF fixture for the "denial" scenario — a claim denied
outright for lapsed coverage (date of service after policy termination),
per the spec's required test scenario list.

    cd backend && pip install -e ".[dev]"
    python ../test_scenarios/03_denial/generate_fixtures.py
"""

from pathlib import Path

import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent

FIXTURES: dict[str, str] = {
    "01_lapsed_coverage.pdf": """SECTION 1 Patient Information
Patient Name: Priya Sharma
Claimant ID: claimant-denial-01
Policy Number: POL-77390-C
Date of Service: 02/14/2026
Policy Effective Date: 01/01/2024
Policy Termination Date: 12/31/2025
Diagnosis: M25.561 (pain in right knee)

SECTION 2 Adjuster Notes
Patient was seen for a follow-up knee evaluation. Policy records confirm
coverage under this policy number was terminated at the end of the prior
calendar year and was not renewed. The date of service on this claim falls
after the termination date, outside any active coverage period.

SECTION 3 Procedure
CPT 99214 - Established patient office visit, moderate complexity.
Billed amount: $220.00.
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
