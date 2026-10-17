from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models.settings import AppSetting
from app.models.user import User
from pydantic import BaseModel


class SettingsOut(BaseModel):
    location_retention_days: int


class SettingsUpdate(BaseModel):
    location_retention_days: int | None = None


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings_api(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SettingsOut:
    result = await db.execute(select(AppSetting).where(AppSetting.key == "global"))
    row = result.scalar_one_or_none()
    if row and "location_retention_days" in row.value:
        return SettingsOut(location_retention_days=row.value["location_retention_days"])
    return SettingsOut(location_retention_days=get_settings().location_retention_days)


@router.put("", response_model=SettingsOut)
async def update_settings(
    body: SettingsUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SettingsOut:
    result = await db.execute(select(AppSetting).where(AppSetting.key == "global"))
    row = result.scalar_one_or_none()
    value = row.value if row else {}
    if body.location_retention_days is not None:
        value["location_retention_days"] = body.location_retention_days
    if row:
        row.value = value
    else:
        db.add(AppSetting(key="global", value=value))
    await db.commit()
    return SettingsOut(location_retention_days=value.get("location_retention_days", 30))
