from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.example_service import ExampleService


def get_example_service(request: Request) -> ExampleService:
    """Return the singleton ExampleService instance from app state."""
    return request.app.state.example_service


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Yield a database session from the app-level session factory."""
    async with request.app.state.db_session_factory() as session:
        yield session
