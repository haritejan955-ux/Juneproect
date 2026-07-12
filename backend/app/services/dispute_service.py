"""Dispute flow — multi-turn conversation contesting a finalized decision.

Deliberately not a re-entry into the 9-node claim graph: the spec requires
"no re-processing the original documents," and a strictly linear
load-context -> respond flow has no conditional routing or retry logic, so
wrapping it in a second LangGraph StateGraph would add machinery this flow
doesn't need. See docs/memory-architecture.md section 3.
"""

from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import ClaimNotFoundError
from app.memory.checkpointer import thread_config
from app.memory.models import Dispute, DisputeMessageRecord
from app.memory.repository import ClaimRepository
from app.prompts.dispute_responder_prompt import build_dispute_responder_prompt
from app.state.graph_state import ConversationTurn
from app.vectorstore.base import VectorStore


class DisputeService:
    def __init__(
        self,
        chat_model: BaseChatModel,
        session_factory: sessionmaker[Session],
        policy_corpus_store: VectorStore,
        rag_top_k: int,
        rag_similarity_threshold: float,
        graph: CompiledStateGraph,
    ) -> None:
        self._chat_model = chat_model
        self._session_factory = session_factory
        self._policy_corpus_store = policy_corpus_store
        self._rag_top_k = rag_top_k
        self._rag_similarity_threshold = rag_similarity_threshold
        self._graph = graph
        """Not used to re-run the pipeline (see module docstring) — only to append this
        exchange to `GraphState.conversation_history` on the claim's existing checkpointed
        thread via `aupdate_state`, so the dispute thread is genuinely part of the claim's
        shared state, not only a SQL-only side record."""

    def _load_context(
        self, repository: ClaimRepository, claim_id: str, message: str
    ) -> tuple[Dispute, str]:
        """Validates the claim has a finalized decision, records the claimant's turn, and
        builds the prompt. Raises `ClaimNotFoundError` before anything is streamed back to
        the caller — shared by both `post_message` and `stream_message` so a bad `claim_id`
        fails identically for both."""
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
        return dispute, prompt

    async def _persist_reply(
        self,
        repository: ClaimRepository,
        dispute: Dispute,
        claim_id: str,
        message: str,
        reply_text: str,
    ) -> DisputeMessageRecord:
        assistant_message = repository.append_dispute_message(dispute.id, "assistant", reply_text)
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

        # SQL (dispute_messages, above) is the durable long-term record. This second write
        # appends the same two turns to conversation_history on the claim's *existing*
        # checkpointed thread — the claim was already run through the graph to reach a
        # decision, so this thread is guaranteed to exist; aupdate_state patches state
        # without executing any node, i.e. without re-processing the original documents.
        claimant_turn: ConversationTurn = {
            "role": "claimant",
            "content": message,
            "timestamp": assistant_message.timestamp.isoformat(),
        }
        assistant_turn: ConversationTurn = {
            "role": "assistant",
            "content": reply_text,
            "timestamp": assistant_message.timestamp.isoformat(),
        }
        await self._graph.aupdate_state(
            thread_config(claim_id),
            {"conversation_history": [claimant_turn, assistant_turn]},
        )
        return assistant_message

    async def post_message(self, claim_id: str, message: str) -> dict:
        with self._session_factory() as session:
            repository = ClaimRepository(session)
            dispute, prompt = self._load_context(repository, claim_id, message)

            response = await self._chat_model.ainvoke(prompt)
            reply_text = (
                response.content if isinstance(response.content, str) else str(response.content)
            )

            assistant_message = await self._persist_reply(
                repository, dispute, claim_id, message, reply_text
            )

            return {
                "id": assistant_message.id,
                "role": "assistant",
                "content": reply_text,
                "timestamp": assistant_message.timestamp,
            }

    async def stream_message(self, claim_id: str, message: str) -> AsyncIterator[dict]:
        """Token-by-token SSE source for the dispute chat. Unlike the claim pipeline's WS
        status stream (deliberately node-level, not token-level — see
        docs/api-architecture.md section 3), streaming raw model output here is safe: this
        runs after a decision is finalized, directly on the claimant's own message, with no
        unredacted claim-document content in play. Yields `{"event": ..., "data": ...}`
        dicts; the router formats these as SSE frames."""
        with self._session_factory() as session:
            repository = ClaimRepository(session)
            dispute, prompt = self._load_context(repository, claim_id, message)

            reply_chunks: list[str] = []
            async for chunk in self._chat_model.astream(prompt):
                piece = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                if not piece:
                    continue
                reply_chunks.append(piece)
                yield {"event": "token", "data": {"content": piece}}

            reply_text = "".join(reply_chunks)
            assistant_message = await self._persist_reply(
                repository, dispute, claim_id, message, reply_text
            )
            yield {
                "event": "done",
                "data": {
                    "id": assistant_message.id,
                    "timestamp": assistant_message.timestamp.isoformat(),
                },
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
