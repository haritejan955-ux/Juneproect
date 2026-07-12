"""FastAPI dependency providers.

Everything here reads from `request.app.state`, which is populated once
during the lifespan startup in `app.main` — routers depend on these
functions, never on concrete singletons, so tests can override any of them
with `app.dependency_overrides[...]`.
"""

from collections.abc import Iterator

from fastapi import Request

from app.memory.repository import ClaimRepository
from app.services.claim_service import ClaimService
from app.services.dispute_service import DisputeService
from app.services.streaming import StreamPublisher


def get_claim_service(request: Request) -> ClaimService:
    return request.app.state.claim_service


def get_dispute_service(request: Request) -> DisputeService:
    return request.app.state.dispute_service


def get_stream_publisher(request: Request) -> StreamPublisher:
    return request.app.state.stream_publisher


def get_claim_repository(request: Request) -> Iterator[ClaimRepository]:
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield ClaimRepository(session)
