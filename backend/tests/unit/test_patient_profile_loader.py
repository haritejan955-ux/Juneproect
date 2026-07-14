from app.agents.nodes import patient_profile_loader


def test_fills_in_defaults_for_missing_fields():
    result = patient_profile_loader.run({"patient_profile": {}})
    profile = result["patient_profile"]

    assert profile["renal_function"] == "normal"
    assert profile["hepatic_function"] == "normal"
    assert profile["allergies"] == []
    assert profile["conditions"] == []


def test_preserves_provided_fields():
    raw = {
        "age": 72,
        "allergies": ["penicillin"],
        "conditions": ["chronic kidney disease"],
        "renal_function": "severe",
    }
    result = patient_profile_loader.run({"patient_profile": raw})
    profile = result["patient_profile"]

    assert profile["age"] == 72
    assert profile["allergies"] == ["penicillin"]
    assert profile["renal_function"] == "severe"
