"""Liveness (`/health`) and readiness (`/health/ready`) probes.

Split per standard k8s-style semantics rather than one endpoint: liveness
answers "is the process up," and must stay cheap and dependency-free so an
orchestrator restarting a genuinely-hung process isn't itself blocked on a
slow DB; readiness answers "can this instance actually serve traffic" and
is allowed to check its dependencies. Neither requires an API key — a
health-check caller (load balancer, orchestrator, `docker compose`
healthcheck) is infrastructure, not a client of the claims API, and
probes need to work before any operator has distributed API keys to them.
"""

import time

from fastapi import APIRouter, Request, Response
from sqlalchemy import text

from app.schemas.health import HealthResponse, ReadinessCheck, ReadinessResponse

router = APIRouter(tags=["health"])

_start_time = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(uptime_seconds=round(time.monotonic() - _start_time, 2))


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request, response: Response) -> ReadinessResponse:
    checks: dict[str, ReadinessCheck] = {}

    session_factory = request.app.state.session_factory
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = ReadinessCheck(status="ok")
    except Exception as exc:  # readiness reports failures, it never raises them
        checks["database"] = ReadinessCheck(status="error", detail=str(exc))

    for name, store in (
        ("policy_corpus_index", request.app.state.policy_corpus_store),
        ("historical_decisions_index", request.app.state.historical_decisions_store),
    ):
        try:
            checks[name] = ReadinessCheck(status="ok", detail=f"{store.document_count()} vectors")
        except Exception as exc:  # readiness reports failures, it never raises them
            checks[name] = ReadinessCheck(status="error", detail=str(exc))

    overall_ok = all(check.status == "ok" for check in checks.values())
    response.status_code = 200 if overall_ok else 503
    return ReadinessResponse(status="ok" if overall_ok else "degraded", checks=checks)
