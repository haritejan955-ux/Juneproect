"""Dispute flow — multi-turn conversation contesting a finalized decision.

Deliberately not a re-entry into the 9-node claim graph: the spec requires
"no re-processing the original documents," and a strictly linear
load-context -> respond flow has no conditional routing or retry logic, so
wrapping it in a second LangGraph StateGraph would add machinery this flow
doesn't need. See docs/memory-architecture.md section 3.
"""

from langchain_core.language_models import BaseChatModel
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import ClaimNotFoundError
from app.memory.repository import ClaimRepository
from app.prompts.dispute_responder_prompt import build_dispute_responder_prompt
from app.vectorstore.base import VectorStore


class DisputeService:
    def __init__(
        self,
        chat_model: BaseChatModel,
        session_factory: sessionmaker[Session],
        policy_corpus_store: VectorStore,
        rag_top_k: int,
        rag_similarity_threshold: float,
    ) -> None:
        self._chat_model = chat_model
        self._session_factory = session_factory
        self._policy_corpus_store = policy_corpus_store
        self._rag_top_k = rag_top_k
        self._rag_similarity_threshold = rag_similarity_threshold

    async def post_message(self, claim_id: str, message: str) -> dict:
        with self._session_factory() as session:
            repository = ClaimRepository(session)

            decision = repository.get_decision(claim_id)
            if decision is None:
                raise ClaimNotFoundError(
                    f"No finalized decision exists for claim {claim_id}", claim_id=claim_id
                )

            dispute = repository.get_or_create_dispute(claim_id)
            history = repository.get_dispute_messages(dispute.id)
            repository.append_dispute_message(dispute.id, "claimant", message)

            additional_chunks = [
                {"text": chunk["text"], "source": chunk["source"], "score": chunk["score"]}
                for chunk in self._policy_corpus_store.search(
                    message, self._rag_top_k, self._rag_similarity_threshold, "policy_corpus"
                )
            ]
            original_citations = [
                {"source_doc": c.source_doc, "section": c.section, "excerpt": c.excerpt}
                for c in repository.get_citations(decision.id)
            ]

            prompt = build_dispute_responder_prompt(
                original_decision={
                    "status": decision.decision,
                    "justification": decision.justification,
                },
                original_citations=original_citations,
                additional_chunks=additional_chunks,
                dispute_history=[{"role": m.role, "content": m.content} for m in history],
                new_message=message,
            )

            response = await self._chat_model.ainvoke(prompt)
            reply_text = (
                response.content if isinstance(response.content, str) else str(response.content)
            )

            assistant_message = repository.append_dispute_message(
                dispute.id, "assistant", reply_text
            )
            repository.append_audit_entries(
                claim_id,
                [
                    {
                        "agent": "dispute_responder",
                        "action": "answered_dispute_message",
                        "details": {"dispute_id": dispute.id},
                        "timestamp": assistant_message.timestamp.isoformat(),
                    }
                ],
            )

            return {
                "id": assistant_message.id,
                "role": "assistant",
                "content": reply_text,
                "timestamp": assistant_message.timestamp,
            }

    def get_thread(self, claim_id: str) -> tuple[str, str, list[dict]]:
        with self._session_factory() as session:
            repository = ClaimRepository(session)
            dispute = repository.get_dispute(claim_id)
            messages = repository.get_dispute_messages(dispute.id)
            return (
                dispute.id,
                dispute.status,
                [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp,
                    }
                    for m in messages
                ],
            )
