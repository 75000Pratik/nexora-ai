import logging
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
    Depends,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse, DocumentStatus
from app.services.document_processing_service import process_document_text
from app.services.pdf_service import extract_text_from_pdf
from app.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


def remove_uploaded_file(file_path: Path, document_id: str) -> None:
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.exception(
            "Failed to remove uploaded PDF. document_id=%s",
            document_id,
        )


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024

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
        remove_uploaded_file(file_path, document_id)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read the uploaded PDF.",
        ) from exc

    if not extracted_text:
        remove_uploaded_file(file_path, document_id)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No extractable text was found in the PDF.",
        )

    try:
        chunks, embeddings = process_document_text(extracted_text)

    except Exception as exc:
        remove_uploaded_file(file_path, document_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process the uploaded document.",
        ) from exc

    repository = DocumentRepository(db)

    try:
        document = repository.create(
            document_id=document_uuid,
            filename=file.filename,
            content_type=file.content_type,
            project_id=project_id,
        )

    except Exception as exc:
        remove_uploaded_file(file_path, document_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save document metadata.",
        ) from exc

    try:
        vector_store.store_document_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            project_id=project_id,
        )

        repository.update_status(
            document,
            DocumentStatus.ready,
        )

    except Exception:
        logger.exception(
            "Document upload failed. document_id=%s",
            document_id,
        )

        try:
            vector_store.delete_document_chunks(document_id)

        except Exception:
            logger.exception(
                "Failed to clean up Qdrant vectors. document_id=%s",
                document_id,
            )

        try:
            repository.update_status(
                document,
                DocumentStatus.failed,
            )

        except Exception:
            logger.exception(
                "Failed to mark document as failed. document_id=%s",
                document_id,
            )

        remove_uploaded_file(file_path, document_id)

        raise

    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        status=DocumentStatus.ready,
    )
