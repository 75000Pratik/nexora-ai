
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )
    document_id: str | None = None
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
    )


class AnswerSource(BaseModel):
    document_id: str
    chunk_index: int
    text: str


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: list[AnswerSource]
