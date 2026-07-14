from app.agents.nodes import allergy_checker


def test_flags_penicillin_class_allergy():
    state = {
        "medications": [
            {"normalized_name": "Amoxicillin", "allergy_class": "penicillins", "recognized": True}
        ],
        "patient_profile": {"allergies": ["penicillin"], "conditions": []},
    }
    result = allergy_checker.run(state)

    assert len(result["allergy_findings"]) == 1
    finding = result["allergy_findings"][0]
    assert finding["severity"] == "contraindicated"
    assert finding["drug"] == "Amoxicillin"


def test_flags_condition_contraindication():
    state = {
        "medications": [
            {"normalized_name": "Metformin", "allergy_class": None, "recognized": True}
        ],
        "patient_profile": {"allergies": [], "conditions": ["severe renal impairment"]},
    }
    result = allergy_checker.run(state)

    assert len(result["allergy_findings"]) == 1
    assert result["allergy_findings"][0]["severity"] == "major"


def test_no_findings_when_no_conflicts():
    state = {
        "medications": [{"normalized_name": "Acetaminophen", "allergy_class": None, "recognized": True}],
        "patient_profile": {"allergies": ["shellfish"], "conditions": ["hypertension"]},
    }
    result = allergy_checker.run(state)

    assert result["allergy_findings"] == []


def test_skips_unrecognized_medications():
    state = {
        "medications": [{"normalized_name": None, "recognized": False}],
        "patient_profile": {"allergies": ["penicillin"], "conditions": []},
    }
    result = allergy_checker.run(state)

    assert result["allergy_findings"] == []
