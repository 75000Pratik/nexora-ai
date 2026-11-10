
from pydantic import BaseModel, Field
from app.services.agent_router import AgentRoute


class AskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )
    document_id: str | None = None
    project_id: str | None = None
    route: AgentRoute = AgentRoute.DOCUMENT_QA
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
