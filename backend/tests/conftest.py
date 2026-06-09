"""
FinSight AI — Test Configuration & Fixtures
Provides async test fixtures, test database, and factories.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from uuid6 import uuid7

from app.core.database import Base
from app.core.security import hash_password
from app.models.user import OAuthProvider, User, UserRole


# Use SQLite for fast tests (no PostgreSQL dependency)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and tear down test database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for tests."""
    async with TestSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a standard test user."""
    user = User(
        id=str(uuid7()),
        email="testuser@example.com",
        name="Test User",
        password_hash=hash_password("TestPass123"),
        role=UserRole.USER,
        oauth_provider=OAuthProvider.LOCAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        id=str(uuid7()),
        email="admin@example.com",
        name="Admin User",
        password_hash=hash_password("AdminPass123"),
        role=UserRole.ADMIN,
        oauth_provider=OAuthProvider.LOCAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession) -> User:
    """Create an analyst test user."""
    user = User(
        id=str(uuid7()),
        email="analyst@example.com",
        name="Analyst User",
        password_hash=hash_password("AnalystPass123"),
        role=UserRole.ANALYST,
        oauth_provider=OAuthProvider.LOCAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user
