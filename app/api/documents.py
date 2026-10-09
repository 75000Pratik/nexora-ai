from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.document import (
    DocumentResponse,
    DocumentStatus,
)

from app.services.pdf_service import extract_text_from_pdf
from app.services.text_service import normalize_text
from app.services.chunking_service import chunk_text

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
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

    document_id = str(uuid4())

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

    cleaned_text = normalize_text(extracted_text)

    chunks = chunk_text(
        cleaned_text,
        chunk_size=1000,
        overlap=150,
    )

    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        status=DocumentStatus.uploaded,
    )
