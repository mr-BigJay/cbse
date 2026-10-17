import os
from collections.abc import AsyncGenerator

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://ardm:ardmtest@127.0.0.1:5432/ardm_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-integration-only-32chars")
os.environ.setdefault("COMMAND_HMAC_SECRET", "test-command-hmac-secret")
os.environ.setdefault("ADMIN_EMAIL", "integration@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "integration-pass")
os.environ.setdefault("TESTING", "1")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.session as db_session
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.user import User, UserRole


async def _reset_schema(engine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    db_session.engine = engine
    db_session.AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await _reset_schema(engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_admin(test_engine) -> tuple[str, str]:
    email = os.environ["ADMIN_EMAIL"]
    password = os.environ["ADMIN_PASSWORD"]
    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is None:
            session.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    role=UserRole.administrator,
                )
            )
            await session.commit()
    return email, password


@pytest_asyncio.fixture
async def client(test_engine, seeded_admin) -> AsyncGenerator[AsyncClient, None]:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    get_settings.cache_clear()
