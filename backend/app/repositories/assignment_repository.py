from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.external_resource import ExternalResource
from app.models.initiative import Initiative
from app.models.provider import Provider
from app.models.purchase_order import PurchaseOrder
from app.models.resource_assignment import ResourceAssignment, ResourceAssignmentInitiative
from app.models.user import AppUser


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assignment_id: UUID) -> ResourceAssignment | None:
        return self.db.scalar(
            select(ResourceAssignment)
            .options(
                joinedload(ResourceAssignment.resource),
                joinedload(ResourceAssignment.provider),
                joinedload(ResourceAssignment.main_initiative),
                joinedload(ResourceAssignment.manager),
                joinedload(ResourceAssignment.analyst_responsible),
                joinedload(ResourceAssignment.purchase_orders),
                joinedload(ResourceAssignment.initiative_allocations),
            )
            .where(ResourceAssignment.id == assignment_id)
        )

    def list_assignments(
        self,
        manager_id: UUID | None,
        analyst_id: UUID | None,
        provider_id: UUID | None,
        initiative_id: UUID | None,
        status: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ):
        query = (
            select(ResourceAssignment)
            .join(ExternalResource, ResourceAssignment.resource_id == ExternalResource.id)
            .join(Provider, ResourceAssignment.provider_id == Provider.id)
            .join(Initiative, ResourceAssignment.main_initiative_id == Initiative.id)
            .join(AppUser, ResourceAssignment.manager_id == AppUser.id)
            .options(
                joinedload(ResourceAssignment.resource),
                joinedload(ResourceAssignment.provider),
                joinedload(ResourceAssignment.main_initiative),
                joinedload(ResourceAssignment.manager),
                joinedload(ResourceAssignment.analyst_responsible),
                joinedload(ResourceAssignment.purchase_orders),
            )
        )
        if manager_id:
            query = query.where(ResourceAssignment.manager_id == manager_id)
        if analyst_id:
            query = query.where(ResourceAssignment.analyst_responsible_id == analyst_id)
        if provider_id:
            query = query.where(ResourceAssignment.provider_id == provider_id)
        if initiative_id:
            query = query.where(ResourceAssignment.main_initiative_id == initiative_id)
        if status:
            query = query.where(ResourceAssignment.status == status)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(ExternalResource.consultant_name).like(pattern),
                    func.lower(Provider.name).like(pattern),
                    func.lower(Initiative.name).like(pattern),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(ResourceAssignment.end_date).offset((page - 1) * page_size).limit(page_size)
        ).unique().all()
        return items, total

    def create(self, assignment: ResourceAssignment, allocations: list[ResourceAssignmentInitiative]) -> ResourceAssignment:
        self.db.add(assignment)
        self.db.flush()
        for allocation in allocations:
            allocation.assignment_id = assignment.id
            self.db.add(allocation)
        self.db.commit()
        return self.get_by_id(assignment.id)

    def list_for_dashboard(self, manager_id: UUID | None, analyst_id: UUID | None):
        query = select(ResourceAssignment).options(joinedload(ResourceAssignment.purchase_orders))
        if manager_id:
            query = query.where(ResourceAssignment.manager_id == manager_id)
        if analyst_id:
            query = query.where(ResourceAssignment.analyst_responsible_id == analyst_id)
        return self.db.scalars(query).unique().all()

    def count_purchase_orders(self, assignment_id: UUID) -> int:
        return self.db.scalar(
            select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.assignment_id == assignment_id)
        ) or 0

    def get_purchase_order_by_period(self, assignment_id: UUID, period_month: date) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder).where(
                PurchaseOrder.assignment_id == assignment_id,
                PurchaseOrder.period_month == period_month,
            )
        )
