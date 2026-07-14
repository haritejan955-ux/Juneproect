from app.agents.nodes import dosage_validator


def test_flags_dose_above_adult_max():
    state = {
        "medications": [
            {"normalized_name": "Ibuprofen", "dose_value": 4000, "dose_unit": "mg", "recognized": True}
        ],
        "patient_profile": {"renal_function": "normal"},
    }
    result = dosage_validator.run(state)

    assert len(result["dosage_findings"]) == 1
    assert result["dosage_findings"][0]["severity"] == "major"
    assert "exceeds" in result["dosage_findings"][0]["description"]


def test_flags_renal_contraindication():
    state = {
        "medications": [
            {"normalized_name": "Metformin", "dose_value": 500, "dose_unit": "mg", "recognized": True}
        ],
        "patient_profile": {"renal_function": "severe"},
    }
    result = dosage_validator.run(state)

    severities = {f["severity"] for f in result["dosage_findings"]}
    assert "contraindicated" in severities


def test_no_findings_for_normal_dose_and_renal_function():
    state = {
        "medications": [
            {"normalized_name": "Acetaminophen", "dose_value": 500, "dose_unit": "mg", "recognized": True}
        ],
        "patient_profile": {"renal_function": "normal"},
    }
    result = dosage_validator.run(state)

    assert result["dosage_findings"] == []
