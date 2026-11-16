from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: str,
        content_type: str,
        project_id: str | None = None,
        status: str = "processing",
    ) -> Document:
        document = Document(
            id=document_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            project_id=project_id,
            status=status,
        )

        try:
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
        except Exception:
            self.db.rollback()
            raise

        return document

    def get_by_id(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> Document | None:
        query = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        return self.db.scalar(query)

    def delete(self, document: Document) -> None:
        try:
            self.db.delete(document)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: DocumentStatus | None = None,
    ) -> tuple[list[Document], int]:

        query = select(Document)
        query = query.where(Document.user_id == user_id)

        """Return pagination documents and the total matching count."""

        if status is not None:
            query = query.where(Document.status == status.value)

        total_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(total_query) or 0

        query = (
            query
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        documents = list(self.db.scalars(query).all())

        return documents, total

    def update_status(
        self,
        document: Document,
        status: DocumentStatus,
    ) -> Document:
        document.status = status.value

        try:
            self.db.commit()
            self.db.refresh(document)
        except Exception:
            self.db.rollback()
            raise

        return document
