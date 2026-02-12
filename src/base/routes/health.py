import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

router = APIRouter(tags=["Health"], prefix="")
logger = logging.getLogger(__name__)


@router.get("/health")
async def health(request: Request):
    """
    Health check endpoint.
    Returns 200 OK if the service is healthy, including database connectivity status.
    """
    result = {"status": "Healthy", "message": "Service is up and running."}

    if hasattr(request.app.state, "db_engine"):
        try:
            async with request.app.state.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            result["database"] = "connected"
        except Exception:
            logger.exception("Database health check failed")
            result["database"] = "unavailable"
            result["status"] = "Degraded"

    return JSONResponse(status_code=200, content=result)


@router.get("/")
async def health_v2():
    """
    Health check endpoint.
    This endpoint returns 200 OK if the service is healthy.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "Healthy", "message": "Service is up and running."},
    )
