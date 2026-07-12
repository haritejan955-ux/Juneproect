# Scenario 4 — Fraud Detected

A claim exercising all four required fraud signal types in one submission —
the spec's fraud-detection scenario. Real, generated PDF; see
[`backend/tests/langgraph/test_fraud_detected_scenario.py`](../../backend/tests/langgraph/test_fraud_detected_scenario.py)
for the automated proof.

Regenerate with:

```bash
cd backend && pip install -e ".[dev]"
python ../test_scenarios/04_fraud_detected/generate_fixtures.py
```

## Fixture

| File | Contains | Expected outcome |
|---|---|---|
| `01_multiple_fraud_signals.pdf` | A visit billed twice for the same date of service (**duplicate billing**), a complexity level inconsistent with the clinical notes (**upcoding**), a service date preceding the policy's effective date (**date conflict**), and two component lab codes billed separately instead of as one bundled panel (**unbundling**) | `fraud_signals` contains one entry per signal type (4 total), the duplicate-billing signal is `severity: "high"`, `attorney_flag: true`, `fraud_score` reflects the highest-severity signal |

## What the automated test proves

Runs the PDF through `build_claim_graph` end-to-end with a scripted fake
chat model that returns all four fraud signal types from Fraud Detector's
structured output — but `fraud_score` and `attorney_flag` themselves are
**not** part of that scripted response. They're computed by
`fraud_detector.py`'s real, unmocked `compute_fraud_score()` and the
high-severity check, so this test is proof those two real code paths
correctly aggregate a scripted set of signals, not just that the fixture
"contains" the right words. `attorney_flag: true` here is contrasted
directly with Scenario 3's plain denial, where it stays `false`.
