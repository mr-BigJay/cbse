from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    enrollment_code: str
    name: str = "Android Device"
    model: str | None = None
    manufacturer: str | None = None
    android_version: str | None = None
    mode: str = "standard"
    public_key: str | None = None
    capabilities: dict[str, Any] = Field(default_factory=dict)


class DeviceRegisterResponse(BaseModel):
    device_id: str
    device_token: str
    sms_secret: str
    command_verification_key: str
    status: str


class DeviceHeartbeatRequest(BaseModel):
    battery_level: int | None = None
    capabilities: dict[str, Any] | None = None
    fcm_token: str | None = None


class DeviceOut(BaseModel):
    id: str
    name: str
    model: str | None
    manufacturer: str | None
    android_version: str | None
    mode: str
    status: str
    capabilities: dict[str, Any]
    last_seen_at: datetime | None
    battery_level: int | None
    enrolled_at: datetime
    approved_at: datetime | None
    online: bool = False

    model_config = {"from_attributes": True}


class LocationReport(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None = None


class LocationOut(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class SmsSendersUpdate(BaseModel):
    phone_numbers: list[str]
