from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.user import AppUser
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.dashboard_schema import (
    DashboardSummaryResponse,
    ExpirationAlertSummary,
    ExpiringResourceItem,
    PurchaseOrderStatusSummary,
)
from app.utils.date_utils import days_to_end, expiration_alert


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.po_repo = PurchaseOrderRepository(db)

    def _scope_ids(self, current_user: AppUser) -> tuple:
        if current_user.role == "ADMIN":
            return None, None
        if current_user.role == "MANAGER":
            return current_user.id, None
        return None, current_user.id

    def get_summary(self, current_user: AppUser) -> DashboardSummaryResponse:
        manager_id, analyst_id = self._scope_ids(current_user)
        assignments = self.assignment_repo.list_for_dashboard(manager_id, analyst_id)
        active_assignments = [a for a in assignments if a.status == "ACTIVE"]
        expiring_soon = [a for a in active_assignments if 0 <= days_to_end(a.end_date) <= 30]
        expired = [a for a in active_assignments if days_to_end(a.end_date) < 0]

        alerts = ExpirationAlertSummary(green=0, amber=0, red=0)
        for assignment in active_assignments:
            alert = expiration_alert(assignment.end_date)
            if alert == "GREEN":
                alerts.green += 1
            elif alert == "AMBER":
                alerts.amber += 1
            else:
                alerts.red += 1

        assignment_ids = [a.id for a in assignments]
        purchase_orders = self.po_repo.list_for_assignments(assignment_ids)
        po_summary = PurchaseOrderStatusSummary(
            total=len(purchase_orders),
            pending=sum(1 for po in purchase_orders if po.status == "PENDING"),
            coupa_generated=sum(1 for po in purchase_orders if po.status == "COUPA_GENERATED"),
            sent=sum(1 for po in purchase_orders if po.status == "SENT"),
            approved=sum(1 for po in purchase_orders if po.status == "APPROVED"),
            closed=sum(1 for po in purchase_orders if po.status == "CLOSED"),
        )

        total_monthly = sum((a.monthly_cost_usd for a in active_assignments), Decimal("0"))
        total_committed = sum((a.total_cost_usd for a in active_assignments), Decimal("0"))

        return DashboardSummaryResponse(
            active_assignments=len(active_assignments),
            expiring_soon=len(expiring_soon),
            expired=len(expired),
            total_monthly_cost_usd=total_monthly,
            total_committed_cost_usd=total_committed,
            purchase_orders=po_summary,
            expiration_alerts=alerts,
        )

    def get_expiring_resources(self, current_user: AppUser) -> list[ExpiringResourceItem]:
        manager_id, analyst_id = self._scope_ids(current_user)
        assignments = self.assignment_repo.list_for_dashboard(manager_id, analyst_id)
        active_assignments = [a for a in assignments if a.status == "ACTIVE"]
        active_assignments.sort(key=lambda a: days_to_end(a.end_date))
        result: list[ExpiringResourceItem] = []
        for assignment in active_assignments:
            if days_to_end(assignment.end_date) > 30:
                continue
            assignment_full = self.assignment_repo.get_by_id(assignment.id)
            if not assignment_full:
                continue
            result.append(
                ExpiringResourceItem(
                    assignment_id=assignment_full.id,
                    consultant_name=assignment_full.resource.consultant_name,
                    technical_profile=assignment_full.resource.technical_profile,
                    provider_name=assignment_full.provider.name,
                    main_initiative_name=assignment_full.main_initiative.name,
                    end_date=assignment_full.end_date,
                    days_to_end=days_to_end(assignment_full.end_date),
                    expiration_alert=expiration_alert(assignment_full.end_date),
                )
            )
        return result
