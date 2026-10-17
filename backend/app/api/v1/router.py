from fastapi import APIRouter

from app.api.v1 import audit, auth, commands, devices, enrollment, settings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(enrollment.router)
api_router.include_router(devices.router)
api_router.include_router(commands.router)
api_router.include_router(audit.router)
api_router.include_router(settings.router)
