from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_audit(
    db: AsyncSession,
    action: str,
    details: dict | None = None,
    user_id: UUID | None = None,
    device_id: UUID | None = None,
    ip: str | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        device_id=device_id,
        action=action,
        details=details or {},
        ip=ip,
    )
    db.add(log)
