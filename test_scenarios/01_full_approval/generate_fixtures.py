"""Generates the PDF fixture for the "full approval" scenario — a
straightforward claim with no coverage gaps or fraud signals, per the
spec's required test scenario list.

This is a real, generated PDF fixture (not a fixed blob) so it can be
opened and read directly, and regenerated on demand. See
backend/tests/langgraph/test_full_approval_scenario.py for the automated
proof that runs it through the real production graph.

    cd backend && pip install -e ".[dev]"
    python ../test_scenarios/01_full_approval/generate_fixtures.py
"""

from pathlib import Path

import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent

FIXTURES: dict[str, str] = {
    "01_routine_office_visit.pdf": """SECTION 1 Patient Information
Patient Name: Maria Alvarez
Claimant ID: claimant-full-approval-01
Policy Number: POL-88213-A
Date of Service: 05/12/2026
Policy Effective Date: 01/01/2025
Diagnosis: J06.9 (acute upper respiratory infection, unspecified)

SECTION 2 Adjuster Notes
Patient presented with cold and sore throat symptoms and was seen for a
routine, established-patient office visit. No complications were noted
during the encounter. Treatment was limited to a single, low-complexity
visit with no additional procedures performed.

SECTION 3 Procedure
CPT 99213 - Established patient office visit, low complexity.
Billed amount: $150.00.
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
