from app.agents.nodes import final_output


def test_flags_pharmacist_review_on_major_severity():
    state = {"report": {"overall_severity": "major"}, "interaction_findings": [], "allergy_findings": [], "dosage_findings": []}
    result = final_output.run(state)

    assert result["pharmacist_review_flag"] is True
    assert result["status"] == "complete"


def test_flags_pharmacist_review_on_individual_high_severity_finding():
    state = {
        "report": {"overall_severity": "minor"},
        "interaction_findings": [{"severity": "contraindicated"}],
        "allergy_findings": [],
        "dosage_findings": [],
    }
    result = final_output.run(state)

    assert result["pharmacist_review_flag"] is True


def test_no_flag_when_all_findings_low_severity():
    state = {
        "report": {"overall_severity": "minor"},
        "interaction_findings": [],
        "allergy_findings": [],
        "dosage_findings": [{"severity": "minor"}],
    }
    result = final_output.run(state)

    assert result["pharmacist_review_flag"] is False


def test_blocked_status_short_circuits():
    state = {"status": "blocked", "injection_reason": "matched heuristic pattern"}
    result = final_output.run(state)

    assert "pharmacist_review_flag" not in result
    assert result["audit_log"][0]["action"] == "terminated_blocked"
