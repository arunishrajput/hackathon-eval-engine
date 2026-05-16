"""
Root conftest.py — in-memory SQLite test database.

SQLite does not support pgvector, JSONB, or PostgreSQL's UUID dialect type.
We patch those before any app models are imported so SQLAlchemy uses
SQLite-compatible equivalents throughout the test session.
"""

import uuid
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy import String, Text, types
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ---------------------------------------------------------------------------
# Patch PostgreSQL-specific dialect types BEFORE the app models are imported.
# ---------------------------------------------------------------------------

# 1. Replace sqlalchemy.dialects.postgresql.UUID with a plain String(36)
import sqlalchemy.dialects.postgresql as pg_dialect


class _SQLiteUUID(types.TypeDecorator):
    """Store UUIDs as varchar(36) in SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


class _SQLiteJSONB(types.TypeDecorator):
    """Store JSONB as plain Text in SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value


# Monkey-patch the dialect module so existing model files that do
# ``from sqlalchemy.dialects.postgresql import UUID, JSONB`` get our shims.
pg_dialect.UUID = _SQLiteUUID
pg_dialect.JSONB = _SQLiteJSONB

# 2. Stub out pgvector so ``from pgvector.sqlalchemy import Vector`` works
#    without the actual C extension (which requires PostgreSQL).
import sys
import types as builtin_types

_pgvector_mod = builtin_types.ModuleType("pgvector")
_pgvector_sqlalchemy_mod = builtin_types.ModuleType("pgvector.sqlalchemy")


class _StubVector(types.TypeDecorator):
    """Stub Vector type — stores as Text for SQLite tests."""
    impl = Text
    cache_ok = True

    def __init__(self, dim=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value


_pgvector_sqlalchemy_mod.Vector = _StubVector
_pgvector_mod.sqlalchemy = _pgvector_sqlalchemy_mod
sys.modules.setdefault("pgvector", _pgvector_mod)
sys.modules.setdefault("pgvector.sqlalchemy", _pgvector_sqlalchemy_mod)

# ---------------------------------------------------------------------------
# Now it's safe to import application code.
# ---------------------------------------------------------------------------
from app.main import app as fastapi_app  # noqa: E402
from app.database import get_db, Base  # noqa: E402
import app.models  # noqa: E402 — registers all ORM models onto Base.metadata

# Re-export under the conventional name used by the fixtures below.
app = fastapi_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Isolated in-memory SQLite session per test function."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client wired to the per-test SQLite session."""

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Shared helper fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin_user(client: AsyncClient):
    """Register an admin user and return (user_dict, access_token)."""
    # Register as participant first, then we'll promote in-DB if needed.
    # For simplicity, we directly insert via the DB in tests that need admin.
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "adminpass123",
            "full_name": "Test Admin",
        },
    )
    assert resp.status_code == 201
    user = resp.json()

    # Promote to admin role directly in the session.
    from sqlalchemy import select, update
    from app.models.user import User, UserRole

    # Grab the db session from the override
    async for session in app.dependency_overrides[get_db]():
        await session.execute(
            update(User)
            .where(User.email == "admin@test.com")
            .values(role=UserRole.admin)
        )
        await session.flush()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return user, token


@pytest_asyncio.fixture
async def participant_user(client: AsyncClient):
    """Register a participant user and return (user_dict, access_token)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "participant@test.com",
            "password": "partpass123",
            "full_name": "Test Participant",
        },
    )
    assert resp.status_code == 201
    user = resp.json()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "participant@test.com", "password": "partpass123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return user, token
