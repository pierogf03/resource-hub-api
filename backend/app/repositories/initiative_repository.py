from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.initiative import Initiative
from app.utils.string_utils import normalize_name


class InitiativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, initiative_id: UUID) -> Initiative | None:
        return self.db.get(Initiative, initiative_id)

    def get_by_name(self, name: str) -> Initiative | None:
        normalized = normalize_name(name).lower()
        return self.db.scalar(select(Initiative).where(func.lower(Initiative.name) == normalized))

    def list_initiatives(
        self,
        search: str | None,
        responsible_manager_id: UUID | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ):
        query = select(Initiative)
        if search:
            query = query.where(func.lower(Initiative.name).like(f"%{search.lower()}%"))
        if responsible_manager_id:
            query = query.where(Initiative.responsible_manager_id == responsible_manager_id)
        if is_active is not None:
            query = query.where(Initiative.is_active == is_active)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(Initiative.name).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return items, total

    def create(self, initiative: Initiative) -> Initiative:
        self.db.add(initiative)
        self.db.commit()
        self.db.refresh(initiative)
        return initiative

    def update(self, initiative: Initiative) -> Initiative:
        self.db.commit()
        self.db.refresh(initiative)
        return initiative