from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        document_id: UUID,
        filename: str,
        content_type: str,
        project_id: str | None = None,
        status: str = "processing",
    ) -> Document:
        document = Document(
            id=document_id,
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

    def update_status(
        self,
        document: Document,
        status: str,
    ) -> Document:
        document.status = status

        try:
            self.db.commit()
            self.db.refresh(document)
        except Exception:
            self.db.rollback()
            raise

        return document