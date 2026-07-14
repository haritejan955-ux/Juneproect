from app.agents.nodes import interaction_retriever as retriever_node


def test_finds_known_interaction(monkeypatch, interaction_retriever):
    monkeypatch.setattr(retriever_node, "get_interaction_retriever", lambda: interaction_retriever)

    state = {
        "medications": [
            {"normalized_name": "Warfarin", "recognized": True},
            {"normalized_name": "Aspirin", "recognized": True},
        ]
    }
    result = retriever_node.run(state)

    assert len(result["interaction_findings"]) == 1
    finding = result["interaction_findings"][0]
    assert finding["citation_doc_id"] == "warfarin_aspirin"
    assert finding["severity"] == "major"
    assert set(finding["drugs"]) == {"warfarin", "aspirin"}


def test_no_finding_for_unrelated_drugs(monkeypatch, interaction_retriever):
    monkeypatch.setattr(retriever_node, "get_interaction_retriever", lambda: interaction_retriever)
    state = {
        "medications": [
            {"normalized_name": "Acetaminophen", "recognized": True},
            {"normalized_name": "Amoxicillin", "recognized": True},
        ]
    }
    result = retriever_node.run(state)

    assert result["interaction_findings"] == []


def test_ignores_unrecognized_medications(monkeypatch, interaction_retriever):
    monkeypatch.setattr(retriever_node, "get_interaction_retriever", lambda: interaction_retriever)
    state = {"medications": [{"normalized_name": None, "recognized": False}]}
    result = retriever_node.run(state)

    assert result["interaction_findings"] == []
