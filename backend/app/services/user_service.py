from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateRequest


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def list_users(self, search: str | None, role: str | None, is_active: bool | None, page: int, page_size: int):
        return self.user_repo.list_users(search, role, is_active, page, page_size)

    def create_user(self, payload: UserCreateRequest) -> AppUser:
        if self.user_repo.get_by_email(payload.email):
            raise AppException("Email already exists", errors=[{"field": "email", "message": "Email already exists"}])
        user = AppUser(
            full_name=payload.full_name.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        return self.user_repo.create(user)
