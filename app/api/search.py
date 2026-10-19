from fastapi import APIRouter

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
def search_documents(
    request: SearchRequest,
) -> SearchResponse:
    results = retrieval_service.retrieve(
        query=request.query,
        limit=request.limit,
        document_id=request.document_id,
    )

    return SearchResponse(
        query=request.query,
        results=results,
    )
