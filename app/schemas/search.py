
from pydantic import BaseModel, Field

from app.schemas.retrieval import RetrievalResult


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )
    document_id: str | None = None
    limit: int = Field(
        default=3,
        ge=1,
        le=20,
    )


class SearchResponse(BaseModel):
    query: str
    results: list[RetrievalResult]
