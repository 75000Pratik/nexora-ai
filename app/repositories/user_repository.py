
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        email: str,
        password_hash: str,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except Exception:
            self.db.rollback()
            raise

        return user

    def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        return self.db.scalar(query)

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)
