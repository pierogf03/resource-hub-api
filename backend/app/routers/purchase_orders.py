from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.purchase_order_schema import (
    PurchaseOrderCreateRequest,
    PurchaseOrderCreateResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdateRequest,
)
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("")
def list_purchase_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    assignment_id: UUID | None = None,
    provider_id: UUID | None = None,
    status: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    items, total = PurchaseOrderService(db).list_purchase_orders(
        current_user, assignment_id, provider_id, status, period_from, period_to, page, page_size
    )
    data = {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return success_response("Purchase orders retrieved successfully", data)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    purchase_order = PurchaseOrderService(db).create_purchase_order(payload)
    data = PurchaseOrderCreateResponse.model_validate(purchase_order).model_dump()
    return success_response("Purchase order created successfully", data)


@router.put("/{purchase_order_id}")
def update_purchase_order(
    purchase_order_id: UUID,
    payload: PurchaseOrderUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AppUser, Depends(get_current_user)],
):
    purchase_order = PurchaseOrderService(db).update_purchase_order(purchase_order_id, payload)
    data = {
        "id": purchase_order.id,
        "po_number": purchase_order.po_number,
        "status": purchase_order.status,
        "amount_usd": purchase_order.amount_usd,
    }
    return success_response("Purchase order updated successfully", data)
