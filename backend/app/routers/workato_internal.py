from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_workato_internal
from app.models.user import AppUser
from app.schemas.ai_chat_api_schema import PurchaseOrderStatusUpdateRequest
from app.schemas.assignment_schema import GeneratePurchaseOrdersRequest
from app.schemas.common_schema import success_response
from app.services.assignment_service import AssignmentService
from app.services.dashboard_service import DashboardService
from app.services.excel_import_service import ExcelImportService
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/internal/workato", tags=["Workato Internal"])


@router.get("/dashboard-summary")
def workato_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
):
    """Skill: get_dashboard_summary — status, assignments, expirations, PO counts, committed cost."""
    summary = DashboardService(db).get_summary(current_user)
    return success_response("Dashboard summary retrieved successfully", summary.model_dump())


@router.get("/expiring-resources")
def workato_expiring_resources(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
    alert: str | None = Query(default=None, description="Filter by RED, AMBER, or GREEN"),
    days_threshold: int = Query(default=30, ge=0, le=365, description="Max days until contract end"),
    include_expired: bool = Query(default=True, description="Include already expired contracts"),
):
    """Skill: get_expiring_resources — expired, RED/AMBER alerts, renewals, contracts ending soon."""
    result = DashboardService(db).get_expiring_resources(
        current_user,
        alert=alert,
        days_threshold=days_threshold,
        include_expired=include_expired,
    )
    return success_response("Expiring resources retrieved successfully", result.model_dump())


@router.get("/assignments")
def workato_assignments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
    assignment_id: UUID | None = Query(default=None, description="Lookup a specific assignment by ID"),
    manager_id: UUID | None = None,
    provider_id: UUID | None = None,
    initiative_id: UUID | None = None,
    status: str | None = None,
    alert: str | None = Query(default=None, description="Filter by expiration alert: RED, AMBER, GREEN"),
    search: str | None = Query(default=None, description="Search consultant, profile, provider, or initiative"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """Skill: search_assignments — consultant, profile, provider, initiative, and assignment lookup."""
    if assignment_id:
        item = AssignmentService(db).get_assignment_detail(assignment_id, current_user)
        data = {
            "items": [item.model_dump()],
            "total": 1,
            "page": 1,
            "page_size": page_size,
        }
        return success_response("Assignments retrieved successfully", data)

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


@router.get("/purchase-orders")
def workato_purchase_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
    assignment_id: UUID | None = None,
    provider_id: UUID | None = None,
    status: str | None = Query(default=None, description="PENDING, COUPA_GENERATED, SENT, APPROVED, CLOSED, CANCELLED"),
    period_from: date | None = Query(default=None, description="Filter purchase orders from this month"),
    period_to: date | None = Query(default=None, description="Filter purchase orders up to this month"),
    search: str | None = Query(default=None, description="Search by consultant, provider, or PO number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """Skill: get_purchase_orders_status — PO status, counts, and filtered listings."""
    result = PurchaseOrderService(db).get_purchase_orders_status(
        current_user,
        assignment_id,
        provider_id,
        status,
        period_from,
        period_to,
        page,
        page_size,
        search,
    )
    return success_response(
        "Purchase orders retrieved successfully",
        result.model_dump(),
    )


@router.get("/budget-summary")
def workato_budget_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
):
    """Skill: get_budget_summary — committed budget, monthly cost, and cost breakdowns."""
    summary = DashboardService(db).get_budget_summary(current_user)
    return success_response("Budget summary retrieved successfully", summary.model_dump())


@router.get("/import-status")
def workato_import_status(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
    recent_limit: int = Query(default=5, ge=1, le=20, description="Number of recent import batches to include"),
):
    """Skill: get_import_status — latest import, historical batches, row errors."""
    status_data = ExcelImportService(db).get_import_status(current_user, recent_limit)
    return success_response("Import status retrieved successfully", status_data.model_dump(mode="json"))


@router.post("/assignments/{assignment_id}/generate-monthly-purchase-orders")
def workato_generate_monthly_purchase_orders(
    assignment_id: UUID,
    payload: GeneratePurchaseOrdersRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
):
    result = AssignmentService(db).generate_monthly_purchase_orders(assignment_id, payload, current_user)
    return success_response("Monthly purchase orders generated successfully", result.model_dump())


@router.put("/purchase-orders/{purchase_order_id}/status")
def workato_update_purchase_order_status(
    purchase_order_id: UUID,
    payload: PurchaseOrderStatusUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AppUser, Depends(verify_workato_internal)],
):
    purchase_order = PurchaseOrderService(db).update_status(
        purchase_order_id,
        payload.status,
        payload.comments,
        current_user,
        po_number=payload.po_number,
    )
    data = {
        "id": purchase_order.id,
        "status": purchase_order.status,
        "po_number": purchase_order.po_number,
        "comments": purchase_order.comments,
    }
    return success_response("Purchase order status updated successfully", data)
