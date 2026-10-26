from fastapi import APIRouter

from app.schemas.answer import AskRequest, AskResponse
from app.services.answer_service import AnswerService

router = APIRouter(
    prefix = "/ask",
    tags = ["answer generation"],
)

answer_service = AnswerService()

@router.post(
    "",
    response_model = AskResponse,
)
def ask_question(
    request: AskRequest,
) -> AskResponse:
    return answer_service.answer(
        query = request.query,
        limit = request.limit,
        document_id = request.document_id,
    )