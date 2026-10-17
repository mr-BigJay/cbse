import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.device import Device


class CommandStatus(str, enum.Enum):
    pending = "pending"
    delivered = "delivered"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"
    expired = "expired"


class CommandType(str, enum.Enum):
    STATUS = "STATUS"
    LOCATE = "LOCATE"
    ALARM = "ALARM"
    LOCK = "LOCK"
    APP_LIST = "APP_LIST"
    SYNC_STATUS = "SYNC_STATUS"


class Command(Base):
    __tablename__ = "commands"
    __table_args__ = (UniqueConstraint("device_id", "idempotency_key", name="uq_device_idempotency"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"))
    type: Mapped[CommandType] = mapped_column(Enum(CommandType))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[CommandStatus] = mapped_column(Enum(CommandStatus), default=CommandStatus.pending)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    signature: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device"] = relationship(back_populates="commands")
