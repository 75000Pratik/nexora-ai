from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.rate_limiter import limiter
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AskResponse:
    selected_route = agent_router.route(
        query=body.query,
        document_id=body.document_id,
        project_id=body.project_id,
        requested_route=body.route,
    )

    if selected_route == AgentRoute.DOCUMENT_QA:

        if body.document_id is not None:
            try:
                document_uuid = UUID(body.document_id)
            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            document = DocumentRepository(db).get_by_id(
                document_id=document_uuid,
                user_id=current_user.id,
            )

            if document is None:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

        if body.project_id is not None:
            try:
                project_uuid = UUID(body.project_id)
            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail="Project not found.",
                )

            project = ProjectRepository(db).get_by_id(
                project_id=project_uuid,
                user_id=current_user.id,
            )

            if project is None:
                raise HTTPException(
                    status_code=404,
                    detail="Project not found.",
                )

        return answer_service.answer(
            user_id=current_user.id,
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
