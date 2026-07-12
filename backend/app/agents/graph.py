"""StateGraph assembly — the 9 agents wired with conditional routing.

`build_claim_graph` is a pure factory: every dependency (chat model,
embeddings, vector stores, checkpointer, thresholds) is passed in rather
than constructed here, which is what makes this graph swappable in tests
(inject a fake chat model, an in-memory vector store) without touching node
code. See docs/langgraph-workflow.md for the full diagram this mirrors.
"""

from functools import partial

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes.answer_synthesizer import build_answer_synthesizer_node
from app.agents.nodes.coverage_validator import build_coverage_validator_node
from app.agents.nodes.document_preprocessor import build_document_preprocessor_node
from app.agents.nodes.final_output import build_final_output_node
from app.agents.nodes.fraud_detector import build_fraud_detector_node
from app.agents.nodes.intent_analyzer import build_intent_analyzer_node
from app.agents.nodes.rag_retriever import build_rag_retriever_node
from app.agents.nodes.security_checker import build_security_checker_node
from app.agents.nodes.self_critic import build_self_critic_node
from app.agents.routing import (
    blocked_node,
    increment_retry_count,
    route_after_critic,
    route_after_security,
)
from app.security.injection_detector import InjectionDetector
from app.state.graph_state import GraphState
from app.vectorstore.base import VectorStore


def build_claim_graph(
    chat_model: BaseChatModel,
    embeddings: Embeddings,
    policy_corpus_store: VectorStore,
    historical_decisions_store: VectorStore,
    checkpointer: BaseCheckpointSaver,
    rag_top_k: int,
    rag_similarity_threshold: float,
    security_block_confidence: float,
    self_critic_score_threshold: float,
    self_critic_max_retries: int,
) -> CompiledStateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("document_preprocessor", build_document_preprocessor_node())
    graph.add_node("intent_analyzer", build_intent_analyzer_node(chat_model))
    graph.add_node(
        "rag_retriever",
        build_rag_retriever_node(
            policy_corpus_store,
            historical_decisions_store,
            embeddings,
            rag_top_k,
            rag_similarity_threshold,
        ),
    )
    graph.add_node(
        "security_checker",
        build_security_checker_node(InjectionDetector(chat_model, security_block_confidence)),
    )
    graph.add_node("coverage_validator", build_coverage_validator_node(chat_model))
    graph.add_node("fraud_detector", build_fraud_detector_node(chat_model))
    graph.add_node("answer_synthesizer", build_answer_synthesizer_node(chat_model))
    graph.add_node(
        "self_critic",
        build_self_critic_node(chat_model, self_critic_score_threshold, self_critic_max_retries),
    )
    graph.add_node("final_output", build_final_output_node())
    graph.add_node("blocked", blocked_node)
    graph.add_node("prepare_retry", increment_retry_count)

    graph.add_edge(START, "document_preprocessor")
    graph.add_edge("document_preprocessor", "intent_analyzer")
    graph.add_edge("intent_analyzer", "rag_retriever")
    graph.add_edge("rag_retriever", "security_checker")

    graph.add_conditional_edges(
        "security_checker",
        route_after_security,
        {"coverage_validator": "coverage_validator", "blocked": "blocked"},
    )
    graph.add_edge("blocked", END)

    graph.add_edge("coverage_validator", "fraud_detector")
    graph.add_edge("fraud_detector", "answer_synthesizer")
    graph.add_edge("answer_synthesizer", "self_critic")

    graph.add_conditional_edges(
        "self_critic",
        partial(
            route_after_critic,
            score_threshold=self_critic_score_threshold,
            max_retries=self_critic_max_retries,
        ),
        {"prepare_retry": "prepare_retry", "final_output": "final_output"},
    )
    graph.add_edge("prepare_retry", "answer_synthesizer")
    graph.add_edge("final_output", END)

    return graph.compile(checkpointer=checkpointer)
