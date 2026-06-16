from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class BudgetBreakdownItem(BaseModel):
    name: str
    monthly_cost_usd: Decimal
    committed_cost_usd: Decimal


class BudgetSummaryResponse(BaseModel):
    total_monthly_cost_usd: Decimal
    total_committed_cost_usd: Decimal
    by_initiative: list[BudgetBreakdownItem] = []
    by_provider: list[BudgetBreakdownItem] = []
    by_manager: list[BudgetBreakdownItem] = []


class PurchaseOrderStatusSummary(BaseModel):
    total: int
    pending: int
    coupa_generated: int
    sent: int
    approved: int
    closed: int


class ExpirationAlertSummary(BaseModel):
    green: int
    amber: int
    red: int


class DashboardSummaryResponse(BaseModel):
    total_assignments: int
    active_assignments: int
    expiring_soon: int
    expired: int
    total_monthly_cost_usd: Decimal
    total_committed_cost_usd: Decimal
    purchase_orders: PurchaseOrderStatusSummary
    expiration_alerts: ExpirationAlertSummary


class ExpiringResourceItem(BaseModel):
    assignment_id: UUID
    consultant_name: str
    technical_profile: str
    provider_name: str
    main_initiative_name: str
    manager_name: str
    end_date: date
    days_to_end: int
    expiration_alert: str
    is_expired: bool
    status: str


class ExpiringResourcesResponse(BaseModel):
    items: list[ExpiringResourceItem]
    total: int
    expired_count: int
    red_count: int
    amber_count: int
    green_count: int
