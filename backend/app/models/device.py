import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.command import Command


class DeviceMode(str, enum.Enum):
    standard = "standard"
    managed = "managed"


class DeviceStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    active = "active"
    revoked = "revoked"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), default="Android Device")
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    android_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mode: Mapped[DeviceMode] = mapped_column(Enum(DeviceMode), default=DeviceMode.standard)
    capabilities: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus), default=DeviceStatus.pending_approval
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_secret_hash: Mapped[str] = mapped_column(String(64))
    sms_secret_hash: Mapped[str] = mapped_column(String(64))
    authorized_sms_senders: Mapped[list] = mapped_column(JSONB, default=list)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    locations: Mapped[list["DeviceLocation"]] = relationship(back_populates="device")
    commands: Mapped[list["Command"]] = relationship(back_populates="device", lazy="selectin")


class DeviceLocation(Base):
    __tablename__ = "device_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    device: Mapped[Device] = relationship(back_populates="locations")
