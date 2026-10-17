from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime


class AuditOut(BaseModel):
    id: str
    action: str
    details: dict
    user_id: str | None
    device_id: str | None
    ip: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut])
async def list_audit(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditOut]:
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
    return [
        AuditOut(
            id=str(r.id),
            action=r.action,
            details=r.details,
            user_id=str(r.user_id) if r.user_id else None,
            device_id=str(r.device_id) if r.device_id else None,
            ip=r.ip,
            created_at=r.created_at,
        )
        for r in result.scalars()
    ]
