from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
            self,
            user_id: UUID,
            name: str,
            description: str | None = None,
    ) -> Project:
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
        )

        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        except Exception:
            self.db.rollback()
            raise

        return project

    def get_by_id(
            self,
            project_id: UUID,
            user_id: UUID,
    ) -> Project | None:
        query = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        return self.db.scalar(query)

    def list_projects(
            self,
            user_id: UUID,
    ) -> list[Project]:
        query = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def delete(self, project: Project) -> None:
        try:
            self.db.delete(project)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
