import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatus,
)
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
    request: Request,
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentResponse:

    form_data = await request.form()
    raw_project_id = form_data.get("project_id")

    if raw_project_id is not None and not str(raw_project_id).strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Project ID cannot be empty.",
        )

    if project_id is not None:
        project_id = project_id.strip()

        if len(project_id) > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Project ID cannot exceed 100 characters.",
            )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File size exceeds the 10 MB limit.",
        )

    if b"%PDF-" not in content[:1024]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid PDF.",
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


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    repository = DocumentRepository(db)

    document = repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        content_type=document.content_type,
        status=DocumentStatus(document.status),
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
def list_documents(
    skip: int = 0,
    limit: int = 20,
    document_status: DocumentStatus | None = None,
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Skip must be greater than or equal to zero.",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Limit must be between 1 and 100.",
        )

    repository = DocumentRepository(db)

    documents, total = repository.list_documents(
        skip=skip,
        limit=limit,
        status=document_status,
    )

    return DocumentListResponse(
        items=[
            DocumentResponse(
                id=str(document.id),
                filename=document.filename,
                content_type=document.content_type,
                status=DocumentStatus(document.status),
            )
            for document in documents
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    repository = DocumentRepository(db)

    document = repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    document_id_str = str(document.id)
    file_path = UPLOAD_DIR / f"{document_id_str}.pdf"

    # Step 1: Delete document vectors from Qdrant.
    try:
        vector_store.delete_document_chunks(document_id_str)

    except Exception as exc:
        logger.exception(
            "Failed to delete document vectors. document_id=%s",
            document_id_str,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document vectors.",
        ) from exc

    # Step 2: Delete the stored PDF.
    try:
        file_path.unlink(missing_ok=True)

    except OSError as exc:
        logger.exception(
            "Failed to delete document PDF. document_id=%s",
            document_id_str,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document file.",
        ) from exc

    # Step 3: Delete document metadata from PostgreSQL.
    try:
        repository.delete(document)

    except Exception as exc:
        logger.exception(
            "Failed to delete document metadata. document_id=%s",
            document_id_str,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document metadata.",
        ) from exc
