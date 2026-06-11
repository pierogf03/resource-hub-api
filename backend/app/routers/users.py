from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.user_schema import UserCreateRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(require_admin)],
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = UserService(db).list_users(search, role, is_active, page, page_size)
    data = {
        "items": [UserResponse.model_validate(item).model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Users retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(require_admin)],
):
    user = UserService(db).create_user(payload)
    data = UserResponse.model_validate(user).model_dump()
    return success_response("User created successfully", data)
