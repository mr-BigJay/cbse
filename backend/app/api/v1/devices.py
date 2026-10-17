from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_device, require_admin
from app.core.security import derive_device_command_key, generate_device_token, hash_token
from app.db.session import get_db
from app.models.device import Device, DeviceLocation, DeviceStatus
from app.models.user import User
from app.schemas.device import (
    DeviceHeartbeatRequest,
    DeviceOut,
    DeviceRegisterResponse,
    LocationOut,
    LocationReport,
    SmsSendersUpdate,
)
from app.services.audit import write_audit
from app.services.capabilities import merge_capabilities

router = APIRouter(prefix="/devices", tags=["devices"])

ONLINE_THRESHOLD = timedelta(minutes=15)


def device_to_out(device: Device) -> DeviceOut:
    online = False
    if device.last_seen_at:
        online = datetime.now(timezone.utc) - device.last_seen_at < ONLINE_THRESHOLD
    return DeviceOut(
        id=str(device.id),
        name=device.name,
        model=device.model,
        manufacturer=device.manufacturer,
        android_version=device.android_version,
        mode=device.mode.value,
        status=device.status.value,
        capabilities=merge_capabilities(device),
        last_seen_at=device.last_seen_at,
        battery_level=device.battery_level,
        enrolled_at=device.enrolled_at,
        approved_at=device.approved_at,
        online=online,
    )


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[DeviceOut]:
    result = await db.execute(select(Device).order_by(Device.enrolled_at.desc()))
    return [device_to_out(d) for d in result.scalars()]


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_to_out(device)


@router.post("/{device_id}/approve", response_model=DeviceOut)
async def approve_device(
    device_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = DeviceStatus.active
    device.approved_at = datetime.now(timezone.utc)
    await write_audit(db, "device.approved", user_id=user.id, device_id=device.id)
    await db.commit()
    return device_to_out(device)


@router.post("/{device_id}/revoke", response_model=DeviceOut)
async def revoke_device(
    device_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = DeviceStatus.revoked
    await write_audit(db, "device.revoked", user_id=user.id, device_id=device.id)
    await db.commit()
    return device_to_out(device)


@router.post("/me/heartbeat")
async def heartbeat(
    body: DeviceHeartbeatRequest,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    device.last_seen_at = datetime.now(timezone.utc)
    if body.battery_level is not None:
        device.battery_level = body.battery_level
    if body.capabilities:
        device.capabilities.update(body.capabilities)
    if body.fcm_token:
        device.fcm_token = body.fcm_token
    await db.commit()
    return {"status": "ok"}


@router.post("/me/rotate-token", response_model=DeviceRegisterResponse)
async def rotate_token(
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> DeviceRegisterResponse:
    new_token = generate_device_token()
    device.device_secret_hash = hash_token(new_token)
    await db.commit()
    return DeviceRegisterResponse(
        device_id=str(device.id),
        device_token=new_token,
        sms_secret="",
        command_verification_key=derive_device_command_key(device.id),
        status=device.status.value,
    )


@router.post("/me/location")
async def report_location(
    body: LocationReport,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    loc = DeviceLocation(
        device_id=device.id,
        latitude=body.latitude,
        longitude=body.longitude,
        accuracy=body.accuracy,
    )
    db.add(loc)
    await db.commit()
    return {"status": "ok"}


@router.get("/{device_id}/locations", response_model=list[LocationOut])
async def device_locations(
    device_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[LocationOut]:
    result = await db.execute(
        select(DeviceLocation)
        .where(DeviceLocation.device_id == device_id)
        .order_by(DeviceLocation.recorded_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()
    return [
        LocationOut(
            latitude=r.latitude,
            longitude=r.longitude,
            accuracy=r.accuracy,
            recorded_at=r.recorded_at,
        )
        for r in rows
    ]


@router.put("/{device_id}/sms-senders")
async def update_sms_senders(
    device_id: UUID,
    body: SmsSendersUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[str]]:
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.authorized_sms_senders = body.phone_numbers
    await write_audit(
        db,
        "device.sms_senders_updated",
        {"count": len(body.phone_numbers)},
        user_id=user.id,
        device_id=device.id,
    )
    await db.commit()
    return {"phone_numbers": device.authorized_sms_senders}
