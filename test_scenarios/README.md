# Test Scenarios

Five required claim scenarios per the spec's deliverables list.

| Folder | Scenario | Status |
|---|---|---|
| `01_full_approval/` | A straightforward claim with no coverage gaps or fraud signals | Scaffolded — content pending |
| `02_partial_approval/` | A claim where some line-items are covered and others are denied | Scaffolded — content pending |
| `03_denial/` | A claim denied outright (e.g. excluded procedure, lapsed coverage) | Scaffolded — content pending |
| `04_fraud_detected/` | A claim exercising all four fraud signal types | Scaffolded — content pending |
| `05_prompt_injection_attack/` | The spec's named test case — real PDF fixtures + the automated end-to-end proof that the hybrid Security Checker catches injection embedded in an uploaded claim PDF, run through the actual production graph | **Done — see its own [README](./05_prompt_injection_attack/README.md)** |

Scaffolded scenarios' sample claim documents, expected decisions, and run instructions are a
follow-up milestone (see [docs/design-decisions.md](../docs/design-decisions.md) "Open items").
