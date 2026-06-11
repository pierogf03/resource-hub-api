from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.purchase_order import PurchaseOrder
from app.models.user import AppUser
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.purchase_order_schema import (
    PurchaseOrderCreateRequest,
    PurchaseOrderCreateResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdateRequest,
)
from app.utils.date_utils import first_day_of_month
from app.utils.money_utils import calculate_amount_usd


class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db
        self.po_repo = PurchaseOrderRepository(db)
        self.assignment_repo = AssignmentRepository(db)

    def _role_filters(self, current_user: AppUser) -> tuple[UUID | None, UUID | None]:
        if current_user.role == "ADMIN":
            return None, None
        if current_user.role == "MANAGER":
            return current_user.id, None
        return None, current_user.id

    def list_purchase_orders(
        self,
        current_user: AppUser,
        assignment_id: UUID | None,
        provider_id: UUID | None,
        status: str | None,
        period_from,
        period_to,
        page: int,
        page_size: int,
    ):
        manager_id, analyst_id = self._role_filters(current_user)
        items, total = self.po_repo.list_purchase_orders(
            assignment_id, provider_id, status, period_from, period_to, manager_id, analyst_id, page, page_size
        )
        response_items = [
            PurchaseOrderResponse(
                id=item.id,
                assignment_id=item.assignment_id,
                consultant_name=item.assignment.resource.consultant_name if item.assignment and item.assignment.resource else None,
                provider_name=item.provider.name if item.provider else None,
                period_month=item.period_month,
                po_number=item.po_number,
                status=item.status,
                amount=item.amount,
                currency=item.currency,
                exchange_rate=item.exchange_rate,
                amount_usd=item.amount_usd,
                comments=item.comments,
            )
            for item in items
        ]
        return response_items, total

    def create_purchase_order(self, payload: PurchaseOrderCreateRequest) -> PurchaseOrderCreateResponse:
        assignment = self.assignment_repo.get_by_id(payload.assignment_id)
        if not assignment:
            raise AppException("Assignment not found", status_code=404)
        period_month = first_day_of_month(payload.period_month)
        if period_month < first_day_of_month(assignment.start_date) or period_month > first_day_of_month(assignment.end_date):
            raise AppException("Purchase order period must be within assignment date range")
        if self.assignment_repo.get_purchase_order_by_period(assignment.id, period_month):
            raise AppException("Purchase order already exists for this assignment and month")

        amount_usd = calculate_amount_usd(payload.amount, payload.currency, payload.exchange_rate)
        purchase_order = PurchaseOrder(
            assignment_id=assignment.id,
            provider_id=assignment.provider_id,
            period_month=period_month,
            po_number=payload.po_number,
            status=payload.status,
            amount=payload.amount,
            currency=payload.currency,
            exchange_rate=payload.exchange_rate if payload.currency == "PEN" else None,
            amount_usd=amount_usd,
            comments=payload.comments,
        )
        created = self.po_repo.create(purchase_order)
        return PurchaseOrderCreateResponse(
            id=created.id,
            assignment_id=created.assignment_id,
            period_month=created.period_month,
            po_number=created.po_number,
            status=created.status,
            amount_usd=created.amount_usd,
        )

    def update_purchase_order(self, purchase_order_id: UUID, payload: PurchaseOrderUpdateRequest) -> PurchaseOrder:
        purchase_order = self.po_repo.get_by_id(purchase_order_id)
        if not purchase_order:
            raise AppException("Purchase order not found", status_code=404)
        purchase_order.po_number = payload.po_number
        purchase_order.status = payload.status
        purchase_order.amount = payload.amount
        purchase_order.currency = payload.currency
        purchase_order.exchange_rate = payload.exchange_rate if payload.currency == "PEN" else None
        purchase_order.amount_usd = calculate_amount_usd(payload.amount, payload.currency, payload.exchange_rate)
        purchase_order.comments = payload.comments
        return self.po_repo.update(purchase_order)
