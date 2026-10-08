from uuid import uuid4

from fastapi import APIRouter, status

from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentStatus,
)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_document(document: DocumentCreate) -> DocumentResponse:
    return DocumentResponse(
        id=str(uuid4()),
        filename=document.filename,
        content_type=document.content_type,
        status=DocumentStatus.uploaded,
    )