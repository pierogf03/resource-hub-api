from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.provider_schema import ProviderCreateRequest, ProviderResponse, ProviderUpdateRequest
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("")
def list_providers(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = ProviderService(db).list_providers(search, is_active, page, page_size)
    data = {
        "items": [ProviderResponse.model_validate(item).model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Providers retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_provider(
    payload: ProviderCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    provider = ProviderService(db).create_provider(payload)
    data = ProviderResponse.model_validate(provider).model_dump()
    return success_response("Provider created successfully", data)


@router.put("/{provider_id}")
def update_provider(
    provider_id: UUID,
    payload: ProviderUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    provider = ProviderService(db).update_provider(provider_id, payload)
    data = ProviderResponse.model_validate(provider).model_dump()
    return success_response("Provider updated successfully", data)
