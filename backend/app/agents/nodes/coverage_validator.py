"""[5] Coverage Validator — maps line-items to policy coverage, always
citing a specific clause. See docs/agent-architecture.md."""

from collections.abc import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.core.audit import audit_update
from app.core.llm_call import invoke_structured
from app.core.logging import get_logger
from app.prompts.coverage_validator_prompt import build_coverage_validator_prompt
from app.state.graph_state import Citation, CoverageLineItem, GraphState

AGENT_NAME = "coverage_validator"

logger = get_logger(__name__)


class _LineItemResult(BaseModel):
    cpt_code: str
    diagnosis_code: str
    status: str = Field(description="'approved' or 'denied'")
    cited_clause: str = Field(min_length=1)
    amount_billed: float | None = None
    amount_covered: float | None = None


class _CoverageValidationResult(BaseModel):
    line_items: list[_LineItemResult]


def build_coverage_validator_node(
    chat_model: BaseChatModel,
) -> Callable[[GraphState], Awaitable[dict]]:
    validator = chat_model.with_structured_output(_CoverageValidationResult)

    async def coverage_validator(state: GraphState) -> dict:
        claim_id = state["claim_id"]
        logger.info(f"{AGENT_NAME}.started", extra={"claim_id": claim_id})

        entities = state.get("extracted_entities", {})
        procedure_codes = entities.get("procedure_codes", [])
        diagnosis_codes = entities.get("diagnosis_codes", [])

        line_items_input = (
            [{"cpt_code": code, "diagnosis_codes": diagnosis_codes} for code in procedure_codes]
            if procedure_codes
            else [{"note": "no procedure codes extracted; evaluate claim-level coverage"}]
        )

        redacted_chunks = state.get("redacted_chunks") or state.get("retrieved_chunks", [])

        result = await invoke_structured(
            validator,
            build_coverage_validator_prompt(line_items_input, list(redacted_chunks)),
            agent_name=AGENT_NAME,
            claim_id=claim_id,
            expected_type=_CoverageValidationResult,
        )

        coverage_map: list[CoverageLineItem] = [
            CoverageLineItem(
                cpt_code=item.cpt_code,
                diagnosis_code=item.diagnosis_code,
                status="approved" if item.status == "approved" else "denied",
                cited_clause=item.cited_clause,
                amount_billed=item.amount_billed,
                amount_covered=item.amount_covered,
            )
            for item in result.line_items
        ]

        citations: list[Citation] = [
            Citation(source_doc="policy_corpus", section=None, excerpt=item.cited_clause)
            for item in result.line_items
        ]

        logger.info(
            f"{AGENT_NAME}.completed",
            extra={"claim_id": claim_id, "line_item_count": len(coverage_map)},
        )

        return {
            "coverage": coverage_map,
            "citations": citations,
            **audit_update(
                AGENT_NAME, "validated_coverage", {"line_item_count": len(coverage_map)}
            ),
        }

    return coverage_validator
