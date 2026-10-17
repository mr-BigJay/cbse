import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter
from sqlalchemy import delete, select

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.device import DeviceLocation
from app.models.settings import AppSetting
from app.models.user import User, UserRole


async def ensure_admin_user() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.admin_email))
        if not result.scalar_one_or_none():
            db.add(
                User(
                    email=settings.admin_email,
                    password_hash=hash_password(settings.admin_password),
                    role=UserRole.administrator,
                )
            )
            await db.commit()


async def purge_old_locations() -> None:
    while True:
        await asyncio.sleep(86400)
        settings = get_settings()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AppSetting).where(AppSetting.key == "global"))
            row = result.scalar_one_or_none()
            days = settings.location_retention_days
            if row and row.value.get("location_retention_days"):
                days = int(row.value["location_retention_days"])
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            await db.execute(delete(DeviceLocation).where(DeviceLocation.recorded_at < cutoff))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_admin_user()
    task = None
    if os.getenv("TESTING") != "1":
        task = asyncio.create_task(purge_old_locations())
    yield
    if task is not None:
        task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Android Remote Device Manager API", version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
