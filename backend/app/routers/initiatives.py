from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.initiative_schema import InitiativeCreateRequest, InitiativeResponse
from app.services.initiative_service import InitiativeService

router = APIRouter(prefix="/initiatives", tags=["Initiatives"])


@router.get("")
def list_initiatives(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
    search: str | None = None,
    responsible_manager_id: UUID | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = InitiativeService(db).list_initiatives(
        search, responsible_manager_id, is_active, page, page_size
    )
    data = {
        "items": [InitiativeResponse.model_validate(item).model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Initiatives retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_initiative(
    payload: InitiativeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    initiative = InitiativeService(db).create_initiative(payload)
    data = InitiativeResponse.model_validate(initiative).model_dump()
    return success_response("Initiative created successfully", data)
