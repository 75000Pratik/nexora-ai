import logging

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.documents import vector_store
from app.core.config import settings
from app.core.database import engine


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "nexora-ai",
        "environment": settings.environment,
    }


@router.get("/ready")
def readiness_check():
    checks = {
        "database": False,
        "qdrant": False,
        "ollama": False,
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        checks["database"] = True
    except Exception:
        logger.exception("Database readiness check failed")

    try:
        vector_store.client.get_collections()
        checks["qdrant"] = True
    except Exception:
        logger.exception("Qdrant readiness check failed")

    try:
        response = httpx.get(
            f"{settings.ollama_url}/api/tags",
            timeout=3.0,
        )
        response.raise_for_status()
        checks["ollama"] = True
    except Exception:
        logger.exception("Ollama readiness check failed")

    is_ready = all(checks.values())

    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
        },
    )
