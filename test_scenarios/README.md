# Test Scenarios

Five required claim scenarios per the spec's deliverables list. Each folder has real, generated
PDF fixtures (open them in a PDF viewer — nothing here is a fixed binary blob, every one is
reproducible via that folder's `generate_fixtures.py`) and an automated proof under
`backend/tests/langgraph/` or `backend/tests/security/` that runs the fixture through the actual
production graph (`build_claim_graph`) end-to-end, not a node in isolation.

| Folder | Scenario | Status |
|---|---|---|
| `01_full_approval/` | A straightforward claim with no coverage gaps or fraud signals | **Done — see its own [README](./01_full_approval/README.md)** |
| `02_partial_approval/` | A claim where some line-items are covered and others are denied | **Done — see its own [README](./02_partial_approval/README.md)** |
| `03_denial/` | A claim denied outright (e.g. excluded procedure, lapsed coverage) | **Done — see its own [README](./03_denial/README.md)** |
| `04_fraud_detected/` | A claim exercising all four fraud signal types | **Done — see its own [README](./04_fraud_detected/README.md)** |
| `05_prompt_injection_attack/` | The spec's named test case — real PDF fixtures + the automated end-to-end proof that the hybrid Security Checker catches injection embedded in an uploaded claim PDF, run through the actual production graph | **Done — see its own [README](./05_prompt_injection_attack/README.md)** |

## A note on how these were verified

Every scenario's automated test uses a scripted fake chat model (`MultiSchemaFakeChatModel`,
`backend/tests/fakes.py`, whose per-schema responses can be a sequence consumed one-per-call —
what the retry-loop test scripts a low-then-high Self-Critic score with) rather than a live LLM
call — that's what makes the suite deterministic, free to run, and safe in CI with no API key.
The fixtures'
document text is written to be a realistic, internally-consistent claim a human reviewer can read
and recognize the scenario from; the *decision itself* (approved/denied/fraud signals) comes from
the scripted model response, not from the graph actually reasoning over the PDF text. Where a
node's own logic is real and unmocked — Fraud Detector's `compute_fraud_score()` aggregation and
`attorney_flag` check, Security Checker's heuristic regex layer — the test docstrings say so
explicitly, since that's the part actually being verified beyond wiring.
