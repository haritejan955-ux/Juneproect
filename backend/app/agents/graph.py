from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes import (
    allergy_checker,
    dosage_validator,
    drug_normalizer,
    final_output,
    interaction_retriever,
    patient_profile_loader,
    prescription_parser,
    risk_synthesizer,
    self_critic,
)
from app.agents.routing import prepare_retry, route_after_critic, route_after_parser
from app.state.graph_state import GraphState


def build_safety_graph() -> CompiledStateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("prescription_parser", prescription_parser.run)
    graph.add_node("drug_normalizer", drug_normalizer.run)
    graph.add_node("patient_profile_loader", patient_profile_loader.run)
    graph.add_node("interaction_retriever", interaction_retriever.run)
    graph.add_node("allergy_checker", allergy_checker.run)
    graph.add_node("dosage_validator", dosage_validator.run)
    graph.add_node("risk_synthesizer", risk_synthesizer.run)
    graph.add_node("self_critic", self_critic.run)
    graph.add_node("prepare_retry", prepare_retry)
    graph.add_node("final_output", final_output.run)

    graph.add_edge(START, "prescription_parser")
    graph.add_conditional_edges(
        "prescription_parser",
        route_after_parser,
        {"blocked": "final_output", "continue": "drug_normalizer"},
    )
    graph.add_edge("drug_normalizer", "patient_profile_loader")
    graph.add_edge("patient_profile_loader", "interaction_retriever")
    graph.add_edge("interaction_retriever", "allergy_checker")
    graph.add_edge("allergy_checker", "dosage_validator")
    graph.add_edge("dosage_validator", "risk_synthesizer")
    graph.add_edge("risk_synthesizer", "self_critic")
    graph.add_conditional_edges(
        "self_critic",
        route_after_critic,
        {"retry": "prepare_retry", "final_output": "final_output"},
    )
    graph.add_edge("prepare_retry", "risk_synthesizer")
    graph.add_edge("final_output", END)

    return graph.compile()


def initial_state(raw_prescription_text: str, patient_profile: dict) -> GraphState:
    return {
        "raw_prescription_text": raw_prescription_text,
        "patient_profile": patient_profile,
        "retry_count": 0,
        "audit_log": [],
    }
