from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import sign_command
from app.models.command import Command, CommandStatus, CommandType
from app.models.device import Device
from app.services.audit import write_audit
from app.services.capabilities import is_command_allowed


async def create_command(
    db: AsyncSession,
    device: Device,
    cmd_type: CommandType,
    payload: dict,
    created_by: UUID | None,
    idempotency_key: str | None = None,
) -> tuple[Command | None, str | None]:
    allowed, cap_state = is_command_allowed(device, cmd_type)
    if not allowed and cap_state == "unsupported":
        return None, f"Command {cmd_type.value} is unsupported for this device"

    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.command_default_ttl_seconds)

    if idempotency_key:
        existing = await db.execute(
            select(Command).where(
                Command.device_id == device.id,
                Command.idempotency_key == idempotency_key,
            )
        )
        found = existing.scalar_one_or_none()
        if found:
            return found, None

    cmd = Command(
        device_id=device.id,
        type=cmd_type,
        payload=payload,
        status=CommandStatus.pending,
        idempotency_key=idempotency_key,
        expires_at=expires_at,
        created_by=created_by,
        signature="",
    )
    db.add(cmd)
    await db.flush()
    cmd.signature = sign_command(cmd.id, device.id, cmd.type.value, cmd.expires_at)
    await write_audit(
        db,
        "command.created",
        {"command_id": str(cmd.id), "type": cmd.type.value},
        user_id=created_by,
        device_id=device.id,
    )
    return cmd, None


async def expire_stale_commands(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Command).where(
            Command.status == CommandStatus.pending,
            Command.expires_at < now,
        )
    )
    for cmd in result.scalars():
        cmd.status = CommandStatus.expired
