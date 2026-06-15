from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.assignment_schema import (
    AssignmentCreateRequest,
    AssignmentCreateResponse,
    GeneratePurchaseOrdersRequest,
    GeneratePurchaseOrdersResponse,
)
from app.schemas.common_schema import success_response
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("")
def list_assignments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    manager_id: UUID | None = None,
    provider_id: UUID | None = None,
    initiative_id: UUID | None = None,
    status: str | None = None,
    alert: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = AssignmentService(db).list_assignments(
        current_user, manager_id, provider_id, initiative_id, status, alert, search, page, page_size
    )
    data = {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Assignments retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    assignment = AssignmentService(db).create_assignment(payload)
    data = AssignmentCreateResponse.model_validate(assignment).model_dump()
    return success_response("Assignment created successfully", data)


@router.post("/{assignment_id}/generate-monthly-purchase-orders", status_code=status.HTTP_201_CREATED)
def generate_monthly_purchase_orders(
    assignment_id: UUID,
    payload: GeneratePurchaseOrdersRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    result = AssignmentService(db).generate_monthly_purchase_orders(assignment_id, payload, current_user)
    data = GeneratePurchaseOrdersResponse.model_validate(result).model_dump()
    return success_response("Monthly purchase orders generated successfully", data)
