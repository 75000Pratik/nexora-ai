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
) -> SearchResponse:
    results = retrieval_service.retrieve(
        query=body.query,
        limit=body.limit,
        document_id=body.document_id,
        project_id=body.project_id,
    )

    return SearchResponse(
        query=body.query,
        results=results,
    )
