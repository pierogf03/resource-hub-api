from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.user import AppUser
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.dashboard_schema import (
    BudgetBreakdownItem,
    BudgetSummaryResponse,
    DashboardSummaryResponse,
    ExpirationAlertSummary,
    ExpiringResourceItem,
    ExpiringResourcesResponse,
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

    def _scoped_assignments(self, current_user: AppUser):
        manager_id, analyst_id = self._scope_ids(current_user)
        return self.assignment_repo.list_for_dashboard(manager_id, analyst_id)

    def get_summary(self, current_user: AppUser) -> DashboardSummaryResponse:
        assignments = self._scoped_assignments(current_user)
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
            total_assignments=len(assignments),
            active_assignments=len(active_assignments),
            expiring_soon=len(expiring_soon),
            expired=len(expired),
            total_monthly_cost_usd=total_monthly,
            total_committed_cost_usd=total_committed,
            purchase_orders=po_summary,
            expiration_alerts=alerts,
        )

    def get_expiring_resources(
        self,
        current_user: AppUser,
        alert: str | None = None,
        days_threshold: int = 30,
        include_expired: bool = True,
    ) -> ExpiringResourcesResponse:
        assignments = self._scoped_assignments(current_user)
        active_assignments = [a for a in assignments if a.status == "ACTIVE"]
        active_assignments.sort(key=lambda a: days_to_end(a.end_date))

        items: list[ExpiringResourceItem] = []
        expired_count = red_count = amber_count = green_count = 0

        for assignment in active_assignments:
            assignment_full = self.assignment_repo.get_by_id(assignment.id)
            if not assignment_full:
                continue

            remaining_days = days_to_end(assignment_full.end_date)
            item_alert = expiration_alert(assignment_full.end_date)
            is_expired = remaining_days < 0

            if is_expired:
                expired_count += 1
            if item_alert == "RED":
                red_count += 1
            elif item_alert == "AMBER":
                amber_count += 1
            else:
                green_count += 1

            if not include_expired and is_expired:
                continue
            if alert and item_alert != alert.upper():
                continue
            if not is_expired and remaining_days > days_threshold:
                continue

            items.append(
                ExpiringResourceItem(
                    assignment_id=assignment_full.id,
                    consultant_name=assignment_full.resource.consultant_name,
                    technical_profile=assignment_full.resource.technical_profile,
                    provider_name=assignment_full.provider.name,
                    main_initiative_name=assignment_full.main_initiative.name,
                    manager_name=assignment_full.manager.full_name,
                    end_date=assignment_full.end_date,
                    days_to_end=remaining_days,
                    expiration_alert=item_alert,
                    is_expired=is_expired,
                    status=assignment_full.status,
                )
            )

        return ExpiringResourcesResponse(
            items=items,
            total=len(items),
            expired_count=expired_count,
            red_count=red_count,
            amber_count=amber_count,
            green_count=green_count,
        )

    def get_budget_summary(self, current_user: AppUser) -> BudgetSummaryResponse:
        assignments = self._scoped_assignments(current_user)
        active_assignments = [a for a in assignments if a.status == "ACTIVE"]

        by_initiative: dict[str, BudgetBreakdownItem] = {}
        by_provider: dict[str, BudgetBreakdownItem] = {}
        by_manager: dict[str, BudgetBreakdownItem] = {}

        total_monthly = Decimal("0")
        total_committed = Decimal("0")

        for assignment in active_assignments:
            full = self.assignment_repo.get_by_id(assignment.id)
            if not full:
                continue

            total_monthly += full.monthly_cost_usd
            total_committed += full.total_cost_usd

            initiative_name = full.main_initiative.name
            provider_name = full.provider.name
            manager_name = full.manager.full_name

            for bucket, name in (
                (by_initiative, initiative_name),
                (by_provider, provider_name),
                (by_manager, manager_name),
            ):
                if name not in bucket:
                    bucket[name] = BudgetBreakdownItem(
                        name=name,
                        monthly_cost_usd=Decimal("0"),
                        committed_cost_usd=Decimal("0"),
                    )
                bucket[name].monthly_cost_usd += full.monthly_cost_usd
                bucket[name].committed_cost_usd += full.total_cost_usd

        return BudgetSummaryResponse(
            total_monthly_cost_usd=total_monthly,
            total_committed_cost_usd=total_committed,
            by_initiative=sorted(by_initiative.values(), key=lambda item: item.name),
            by_provider=sorted(by_provider.values(), key=lambda item: item.name),
            by_manager=sorted(by_manager.values(), key=lambda item: item.name),
        )
