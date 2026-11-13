from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.schemas.answer import AskRequest, AskResponse
from app.services.answer_service import AnswerService
from app.services.agent_router import AgentRoute, AgentRouter
from app.services.general_answer_service import GeneralAnswerService

router = APIRouter(
    prefix="/ask",
    tags=["answer generation"],
)

answer_service = AnswerService()
agent_router = AgentRouter()
general_answer_service = GeneralAnswerService()


@router.post(
    "",
    response_model=AskResponse,
)
@limiter.limit(settings.ask_rate_limit)
def ask_question(
    request: Request,
    body: AskRequest,
) -> AskResponse:
    selected_route = agent_router.route(
        query=body.query,
        document_id=body.document_id,
        project_id=body.project_id,
        requested_route=body.route,
    )

    if selected_route == AgentRoute.DOCUMENT_QA:
        return answer_service.answer(
            query=body.query,
            limit=body.limit,
            document_id=body.document_id,
            project_id=body.project_id,
        )

    if selected_route == AgentRoute.GENERAL:
        return general_answer_service.answer(
            query=body.query,
        )

    raise HTTPException(
        status_code=501,
        detail="Requested route is not implemented yet",
    )
