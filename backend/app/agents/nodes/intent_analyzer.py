"""[2] Intent Analyzer — LLM structured-output classification.

Note: this node runs before Security Checker (node 4) in the spec's fixed
pipeline order, so its prompt treats document metadata as untrusted data by
construction (it only ever sees `document_metadata`, a small deterministic
summary produced by node 1 — never raw document text). See
docs/security-architecture.md section 2 for the full ordering discussion.
"""

from collections.abc import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.core.audit import audit_update
from app.prompts.intent_analyzer_prompt import build_intent_analyzer_prompt
from app.state.graph_state import GraphState, Intent

AGENT_NAME = "intent_analyzer"


class IntentClassification(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    claimant_id: str | None = None
    date_of_service: str | None = None
    procedure_codes: list[str] = Field(default_factory=list)
    diagnosis_codes: list[str] = Field(default_factory=list)


def build_intent_analyzer_node(
    chat_model: BaseChatModel,
) -> Callable[[GraphState], Awaitable[dict]]:
    classifier = chat_model.with_structured_output(IntentClassification)

    async def intent_analyzer(state: GraphState) -> dict:
        prompt = build_intent_analyzer_prompt(state["query"], state.get("document_metadata", {}))
        result = await classifier.ainvoke(prompt)
        assert isinstance(result, IntentClassification)

        entities = {
            key: value
            for key, value in {
                "claimant_id": result.claimant_id,
                "date_of_service": result.date_of_service,
                "procedure_codes": result.procedure_codes,
                "diagnosis_codes": result.diagnosis_codes,
            }.items()
            if value
        }

        return {
            "intent": result.intent,
            "intent_confidence": result.confidence,
            "extracted_entities": entities,
            **audit_update(
                AGENT_NAME,
                "classified_intent",
                {"intent": result.intent, "confidence": result.confidence},
            ),
        }

    return intent_analyzer
