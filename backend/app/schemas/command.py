from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CommandCreate(BaseModel):
    device_id: str
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandOut(BaseModel):
    id: str
    device_id: str
    type: str
    payload: dict[str, Any]
    status: str
    expires_at: datetime
    result: dict[str, Any] | None
    signature: str
    created_at: datetime
    delivered_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CommandEnvelope(BaseModel):
    command_id: str
    type: str
    payload: dict[str, Any]
    expires_at: datetime
    signature: str


class CommandAck(BaseModel):
    status: str = "delivered"


class CommandResult(BaseModel):
    status: str  # completed | failed | rejected
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
