import logging
import os
import socket
from urllib.parse import urlparse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import get_settings

logger = logging.getLogger("database")
settings = get_settings()

Base = declarative_base()

def is_db_reachable(db_url: str) -> bool:
    """Fast socket check (0.1s) to see if Postgres port is open, avoiding asyncpg timeouts."""
    if not db_url.startswith("postgresql"):
        return True
    try:
        clean_url = db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
        parsed = urlparse(clean_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except (OSError, socket.timeout):
        return False

# Determine effective database URL
configured_url = settings.DATABASE_URL
if configured_url.startswith("postgresql") and not is_db_reachable(configured_url):
    logger.warning(
        f"PostgreSQL at {configured_url} is not reachable. "
        "Automatically switching to local SQLite database at sqlite+aiosqlite:///./lenny_assistant.db"
    )
    active_db_url = "sqlite+aiosqlite:///./lenny_assistant.db"
else:
    active_db_url = configured_url

def get_engine_for_url(url: str):
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=settings.DB_ECHO)
    return create_async_engine(
        url,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

engine = get_engine_for_url(active_db_url)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

_tables_initialized = False

async def ensure_tables_exist():
    global _tables_initialized
    if not _tables_initialized:
        async with engine.begin() as conn:
            if "postgresql" in active_db_url:
                try:
                    from sqlalchemy import text
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
                except Exception:
                    pass
            await conn.run_sync(Base.metadata.create_all)
        _tables_initialized = True

async def init_db_with_fallback():
    await ensure_tables_exist()
    logger.info(f"Database schema initialized on {active_db_url}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    await ensure_tables_exist()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

