from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class DocumentCreate(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
        description="Original document filename",
    )

    content_type: str = Field(
        min_length=1,
        max_length=100,
        description="MIME type of the uploaded document",
    )


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: DocumentStatus
