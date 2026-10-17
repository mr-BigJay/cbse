from datetime import datetime

from pydantic import BaseModel


class EnrollmentCodeCreate(BaseModel):
    ttl_minutes: int | None = None


class EnrollmentCodeOut(BaseModel):
    id: str
    code: str
    expires_at: datetime
