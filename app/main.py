from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    LLMServiceTimeoutError,
    LLMServiceError,
)
from app.api.ask import router as ask_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import settings
from app.api.search import router as search_router


app = FastAPI(
    title=settings.app_name,
    description="Production Agentic Knowledge Intelligence Platform",
    version=settings.app_version,
)


@app.exception_handler(LLMServiceTimeoutError)
async def llm_timeout_handler(
    request: Request,
    exc: LLMServiceTimeoutError,
):
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
    return JSONResponse(
        status_code=502,
        content={
            "detail": "The AI service is temporarily unavailable."
        },
    )

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)
