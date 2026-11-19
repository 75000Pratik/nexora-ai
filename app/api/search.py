from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from uuid import UUID
from fastapi import APIRouter, Request

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.schemas.search import SearchRequest, SearchResponse
from app.services.hybrid_retrieval_service import HybridRetrievalService

router = APIRouter(
    prefix="/search",
    tags=["search"],

)

retrieval_service = HybridRetrievalService()


@router.post(
    "",
    response_model=SearchResponse,
)
@limiter.limit(settings.search_rate_limit)
def search_documents(
    request: Request,
    body: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
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
    results = retrieval_service.retrieve(
        user_id=current_user.id,
        query=body.query,
        limit=body.limit,
        document_id=body.document_id,
        project_id=body.project_id,
    )

    return SearchResponse(
        query=body.query,
        results=results,
    )
