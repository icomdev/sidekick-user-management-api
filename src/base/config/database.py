import logging
import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.base.utils.env_utils import is_local_development

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


def _get_database_url() -> str:
    """Resolve database URL from environment, defaulting to local SQLite."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return "sqlite+aiosqlite:///./local.db"


async def init_db() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize the database engine and session factory.

    In non-production environments, auto-creates all tables registered
    with Base.metadata.

    Returns:
        Tuple of (engine, session_factory).
    """
    url = _get_database_url()

    # Log connection target without credentials
    safe_url = url.split("@")[-1] if "@" in url else url
    logger.info("Connecting to database: %s", safe_url)

    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(url, connect_args=connect_args)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Auto-create tables in non-production environments
    if is_local_development():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created.")

    return engine, session_factory


async def close_db(engine: AsyncEngine) -> None:
    """Dispose the database engine and release connections."""
    if engine:
        await engine.dispose()
        logger.info("Database connection closed.")
        logger.info("Database connection closed.")
