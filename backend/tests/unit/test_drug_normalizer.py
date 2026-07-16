from app.agents.nodes import drug_normalizer


def test_normalizes_known_aliases():
    state = {
        "medications": [
            {"raw_name": "Coumadin", "dose_value": 5, "dose_unit": "mg"},
            {"raw_name": "Tylenol", "dose_value": 500, "dose_unit": "mg"},
        ]
    }
    result = drug_normalizer.run(state)

    names = {m["normalized_name"] for m in result["medications"]}
    assert names == {"Warfarin", "Acetaminophen"}
    assert result["unrecognized_drugs"] == []
    assert all(m["recognized"] for m in result["medications"])


def test_flags_unrecognized_drug():
    state = {"medications": [{"raw_name": "Zorbitrex9000", "dose_value": None, "dose_unit": None}]}
    result = drug_normalizer.run(state)

    assert result["unrecognized_drugs"] == ["Zorbitrex9000"]
    assert result["medications"][0]["recognized"] is False
