import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    MfaEnableRequest,
    MfaSetupResponse,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.totp_enabled:
        if not body.totp_code or not user.totp_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="TOTP required")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(body.totp_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP")

    access = create_access_token(str(user.id), {"role": user.role.value})
    refresh = create_refresh_token(str(user.id))
    from datetime import datetime, timezone

    refresh_payload = decode_token(refresh)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
        )
    )
    await write_audit(db, "auth.login", user_id=user.id, ip=request.client.host if request.client else None)
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False))
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stored.revoked = True
    user_id = str(stored.user_id)
    access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    new_payload = decode_token(new_refresh)
    db.add(
        RefreshToken(
            user_id=stored.user_id,
            token_hash=hash_token(new_refresh),
            expires_at=datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc),
        )
    )
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        totp_enabled=user.totp_enabled,
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def mfa_setup(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MfaSetupResponse:
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.totp_enabled = False
    await db.commit()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="ARDM")
    return MfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/mfa/enable")
async def mfa_enable(
    body: MfaEnableRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Run MFA setup first")
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP")
    user.totp_enabled = True
    await db.commit()
    return {"enabled": True}
