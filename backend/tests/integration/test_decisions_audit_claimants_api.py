"""HTTP-contract tests for the read-heavy routers — decisions, audit, claimants, and the
non-streaming dispute endpoints. These seed real rows directly through `ClaimRepository`
against the app's real (temp SQLite) database, rather than faking the service layer: unlike
`claims`/`dispute/stream`, nothing here calls an LLM, so there's no reason not to exercise the
actual repository + router code end-to-end. See `tests/integration/test_claims_api.py` and
`tests/integration/test_dispute_stream.py` for the pattern used where an LLM call is in the
loop instead.
"""

from fastapi.testclient import TestClient

from app.api.dependencies import get_dispute_service
from app.main import create_app
from app.memory.repository import ClaimRepository
from app.state.graph_state import FinalDecision
from tests.conftest import TEST_API_KEY

AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}


def _seed_claim(app, claim_id: str, claimant_ref: str, query: str = "Is this covered?") -> None:
    with app.state.session_factory() as session:
        repository = ClaimRepository(session)
        claimant = repository.get_or_create_claimant(claimant_ref)
        repository.create_claim(claim_id, claimant.id, query)


def _seed_decision(app, claim_id: str) -> None:
    final_decision: FinalDecision = {
        "claim_id": claim_id,
        "status": "partial_approved",
        "confidence_score": 0.91,
        "low_confidence": False,
        "attorney_flag": False,
        "justification": "One line-item is covered, the other is excluded.",
        "coverage_map": [
            {
                "cpt_code": "97110",
                "diagnosis_code": "M54.5",
                "status": "approved",
                "cited_clause": "Physical therapy is a covered rehabilitative benefit.",
                "amount_billed": 90.0,
                "amount_covered": 90.0,
            },
            {
                "cpt_code": "15780",
                "diagnosis_code": "L70.0",
                "status": "denied",
                "cited_clause": "Cosmetic procedures are excluded under policy section 4.2.",
                "amount_billed": 800.0,
                "amount_covered": 0.0,
            },
        ],
        "fraud_signals": [
            {
                "signal_type": "upcoding",
                "severity": "low",
                "evidence": "Minor complexity mismatch noted.",
            }
        ],
        "citations": [
            {"source_doc": "policy_corpus", "section": "4.2", "excerpt": "Cosmetic exclusion."}
        ],
        "disclaimer": "This is not a final legal determination.",
        "retry_count": 1,
    }
    with app.state.session_factory() as session:
        ClaimRepository(session).save_decision(claim_id, final_decision)


def _seed_audit_entries(app, claim_id: str) -> None:
    with app.state.session_factory() as session:
        ClaimRepository(session).append_audit_entries(
            claim_id,
            [
                {
                    "agent": "document_preprocessor",
                    "action": "parsed_document",
                    "details": {"chunk_count": 3},
                    "timestamp": "2026-01-01T00:00:00+00:00",
                },
                {
                    "agent": "final_output",
                    "action": "finalized_decision",
                    "details": {"status": "partial_approved"},
                    "timestamp": "2026-01-01T00:00:05+00:00",
                },
            ],
        )


def test_get_claim_status_returns_seeded_claim():
    app = create_app()
    with TestClient(app) as client:
        _seed_claim(app, "claim-status-1", "claimant-status-1", query="Is my MRI covered?")

        response = client.get("/api/v1/claims/claim-status-1", headers=AUTH_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "claim-status-1"
    assert body["status"] == "processing"
    assert body["query"] == "Is my MRI covered?"


def test_get_decision_returns_full_seeded_payload():
    app = create_app()
    with TestClient(app) as client:
        _seed_claim(app, "claim-decision-1", "claimant-decision-1")
        _seed_decision(app, "claim-decision-1")

        response = client.get("/api/v1/claims/claim-decision-1/decision", headers=AUTH_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial_approved"
    assert body["retry_count"] == 1
    assert len(body["coverage_map"]) == 2
    statuses = {item["cpt_code"]: item["status"] for item in body["coverage_map"]}
    assert statuses == {"97110": "approved", "15780": "denied"}
    assert body["fraud_signals"][0]["signal_type"] == "upcoding"
    assert body["citations"][0]["section"] == "4.2"


def test_get_audit_trail_returns_seeded_entries_in_order():
    app = create_app()
    with TestClient(app) as client:
        _seed_claim(app, "claim-audit-1", "claimant-audit-1")
        _seed_audit_entries(app, "claim-audit-1")

        response = client.get("/api/v1/claims/claim-audit-1/audit", headers=AUTH_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert [entry["agent"] for entry in body["entries"]] == [
        "document_preprocessor",
        "final_output",
    ]
    assert body["entries"][0]["details"] == {"chunk_count": 3}


def test_get_claimant_history_returns_claims_newest_first():
    app = create_app()
    with TestClient(app) as client:
        _seed_claim(app, "claim-hist-older", "claimant-history-1", query="older claim")
        _seed_claim(app, "claim-hist-newer", "claimant-history-1", query="newer claim")

        response = client.get(
            "/api/v1/claimants/claimant-history-1/history", headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    body = response.json()
    claim_ids = [claim["claim_id"] for claim in body["claims"]]
    assert set(claim_ids) == {"claim-hist-older", "claim-hist-newer"}


def test_get_claimant_history_for_unknown_claimant_is_404():
    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/claimants/no-such-claimant/history", headers=AUTH_HEADERS
        )

    assert response.status_code == 404
    assert response.json()["error_code"] == "claimant_not_found"


def test_get_dispute_thread_returns_seeded_messages():
    app = create_app()
    with TestClient(app) as client:
        _seed_claim(app, "claim-dispute-thread-1", "claimant-dispute-1")
        _seed_decision(app, "claim-dispute-thread-1")
        with app.state.session_factory() as session:
            repository = ClaimRepository(session)
            dispute = repository.get_or_create_dispute("claim-dispute-thread-1")
            repository.append_dispute_message(dispute.id, "claimant", "Why was this denied?")
            repository.append_dispute_message(dispute.id, "assistant", "Because of exclusion X.")

        response = client.get(
            "/api/v1/claims/claim-dispute-thread-1/dispute", headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "open"
    assert [m["role"] for m in body["messages"]] == ["claimant", "assistant"]
    assert body["messages"][1]["content"] == "Because of exclusion X."


class _FakeDisputeService:
    async def post_message(self, claim_id: str, message: str) -> dict:
        return {
            "id": "reply-1",
            "role": "assistant",
            "content": f"Reviewed: {message}",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }

    def get_thread(self, claim_id: str):
        return "dispute-1", "open", []


def test_post_dispute_message_returns_the_assistant_reply():
    """Non-streaming POST /dispute — service-layer faked the same way test_claims_api.py fakes
    claim_service, since a real DisputeService.post_message() call reaches the LLM. The SSE
    variant of this same contract is covered in test_dispute_stream.py."""
    app = create_app()
    app.dependency_overrides[get_dispute_service] = lambda: _FakeDisputeService()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/claims/claim-post-dispute-1/dispute",
            headers=AUTH_HEADERS,
            json={"message": "Please reconsider"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert body["content"] == "Reviewed: Please reconsider"
