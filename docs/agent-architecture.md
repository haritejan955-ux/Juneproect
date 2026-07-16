# Agent Architecture

Nine agents, each a plain function `(GraphState) -> dict` in `backend/app/agents/nodes/`,
wired into a single LangGraph `StateGraph` (`backend/app/agents/graph.py`). Every node reads
whatever fields it needs from `GraphState` and returns only the fields it owns — LangGraph
merges the returned dict into the shared state, and `audit_log` uses an `operator.add`
reducer so every node's entry is appended rather than overwritten.

| # | Agent | File | Reads | Writes | LLM? |
|---|---|---|---|---|---|
| 1 | Prescription Parser | `prescription_parser.py` | `raw_prescription_text` | `medications`, `injection_detected`, `injection_reason` | Yes — hybrid injection check + structured extraction |
| 2 | Drug Normalizer | `drug_normalizer.py` | `medications` | `medications` (enriched), `unrecognized_drugs` | No — local reference table lookup |
| 3 | Patient Profile Loader | `patient_profile_loader.py` | `patient_profile` | `patient_profile` (validated, defaults filled) | No |
| 4 | Interaction Retriever | `interaction_retriever.py` | `medications` | `interaction_findings` | No LLM call, but RAG (FAISS) |
| 5 | Allergy & Contraindication Checker | `allergy_checker.py` | `medications`, `patient_profile` | `allergy_findings` | No |
| 6 | Dosage Validator | `dosage_validator.py` | `medications`, `patient_profile` | `dosage_findings` | No |
| 7 | Risk Synthesizer | `risk_synthesizer.py` | all finding lists, `critique` | `report` | Yes — structured output |
| 8 | Self-Critic | `self_critic.py` | `report`, all finding lists | `critique`, `critique_approved` | Yes — structured output |
| 9 | Final Output | `final_output.py` | `report`, all finding lists, `status` | `pharmacist_review_flag`, `status` | No |

A tenth function, `prepare_retry` (in `routing.py`, not counted among the 9 conceptual
agents — it's plumbing for the retry loop, not a decision-making agent), increments
`retry_count` and is the only place that can trigger another Risk Synthesizer pass.

## Why deterministic checks do most of the work

Only three of the nine agents call an LLM (Parser, Synthesizer, Critic). Interaction
retrieval, allergy/contraindication checking, and dosage validation are implemented as
plain code against `backend/app/data/drug_reference.py` and the FAISS-retrieved monographs.
This is a deliberate choice for a safety-critical domain: a drug-drug interaction either is
or isn't in the knowledge base for a given pair, and a dose either is or isn't in range for a
given renal function — there's no ambiguity for an LLM to usefully resolve, and keeping
these checks as code makes them exhaustively testable and impossible for a prompt to
"reason around." The LLM's job is synthesis (turning three structured finding lists into one
coherent report) and self-review, not clinical judgment from scratch.

## Pipeline diagram

```
Prescription Parser ──[injection?]──▶ blocked ──▶ Final Output
        │ continue
        ▼
Drug Normalizer
        │
        ▼
Patient Profile Loader
        │
        ▼
Interaction Retriever (RAG)
        │
        ▼
Allergy & Contraindication Checker
        │
        ▼
Dosage Validator
        │
        ▼
Risk Synthesizer ◀────────────┐
        │                      │ prepare_retry
        ▼                      │ (retry_count++, max 2)
Self-Critic ──[rejected & retries left]──┘
        │
   [approved, or retries exhausted]
        ▼
Final Output (pharmacist_review_flag, status=complete)
```
