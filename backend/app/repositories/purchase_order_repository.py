from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.external_resource import ExternalResource
from app.models.provider import Provider
from app.models.purchase_order import PurchaseOrder
from app.models.resource_assignment import ResourceAssignment


class PurchaseOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, purchase_order_id: UUID) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.assignment).joinedload(ResourceAssignment.resource),
                joinedload(PurchaseOrder.provider),
            )
            .where(PurchaseOrder.id == purchase_order_id)
        )

    def list_purchase_orders(
        self,
        assignment_id: UUID | None,
        provider_id: UUID | None,
        status: str | None,
        period_from: date | None,
        period_to: date | None,
        manager_id: UUID | None,
        analyst_id: UUID | None,
        page: int,
        page_size: int,
    ):
        query = (
            select(PurchaseOrder)
            .join(ResourceAssignment, PurchaseOrder.assignment_id == ResourceAssignment.id)
            .join(ExternalResource, ResourceAssignment.resource_id == ExternalResource.id)
            .join(Provider, PurchaseOrder.provider_id == Provider.id)
            .options(
                joinedload(PurchaseOrder.assignment).joinedload(ResourceAssignment.resource),
                joinedload(PurchaseOrder.provider),
            )
        )
        if assignment_id:
            query = query.where(PurchaseOrder.assignment_id == assignment_id)
        if provider_id:
            query = query.where(PurchaseOrder.provider_id == provider_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
        if period_from:
            query = query.where(PurchaseOrder.period_month >= period_from)
        if period_to:
            query = query.where(PurchaseOrder.period_month <= period_to)
        if manager_id:
            query = query.where(ResourceAssignment.manager_id == manager_id)
        if analyst_id:
            query = query.where(ResourceAssignment.analyst_responsible_id == analyst_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(PurchaseOrder.period_month.desc()).offset((page - 1) * page_size).limit(page_size)
        ).unique().all()
        return items, total

    def create(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        self.db.add(purchase_order)
        self.db.commit()
        self.db.refresh(purchase_order)
        return purchase_order

    def update(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        self.db.commit()
        self.db.refresh(purchase_order)
        return purchase_order

    def list_for_assignments(self, assignment_ids: list[UUID]) -> list[PurchaseOrder]:
        if not assignment_ids:
            return []
        return self.db.scalars(select(PurchaseOrder).where(PurchaseOrder.assignment_id.in_(assignment_ids))).all()
