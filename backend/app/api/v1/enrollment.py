from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import get_settings
from app.core.limiter import limiter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.security import (
    derive_device_command_key,
    generate_device_token,
    generate_enrollment_code,
    generate_sms_secret,
    hash_token,
)
from app.db.session import get_db
from app.models.device import Device, DeviceMode, DeviceStatus
from app.models.enrollment import EnrollmentCode
from app.models.user import User
from app.schemas.device import DeviceRegisterRequest, DeviceRegisterResponse
from app.schemas.enrollment import EnrollmentCodeCreate, EnrollmentCodeOut
from app.services.audit import write_audit
from app.services.capabilities import default_capabilities

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/codes", response_model=EnrollmentCodeOut)
async def create_enrollment_code(
    body: EnrollmentCodeCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentCodeOut:
    settings = get_settings()
    ttl = body.ttl_minutes or settings.enrollment_code_ttl_minutes
    code = generate_enrollment_code()
    row = EnrollmentCode(
        code_hash=hash_token(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl),
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return EnrollmentCodeOut(id=str(row.id), code=code, expires_at=row.expires_at)


@router.post("/register", response_model=DeviceRegisterResponse)
@limiter.limit("30/minute")
async def register_device(
    body: DeviceRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DeviceRegisterResponse:
    result = await db.execute(
        select(EnrollmentCode).where(
            EnrollmentCode.code_hash == hash_token(body.enrollment_code),
            EnrollmentCode.used_at.is_(None),
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment or enrollment.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired enrollment code")

    device_token = generate_device_token()
    sms_secret = generate_sms_secret()
    mode = DeviceMode.managed if body.mode == "managed" else DeviceMode.standard
    caps = default_capabilities(mode)
    if body.capabilities:
        caps.update(body.capabilities)

    device = Device(
        name=body.name,
        model=body.model,
        manufacturer=body.manufacturer,
        android_version=body.android_version,
        mode=mode,
        capabilities=caps,
        status=DeviceStatus.pending_approval,
        public_key=body.public_key,
        device_secret_hash=hash_token(device_token),
        sms_secret_hash=hash_token(sms_secret),
    )
    db.add(device)
    await db.flush()

    enrollment.used_at = datetime.now(timezone.utc)
    enrollment.device_id = device.id
    await write_audit(
        db,
        "device.enrolled",
        {"device_id": str(device.id)},
        device_id=device.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return DeviceRegisterResponse(
        device_id=str(device.id),
        device_token=device_token,
        sms_secret=sms_secret,
        command_verification_key=derive_device_command_key(device.id),
        status=device.status.value,
    )
