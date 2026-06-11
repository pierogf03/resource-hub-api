from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import decode_token, get_current_user
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, LoginResponse, RegisterRequest, UserAuthResponse
from app.schemas.common_schema import success_response
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _optional_admin_from_header(authorization: str | None, db: Session) -> AppUser | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return None
    from uuid import UUID

    user = UserRepository(db).get_by_id(UUID(str(user_id)))
    if user and user.is_active and user.role == "ADMIN":
        return user
    return None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
):
    user_repo = UserRepository(db)
    allow_without_admin = user_repo.count() == 0
    if not allow_without_admin:
        admin = _optional_admin_from_header(authorization, db)
        if not admin:
            raise AppException("Admin access required", status_code=status.HTTP_403_FORBIDDEN)
    user = AuthService(db).register(payload, allow_without_admin=allow_without_admin)
    data = UserAuthResponse.model_validate(user).model_dump()
    return success_response("User registered successfully", data)


@router.post("/login")
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    token, expires_in, user = AuthService(db).login(payload)
    data = LoginResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserAuthResponse.model_validate(user),
    ).model_dump()
    return success_response("Login successful", data)


@router.get("/me")
def me(current_user: Annotated[AppUser, Depends(get_current_user)]):
    data = UserAuthResponse.model_validate(current_user).model_dump()
    return success_response("Current user retrieved successfully", data)
