# Security Architecture

## Prompt-injection defense

`backend/app/security/injection_detector.py::detect_injection` is a two-layer hybrid, run
against the raw free-text prescription/notes field before anything else touches it (first
thing the Prescription Parser node does):

1. **Heuristic scan** (`heuristic_scan`) — a fixed list of regex patterns for known
   injection phrasings ("ignore all previous instructions", "reveal your system prompt",
   "act as an unrestricted/jailbroken/DAN assistant", literal chat-template delimiters like
   `<|im_start|>`, etc.). Matches short-circuit immediately: free, instant, and catches the
   obvious cases even if the LLM classifier layer is down or misconfigured.
2. **LLM classifier fallback** — anything that passes the heuristic is still checked by a
   dedicated classifier call (`llm.with_structured_output(InjectionClassification)`) with a
   system prompt that explicitly instructs it not to flag ordinary clinical language, however
   unusual, only genuine attempts to manipulate the assistant's behavior.

If either layer flags the text, the graph routes straight to `final_output` without ever
running drug normalization, RAG retrieval, or synthesis on attacker-controlled input —
see `docs/langgraph-workflow.md`'s routing section. Proven end-to-end (through the real
production graph, not a unit in isolation) in `backend/tests/security/test_prompt_injection.py`
for both the heuristic-caught and LLM-classifier-caught cases, plus a legitimate-clinical-text
case to confirm the detector doesn't over-trigger.

## Auth

`X-API-Key` on every `/api/v1/*` route, fail-closed (`docs/api-architecture.md`). No user
accounts or sessions in this project's scope — it's a single shared API key model, appropriate
for a backend consumed by one first-party frontend.

## What's out of scope

This project does not implement PHI-grade access controls, audit-log immutability
guarantees, or HIPAA compliance controls (encryption-at-rest key management, BAA-level
infrastructure, etc.) — it's a demonstration of the agentic pipeline and API/security
patterns, not a compliance-ready clinical system. A real deployment handling actual patient
data would need those on top of what's here.
