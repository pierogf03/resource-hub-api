from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, payload: RegisterRequest, allow_without_admin: bool = False) -> AppUser:
        if self.user_repo.get_by_email(payload.email):
            raise AppException("Email already registered", errors=[{"field": "email", "message": "Email already exists"}])
        if not allow_without_admin and self.user_repo.count() > 0:
            raise AppException("Registration requires admin privileges")
        user = AppUser(
            full_name=payload.full_name.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        return self.user_repo.create(user)

    def login(self, payload: LoginRequest) -> tuple[str, int, AppUser]:
        user = self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppException("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppException("User is inactive", status_code=403)
        token, expires_in = create_access_token(user)
        return token, expires_in, user
