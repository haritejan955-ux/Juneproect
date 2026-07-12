# Scenario 3 — Denial

A claim denied outright for lapsed coverage — the spec's named example
("excluded procedure, lapsed coverage"). Real, generated PDF; see
[`backend/tests/langgraph/test_denial_scenario.py`](../../backend/tests/langgraph/test_denial_scenario.py)
for the automated proof.

Regenerate with:

```bash
cd backend && pip install -e ".[dev]"
python ../test_scenarios/03_denial/generate_fixtures.py
```

## Fixture

| File | Contains | Expected outcome |
|---|---|---|
| `01_lapsed_coverage.pdf` | A follow-up office visit with a date of service (02/14/2026) after the policy's stated termination date (12/31/2025) | `status: "denied"`, the sole coverage line-item denied and cited against the lapsed-coverage clause, no fraud signals, `attorney_flag: false` |

## What the automated test proves

Runs the PDF through `build_claim_graph` end-to-end with a scripted fake
chat model, and asserts the finalized decision is `denied` with a non-empty
`cited_clause` explaining *why* (lapsed coverage), and that a plain denial
on its own does not set `attorney_flag` — that flag is reserved for
high-severity fraud or high-risk legal interpretation (see Scenario 4),
not every denial.
