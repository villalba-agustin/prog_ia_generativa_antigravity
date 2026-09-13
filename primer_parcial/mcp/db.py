"""
Database connection management for Liga de Barrios y Fincas MCP Server.
Connects asynchronously to PostgreSQL using SQLAlchemy Core and asyncpg.
Loads environment variables from .env if present.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection

# Search for .env in current directory and parent directories
env_paths = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/liga_barrios"

# Ensure asyncpg dialect is used for async engine
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Masked URL for logging / debugging without leaking password
def get_safe_db_info() -> dict:
    masked = DATABASE_URL
    if "@" in masked and ":" in masked:
        try:
            proto, rest = masked.split("://", 1)
            user_pass, host_db = rest.split("@", 1)
            user = user_pass.split(":")[0]
            masked = f"{proto}://{user}:***@{host_db}"
        except Exception:
            masked = "postgresql://***:***@.../..."
    return {
        "status": "configured",
        "url_masked": masked,
        "database": DATABASE_URL.split("/")[-1] if "/" in DATABASE_URL else "liga_barrios"
    }

from sqlalchemy.pool import NullPool

_engine: AsyncEngine | None = None

def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            poolclass=NullPool
        )
    return _engine


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Provide an async database connection context."""
    engine = get_engine()
    async with engine.connect() as conn:
        yield conn

async def test_connection() -> bool:
    """Quick connectivity test."""
    try:
        from sqlalchemy import text
        async with get_db_connection() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
