from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)
settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user: AppUser) -> tuple[str, int]:
    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(user.id),
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise AppException("Invalid or expired token", status_code=status.HTTP_401_UNAUTHORIZED) from exc


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> AppUser:
    if credentials is None or not credentials.credentials:
        raise AppException("Not authenticated", status_code=status.HTTP_401_UNAUTHORIZED)
    payload = decode_token(credentials.credentials)
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise AppException("Invalid token payload", status_code=status.HTTP_401_UNAUTHORIZED)
    user = UserRepository(db).get_by_id(UUID(str(user_id)))
    if not user:
        raise AppException("User not found", status_code=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise AppException("User is inactive", status_code=status.HTTP_403_FORBIDDEN)
    return user


def require_admin(current_user: Annotated[AppUser, Depends(get_current_user)]) -> AppUser:
    if current_user.role != "ADMIN":
        raise AppException("Admin access required", status_code=status.HTTP_403_FORBIDDEN)
    return current_user


def require_manager_or_admin(current_user: Annotated[AppUser, Depends(get_current_user)]) -> AppUser:
    if current_user.role not in {"ADMIN", "MANAGER"}:
        raise AppException("Manager or admin access required", status_code=status.HTTP_403_FORBIDDEN)
    return current_user
