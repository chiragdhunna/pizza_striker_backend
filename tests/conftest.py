"""Test configuration and fixtures."""

import os

# Set test environment variables before any app imports so that Settings
# loads without requiring a real .env file or actual credentials.
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing_only")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.main import app
from app.database import Base, get_db
from app.config import get_settings


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    # Use SQLite for testing (in-memory)
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(db_session):
    """Create test client with mocked database."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()
