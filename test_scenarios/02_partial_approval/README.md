# Scenario 2 — Partial Approval

A claim where one line-item is covered and another is excluded — the spec's
required "some line-items covered, others denied" scenario. Real, generated
PDF; see
[`backend/tests/langgraph/test_partial_approval_scenario.py`](../../backend/tests/langgraph/test_partial_approval_scenario.py)
for the automated proof.

Regenerate with:

```bash
cd backend && pip install -e ".[dev]"
python ../test_scenarios/02_partial_approval/generate_fixtures.py
```

## Fixture

| File | Contains | Expected outcome |
|---|---|---|
| `01_therapy_plus_cosmetic_procedure.pdf` | Two unrelated procedures in one visit: medically-necessary physical therapy (CPT 97110) and an elective cosmetic procedure (CPT 15780) | `status: "partial_approved"`, one approved line-item, one denied line-item citing the plan's cosmetic-procedure exclusion |

## What the automated test proves

Runs the PDF through `build_claim_graph` end-to-end with a scripted fake
chat model, and asserts the finalized decision is `partial_approved` with
exactly one `approved` and one `denied` coverage line-item — each denied
line-item carries a non-empty `cited_clause`, matching the acceptance
criterion that every decision cites a specific policy clause, not just
approvals.
