"""Shared scaffolding for the full-pipeline scenario tests in this package.

Every test here runs the *actual* production graph (`build_claim_graph` —
the same function `app.main`'s lifespan wires up) against a real PDF
fixture from `test_scenarios/`, with only the chat model faked. That's a
deliberately higher bar than a node-level unit test: it proves the 9 nodes
are wired together correctly for a given claim shape, not just that each
node works in isolation.
"""

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from app.agents.graph import build_claim_graph
from app.agents.nodes.answer_synthesizer import _SynthesisResult
from app.agents.nodes.coverage_validator import _CoverageValidationResult
from app.agents.nodes.fraud_detector import _FraudDetectionResult
from app.agents.nodes.intent_analyzer import IntentClassification
from app.agents.nodes.self_critic import _CritiqueResult
from app.memory.checkpointer import build_checkpointer, thread_config
from app.security.injection_detector import InjectionClassification
from app.state.graph_state import GraphState, RawDocument
from app.vectorstore.hybrid_store import HybridVectorStore
from tests.fakes import FakeEmbeddings

SCENARIOS_DIR = Path(__file__).resolve().parents[3] / "test_scenarios"

NOT_AN_INJECTION = InjectionClassification(
    is_injection=False, confidence=0.0, reasoning="Routine claim narrative, no override attempt."
)


def raw_document(pdf_path: Path) -> RawDocument:
    return RawDocument(
        filename=pdf_path.name,
        storage_path=str(pdf_path),
        doc_type="cms_1500",
        content_type="application/pdf",
    )


def initial_state(claim_id: str, pdf_path: Path, query: str) -> GraphState:
    return {
        "claim_id": claim_id,
        "claimant_id": "claimant-1",
        "query": query,
        "claim_document": [raw_document(pdf_path)],
        "retry_count": 0,
        "audit_log": [],
        "conversation_history": [],
    }


def build_test_graph(chat_model: BaseChatModel) -> CompiledStateGraph:
    """`chat_model` is typed as the real `BaseChatModel` interface, not the concrete
    `MultiSchemaFakeChatModel` test double that's actually passed in — these fakes are
    deliberately duck-typed (see `tests/fakes.py`'s module docstring) rather than real
    LangChain subclasses, so they satisfy this by structure, not by inheritance."""
    embeddings = FakeEmbeddings()
    return build_claim_graph(
        chat_model=chat_model,
        embeddings=embeddings,
        policy_corpus_store=HybridVectorStore.ephemeral("policy_corpus", embeddings),
        historical_decisions_store=HybridVectorStore.ephemeral("historical_decisions", embeddings),
        checkpointer=build_checkpointer(),
        rag_top_k=5,
        rag_similarity_threshold=0.5,
        security_block_confidence=0.7,
        self_critic_score_threshold=0.8,
        self_critic_max_retries=2,
    )


async def run_scenario(claim_id: str, pdf_path: Path, query: str, chat_model) -> dict:
    graph = build_test_graph(chat_model)
    result = await graph.ainvoke(
        initial_state(claim_id, pdf_path, query),
        config=thread_config(claim_id),
    )
    return result


def schema_placeholders(overrides: dict[type, object]) -> dict[type, object]:
    """Every node's `with_structured_output(Schema)` runs once at *graph construction* time
    (see `test_malicious_pdf_injection.py`'s docstring for why), so `MultiSchemaFakeChatModel`
    needs a configured entry for every schema in the graph even when a given scenario only
    exercises some of them. This bundles reasonable defaults for the ones a scenario test
    isn't scripting on purpose, so each test only has to spell out what it actually cares
    about via `overrides` — keyed by the actual schema class, e.g.
    `schema_placeholders({IntentClassification: IntentClassification(...)})`."""
    defaults: dict[type, object] = {
        IntentClassification: IntentClassification(intent="coverage_check", confidence=0.9),
        InjectionClassification: NOT_AN_INJECTION,
        _CoverageValidationResult: _CoverageValidationResult(line_items=[]),
        _FraudDetectionResult: _FraudDetectionResult(signals=[]),
        _SynthesisResult: _SynthesisResult(decision="denied", justification="unused placeholder"),
        _CritiqueResult: _CritiqueResult(
            legal_accuracy=1.0, completeness=1.0, hallucination_risk=1.0, critique=""
        ),
    }
    defaults.update(overrides)
    return defaults
