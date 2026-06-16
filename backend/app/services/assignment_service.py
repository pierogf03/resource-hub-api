from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.purchase_order import PurchaseOrder
from app.models.resource_assignment import ResourceAssignment, ResourceAssignmentInitiative
from app.models.user import AppUser
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.external_resource_repository import ExternalResourceRepository
from app.repositories.initiative_repository import InitiativeRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.assignment_schema import (
    AssignmentCreateRequest,
    AssignmentCreateResponse,
    AssignmentListItem,
    GeneratePurchaseOrdersRequest,
    GeneratePurchaseOrdersResponse,
    GeneratedPurchaseOrderItem,
    InitiativeAllocationRequest,
)
from app.services.exchange_rate_service import resolve_pen_exchange_rate
from app.utils.date_utils import days_to_end, expiration_alert, first_day_of_month, months_in_range
from app.utils.money_utils import calculate_monthly_cost_usd, calculate_total_cost_usd
from app.utils.permission_utils import assert_assignment_access


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.resource_repo = ExternalResourceRepository(db)
        self.provider_repo = ProviderRepository(db)
        self.initiative_repo = InitiativeRepository(db)
        self.user_repo = UserRepository(db)

    def _role_filters(self, current_user: AppUser, manager_id: UUID | None) -> tuple[UUID | None, UUID | None]:
        if current_user.role == "ADMIN":
            return manager_id, None
        if current_user.role == "MANAGER":
            return current_user.id, None
        return None, current_user.id

    def list_assignments(
        self,
        current_user: AppUser,
        manager_id: UUID | None,
        provider_id: UUID | None,
        initiative_id: UUID | None,
        status: str | None,
        alert: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ):
        effective_manager_id, analyst_id = self._role_filters(current_user, manager_id)
        items, total = self.assignment_repo.list_assignments(
            effective_manager_id,
            analyst_id,
            provider_id,
            initiative_id,
            status,
            search,
            page,
            page_size,
        )

        result: list[AssignmentListItem] = []
        for item in items:
            item_alert = expiration_alert(item.end_date)
            if alert and item_alert != alert.upper():
                continue
            result.append(
                AssignmentListItem(
                    id=item.id,
                    consultant_name=item.resource.consultant_name,
                    technical_profile=item.resource.technical_profile,
                    provider_name=item.provider.name,
                    main_initiative_name=item.main_initiative.name,
                    manager_name=item.manager.full_name,
                    analyst_responsible_name=item.analyst_responsible.full_name if item.analyst_responsible else None,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    duration_months=item.duration_months,
                    monthly_cost=item.monthly_cost,
                    currency=item.currency,
                    exchange_rate=item.exchange_rate,
                    monthly_cost_usd=item.monthly_cost_usd,
                    total_cost_usd=item.total_cost_usd,
                    status=item.status,
                    days_to_end=days_to_end(item.end_date),
                    expiration_alert=item_alert,
                    purchase_orders_count=len(item.purchase_orders),
                )
            )
        if alert:
            total = len(result)
        return result, total

    def get_assignment_detail(self, assignment_id: UUID, current_user: AppUser) -> AssignmentListItem:
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise AppException("Assignment not found", status_code=404)
        assert_assignment_access(assignment, current_user)
        return AssignmentListItem(
            id=assignment.id,
            consultant_name=assignment.resource.consultant_name,
            technical_profile=assignment.resource.technical_profile,
            provider_name=assignment.provider.name,
            main_initiative_name=assignment.main_initiative.name,
            manager_name=assignment.manager.full_name,
            analyst_responsible_name=assignment.analyst_responsible.full_name
            if assignment.analyst_responsible
            else None,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            duration_months=assignment.duration_months,
            monthly_cost=assignment.monthly_cost,
            currency=assignment.currency,
            exchange_rate=assignment.exchange_rate,
            monthly_cost_usd=assignment.monthly_cost_usd,
            total_cost_usd=assignment.total_cost_usd,
            status=assignment.status,
            days_to_end=days_to_end(assignment.end_date),
            expiration_alert=expiration_alert(assignment.end_date),
            purchase_orders_count=len(assignment.purchase_orders),
        )

    def _validate_allocations(self, payload: AssignmentCreateRequest) -> list[ResourceAssignmentInitiative]:
        allocations_data: list[InitiativeAllocationRequest] = payload.initiatives or [
            InitiativeAllocationRequest(
                initiative_id=payload.main_initiative_id,
                allocation_percentage=Decimal("100"),
                is_primary=True,
                is_funding_source=True,
            )
        ]
        total_percentage = sum(item.allocation_percentage for item in allocations_data)
        if total_percentage > Decimal("100"):
            raise AppException("Total allocation percentage cannot exceed 100")
        primary_count = sum(1 for item in allocations_data if item.is_primary)
        funding_count = sum(1 for item in allocations_data if item.is_funding_source)
        if primary_count != 1:
            raise AppException("Exactly one primary initiative is required")
        if funding_count != 1:
            raise AppException("Exactly one funding source initiative is required")
        allocations: list[ResourceAssignmentInitiative] = []
        for item in allocations_data:
            if not self.initiative_repo.get_by_id(item.initiative_id):
                raise AppException("Initiative not found in allocations", status_code=404)
            allocations.append(
                ResourceAssignmentInitiative(
                    initiative_id=item.initiative_id,
                    allocation_percentage=item.allocation_percentage,
                    is_primary=item.is_primary,
                    is_funding_source=item.is_funding_source,
                )
            )
        return allocations

    def create_assignment(self, payload: AssignmentCreateRequest) -> AssignmentCreateResponse:
        if not self.resource_repo.get_by_id(payload.resource_id):
            raise AppException("External resource not found", status_code=404)
        if not self.provider_repo.get_by_id(payload.provider_id):
            raise AppException("Provider not found", status_code=404)
        if not self.initiative_repo.get_by_id(payload.main_initiative_id):
            raise AppException("Initiative not found", status_code=404)
        manager = self.user_repo.get_by_id(payload.manager_id)
        if not manager:
            raise AppException("Manager not found", status_code=404)
        if manager.role not in {"MANAGER", "ADMIN"}:
            raise AppException("Manager must have MANAGER or ADMIN role")
        if payload.analyst_responsible_id and not self.user_repo.get_by_id(payload.analyst_responsible_id):
            raise AppException("Analyst responsible not found", status_code=404)

        exchange_rate = (
            resolve_pen_exchange_rate(payload.exchange_rate) if payload.currency == "PEN" else None
        )
        monthly_cost_usd = calculate_monthly_cost_usd(payload.monthly_cost, payload.currency, exchange_rate)
        total_cost_usd = calculate_total_cost_usd(monthly_cost_usd, payload.duration_months)
        allocations = self._validate_allocations(payload)

        assignment = ResourceAssignment(
            resource_id=payload.resource_id,
            provider_id=payload.provider_id,
            main_initiative_id=payload.main_initiative_id,
            manager_id=payload.manager_id,
            analyst_responsible_id=payload.analyst_responsible_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            duration_months=payload.duration_months,
            monthly_cost=payload.monthly_cost,
            currency=payload.currency,
            exchange_rate=exchange_rate,
            monthly_cost_usd=monthly_cost_usd,
            total_cost_usd=total_cost_usd,
            status="ACTIVE",
            comments=payload.comments,
        )
        created = self.assignment_repo.create(assignment, allocations)
        return AssignmentCreateResponse(
            id=created.id,
            resource_id=created.resource_id,
            monthly_cost_usd=created.monthly_cost_usd,
            total_cost_usd=created.total_cost_usd,
            status=created.status,
        )

    def generate_monthly_purchase_orders(
        self,
        assignment_id: UUID,
        payload: GeneratePurchaseOrdersRequest,
        current_user: AppUser | None = None,
    ) -> GeneratePurchaseOrdersResponse:
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise AppException("Assignment not found", status_code=404)
        if current_user is not None:
            assert_assignment_access(assignment, current_user)

        generated: list[GeneratedPurchaseOrderItem] = []
        skipped_count = 0
        for period_month in months_in_range(assignment.start_date, assignment.end_date):
            period_month = first_day_of_month(period_month)
            existing = self.assignment_repo.get_purchase_order_by_period(assignment.id, period_month)
            if existing:
                if payload.overwrite_existing:
                    self.db.delete(existing)
                    self.db.commit()
                else:
                    skipped_count += 1
                    continue
            amount_usd = calculate_monthly_cost_usd(
                assignment.monthly_cost, assignment.currency, assignment.exchange_rate
            )
            purchase_order = PurchaseOrder(
                assignment_id=assignment.id,
                provider_id=assignment.provider_id,
                period_month=period_month,
                status="PENDING",
                amount=assignment.monthly_cost,
                currency=assignment.currency,
                exchange_rate=assignment.exchange_rate,
                amount_usd=amount_usd,
            )
            self.db.add(purchase_order)
            self.db.commit()
            self.db.refresh(purchase_order)
            generated.append(
                GeneratedPurchaseOrderItem(
                    id=purchase_order.id,
                    period_month=purchase_order.period_month,
                    status=purchase_order.status,
                    amount_usd=purchase_order.amount_usd,
                )
            )
        return GeneratePurchaseOrdersResponse(
            assignment_id=assignment.id,
            generated_count=len(generated),
            skipped_count=skipped_count,
            items=generated,
        )
