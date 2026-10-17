from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_device, require_admin
from app.core.security import verify_command_signature
from app.db.session import get_db
from app.models.command import Command, CommandStatus, CommandType
from app.models.device import Device, DeviceStatus
from app.models.user import User
from app.schemas.command import CommandAck, CommandCreate, CommandEnvelope, CommandOut, CommandResult
from app.services.audit import write_audit
from app.services.commands import create_command, expire_stale_commands

router = APIRouter(prefix="/commands", tags=["commands"])


def command_to_out(cmd: Command) -> CommandOut:
    return CommandOut(
        id=str(cmd.id),
        device_id=str(cmd.device_id),
        type=cmd.type.value,
        payload=cmd.payload or {},
        status=cmd.status.value,
        expires_at=cmd.expires_at,
        result=cmd.result,
        signature=cmd.signature,
        created_at=cmd.created_at,
        delivered_at=cmd.delivered_at,
        completed_at=cmd.completed_at,
    )


@router.post("", response_model=CommandOut)
async def create_device_command(
    body: CommandCreate,
    request: Request,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> CommandOut:
    try:
        device_id = UUID(body.device_id)
        cmd_type = CommandType(body.type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid device_id or command type") from exc

    device = await db.get(Device, device_id)
    if not device or device.status != DeviceStatus.active:
        raise HTTPException(status_code=400, detail="Device not active")

    cmd, err = await create_command(
        db, device, cmd_type, body.payload, user.id, idempotency_key=idempotency_key
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    assert cmd is not None
    await write_audit(
        db,
        "command.requested",
        {"type": cmd.type.value},
        user_id=user.id,
        device_id=device.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(cmd)
    return command_to_out(cmd)


@router.get("", response_model=list[CommandOut])
async def list_commands(
    device_id: UUID | None = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[CommandOut]:
    q = select(Command).order_by(Command.created_at.desc()).limit(100)
    if device_id:
        q = q.where(Command.device_id == device_id)
    result = await db.execute(q)
    return [command_to_out(c) for c in result.scalars()]


@router.get("/pending", response_model=list[CommandEnvelope])
async def pending_commands(
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> list[CommandEnvelope]:
    await expire_stale_commands(db)
    if device.status != DeviceStatus.active:
        return []
    result = await db.execute(
        select(Command).where(
            Command.device_id == device.id,
            Command.status == CommandStatus.pending,
            Command.expires_at >= datetime.now(timezone.utc),
        )
    )
    envelopes = []
    for cmd in result.scalars():
        if not verify_command_signature(cmd.id, device.id, cmd.type.value, cmd.expires_at, cmd.signature):
            continue
        envelopes.append(
            CommandEnvelope(
                command_id=str(cmd.id),
                type=cmd.type.value,
                payload=cmd.payload or {},
                expires_at=cmd.expires_at,
                signature=cmd.signature,
            )
        )
    await db.commit()
    return envelopes


@router.post("/{command_id}/ack", response_model=CommandOut)
async def ack_command(
    command_id: UUID,
    body: CommandAck,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> CommandOut:
    cmd = await db.get(Command, command_id)
    if not cmd or cmd.device_id != device.id:
        raise HTTPException(status_code=404, detail="Command not found")
    if cmd.status != CommandStatus.pending:
        return command_to_out(cmd)
    cmd.status = CommandStatus.delivered
    cmd.delivered_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cmd)
    return command_to_out(cmd)


@router.post("/{command_id}/result", response_model=CommandOut)
async def command_result(
    command_id: UUID,
    body: CommandResult,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> CommandOut:
    cmd = await db.get(Command, command_id)
    if not cmd or cmd.device_id != device.id:
        raise HTTPException(status_code=404, detail="Command not found")
    try:
        cmd.status = CommandStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc
    cmd.result = body.result
    if body.error:
        cmd.result = {**(cmd.result or {}), "error": body.error}
    cmd.completed_at = datetime.now(timezone.utc)
    await write_audit(db, "command.completed", {"command_id": str(cmd.id), "status": cmd.status.value})
    await db.commit()
    await db.refresh(cmd)
    return command_to_out(cmd)
