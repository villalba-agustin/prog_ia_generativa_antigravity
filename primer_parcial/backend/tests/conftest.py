import asyncio
import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_headers(db_session: AsyncSession) -> dict:
    from sqlalchemy import select
    from app.models.user import User
    query = await db_session.execute(select(User).where(User.role == "ADMINISTRADOR").limit(1))
    admin = query.scalar_one()
    token = create_access_token(
        subject=str(admin.id),
        role="ADMINISTRADOR"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_delegate_headers(db_session: AsyncSession):
    async def _make(team_id: uuid.UUID) -> dict:
        from sqlalchemy import select
        from app.models.user import User
        query = await db_session.execute(
            select(User).where(User.role == "DELEGADO", User.team_id == team_id).limit(1)
        )
        delegate = query.scalar_one()
        token = create_access_token(
            subject=str(delegate.id),
            role="DELEGADO",
            team_id=str(team_id)
        )
        return {"Authorization": f"Bearer {token}"}
    return _make
