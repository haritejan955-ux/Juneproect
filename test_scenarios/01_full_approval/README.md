# Scenario 1 — Full Approval

A straightforward claim with no coverage gaps or fraud signals — the spec's
baseline scenario. The PDF is real and generated (not a fixed blob); open it
in a PDF viewer and the text is exactly what
[`backend/tests/langgraph/test_full_approval_scenario.py`](../../backend/tests/langgraph/test_full_approval_scenario.py)
runs through the actual production graph.

Regenerate with:

```bash
cd backend && pip install -e ".[dev]"
python ../test_scenarios/01_full_approval/generate_fixtures.py
```

## Fixture

| File | Contains | Expected outcome |
|---|---|---|
| `01_routine_office_visit.pdf` | A single, low-complexity established-patient office visit (CPT 99213) for an upper respiratory infection, fully within an active policy period | `status: "approved"`, one approved coverage line-item, no fraud signals, `attorney_flag: false` |

## What the automated test proves

`test_full_approval_scenario.py` runs this PDF through `build_claim_graph`
end-to-end with a scripted fake chat model (no live LLM — see the note in
`test_scenarios/05_prompt_injection_attack/README.md` about why these tests
don't depend on real model calls) and asserts the finalized decision is
`approved`, `Self-Critic` passes without a retry, and every line-item in the
coverage map is approved. It's the control case the partial-approval,
denial, and fraud scenarios are contrasted against.
