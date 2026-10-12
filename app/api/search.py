from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(
    prefix="/search",
    tags=["search"],

)

retrieval_service = RetrievalService()


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
