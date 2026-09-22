import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

import src.models  # registers every mapper before create_all
from src.core.config import settings
from src.db.base import Base
from src.db.session import get_db
from src.main import app
from tests.factories import PermissionFactory, RoleFactory, UserFactory


def _test_database_url() -> Any:
    """Same server as DATABASE_URL, but a dedicated `<db>_test` database."""
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return make_url(override)

    url = make_url(settings.DATABASE_URL)
    return url.set(database=f"{url.database}_test")


async def _ensure_database(url: Any) -> None:
    admin_engine = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    """One engine per test run, with the schema built from the models."""
    url = _test_database_url()
    await _ensure_database(url)

    test_engine = create_async_engine(url, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """
    A session inside an outer transaction that is always rolled back.

    `join_transaction_mode="create_savepoint"` lets the application code call
    `commit()` for real while the outer transaction keeps every write out of
    the next test.
    """
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """HTTP client talking to the ASGI app, sharing the test's transaction."""

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def _bound_factories(db: AsyncSession) -> None:
    """Point every factory at the transaction this test runs in."""
    for factory_class in (PermissionFactory, RoleFactory, UserFactory):
        factory_class._meta.sqlalchemy_session = db


@pytest.fixture
def permission_factory(_bound_factories: None) -> type[PermissionFactory]:
    return PermissionFactory


@pytest.fixture
def role_factory(_bound_factories: None) -> type[RoleFactory]:
    return RoleFactory


@pytest.fixture
def user_factory(_bound_factories: None) -> type[UserFactory]:
    return UserFactory
