import logging

from app.api.auth import router as auth_router
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limiter import limiter
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIDMiddleware
from app.core.exceptions import (
    LLMServiceTimeoutError,
    LLMServiceError,
)
from app.api.ask import router as ask_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import settings
from app.api.projects import router as projects_router
from app.api.search import router as search_router

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Production Agentic Knowledge Intelligence Platform",
    version=settings.app_version,
)

app.add_middleware(RequestIDMiddleware)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


@app.exception_handler(LLMServiceTimeoutError)
async def llm_timeout_handler(
    request: Request,
    exc: LLMServiceTimeoutError,
):
    logger.error(
        "LLM service request timed out",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": 504,
        },
    )

    return JSONResponse(
        status_code=504,
        content={
            "detail": "The AI service request timed out. Please try again."
        },
    )


@app.exception_handler(LLMServiceError)
async def llm_error_handler(
    request: Request,
    exc: LLMServiceError,
):
    logger.error(
        "LLM service unavailable",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": 502,
        },
    )

    return JSONResponse(
        status_code=502,
        content={
            "detail": "The AI service is temporarily unavailable."
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.error(
        "Unhandled request exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred."
        },
    )

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(auth_router)
app.include_router(projects_router)
