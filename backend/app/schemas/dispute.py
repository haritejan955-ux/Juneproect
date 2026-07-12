from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["claimant", "assistant"]


class DisputeMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class DisputeMessageResponse(BaseModel):
    id: str
    role: Role
    content: str
    timestamp: datetime


class DisputeThreadResponse(BaseModel):
    dispute_id: str
    claim_id: str
    status: Literal["open", "resolved"]
    messages: list[DisputeMessageResponse]
