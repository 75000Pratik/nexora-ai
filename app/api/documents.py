from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Depends
from sqlalchemy.orm import Session

from app.schemas.document import (
    DocumentResponse,
    DocumentStatus,
)

from app.services.pdf_service import extract_text_from_pdf
from app.services.vector_store_service import VectorStoreService
from app.services.document_processing_service import process_document_text
from app.repositories.document_repository import DocumentRepository
from app.core.database import get_db

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}

vector_store = VectorStoreService()
vector_store.ensure_collection()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 10 MB limit.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    document_uuid = uuid4()
    document_id = str(document_uuid)


    safe_filename = f"{document_id}.pdf"
    file_path = UPLOAD_DIR / safe_filename

    file_path.write_bytes(content)

    try:
        extracted_text = extract_text_from_pdf(file_path)

    except Exception as exc:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read the uploaded PDF.",
        ) from exc

    if not extracted_text:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No extractable text was found in the PDF.",
        )

    chunks, embeddings = process_document_text(extracted_text)

    repository = DocumentRepository(db)

    document = repository.create(
        document_id=document_uuid,
        filename=file.filename,
        content_type=file.content_type,
        project_id=project_id,
    )

    try:

        vector_store.store_document_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            project_id=project_id,
        )

        repository.update_status(document, "ready")

    except Exception:
        repository.update_status(document, "failed")
        raise    

    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        status=DocumentStatus.ready,
    )
