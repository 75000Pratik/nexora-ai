from uuid import UUID
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)

    def register(
        self,
        email: str,
        password: str,
    ) -> User | None:
        existing_user = self.user_repository.get_by_email(email)

        if existing_user is not None:
            return None

        hashed_password = hash_password(password)

        return self.user_repository.create(
            email=email,
            password_hash=hashed_password,
        )

    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[User, str] | None:
        user = self.user_repository.get_by_email(email)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        access_token = create_access_token(str(user.id))

        return user, access_token

    def get_user(self, user_id: str) -> User | None:

        try:
            parsed_user_id = UUID(user_id)
        except ValueError:
            return None

        return self.user_repository.get_by_id(parsed_user_id)
