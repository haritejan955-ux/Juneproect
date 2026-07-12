from datetime import datetime

from pydantic import BaseModel


class AuditLogEntryResponse(BaseModel):
    agent: str
    action: str
    details: dict
    timestamp: datetime


class AuditTrailResponse(BaseModel):
    claim_id: str
    entries: list[AuditLogEntryResponse]
