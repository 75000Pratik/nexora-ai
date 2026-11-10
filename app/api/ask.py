from fastapi import APIRouter, HTTPException

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
def ask_question(
    request: AskRequest,
) -> AskResponse:
    selected_route = agent_router.route(
        query=request.query,
        document_id=request.document_id,
        project_id=request.project_id,
        requested_route=request.route,
    )

    if selected_route == AgentRoute.DOCUMENT_QA:
        return answer_service.answer(
            query=request.query,
            limit=request.limit,
            document_id=request.document_id,
            project_id=request.project_id,
        )

    if selected_route == AgentRoute.GENERAL:
        return general_answer_service.answer(
            query=request.query,
        )

    raise HTTPException(
        status_code=501,
        detail="Requested route is not implemented yet",
    )
