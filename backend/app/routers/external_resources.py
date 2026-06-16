from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.external_resource_schema import ExternalResourceCreateRequest, ExternalResourceResponse, ExternalResourceUpdateRequest
from app.services.external_resource_service import ExternalResourceService
from uuid import UUID
router = APIRouter(prefix="/external-resources", tags=["External Resources"])


@router.get("")
def list_external_resources(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
    search: str | None = None,
    technical_profile: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = ExternalResourceService(db).list_resources(
        search, technical_profile, is_active, page, page_size
    )
    data = {
        "items": [ExternalResourceResponse.model_validate(item).model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("External resources retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_external_resource(
    payload: ExternalResourceCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    resource = ExternalResourceService(db).create_resource(payload)
    data = ExternalResourceResponse.model_validate(resource).model_dump()
    return success_response("External resource created successfully", data)

@router.put("/{resource_id}")
def update_external_resource(
    resource_id: UUID,
    payload: ExternalResourceUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    resource = ExternalResourceService(db).update_resource(resource_id, payload)
    data = ExternalResourceResponse.model_validate(resource).model_dump()
    return success_response("External resource updated successfully", data)