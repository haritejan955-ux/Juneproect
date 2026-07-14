# LangGraph Workflow

`backend/app/agents/graph.py` builds and compiles the `StateGraph[GraphState]`.

## Conditional routing

Two decision points, both in `backend/app/agents/routing.py`:

1. **`route_after_parser`** — reads `injection_detected`. If a prompt-injection attempt was
   caught (heuristic or LLM classifier), the graph short-circuits straight to `final_output`,
   skipping drug normalization, interaction/allergy/dosage checks, and synthesis entirely — an
   injection attempt never reaches the LLM calls that do real clinical reasoning.
2. **`route_after_critic`** — reads `critique_approved` and `retry_count`. Approved → straight
   to `final_output`. Not approved and under `MAX_SYNTHESIS_RETRIES` (default 2) → `prepare_retry`,
   which increments `retry_count` and loops back to `risk_synthesizer` with the critique injected
   into its prompt. Not approved and out of retries → `final_output` anyway (the guard's job is
   to bound the loop, not to block output indefinitely; the report that ships is the best
   available draft, and `retry_count` in the audit trail records that it wasn't approved).

## Retry-loop guard

The increment lives in a dedicated node (`prepare_retry`) rather than inline in the
conditional-edge function, for two reasons: it shows up as its own audit log entry (so a
reviewer can see exactly how many synthesis attempts a report went through), and it makes the
increment impossible to bypass — every path back to `risk_synthesizer` goes through it.

## Streaming

The FastAPI layer runs the graph with `stream_mode="values"` (`backend/app/services/graph_runner.py`),
which yields the full merged state after every node completes, not just the node's delta. This
makes it trivial to read "which agent just ran" off `audit_log[-1]["agent"]` without maintaining
separate bookkeeping, and it's how the WebSocket progress feed (`/ws/reports/{id}`) gets its
per-agent updates.

## Why LLM calls are synchronous

The nodes call `llm.with_structured_output(Schema).invoke(...)` synchronously — LangGraph and
the langchain sync client handle that fine, and it keeps every node a plain, easily-unit-testable
function. The FastAPI layer runs the whole graph on a worker thread (`threading.Thread` inside
`run_and_broadcast`) so a multi-second LLM-bound graph run never blocks the async event loop that
serves other requests.
