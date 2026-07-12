from typing import Literal

from pydantic import BaseModel

CheckStatus = Literal["ok", "error"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    uptime_seconds: float


class ReadinessCheck(BaseModel):
    status: CheckStatus
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, ReadinessCheck]
