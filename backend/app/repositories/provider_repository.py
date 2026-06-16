from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.provider import Provider
from app.utils.string_utils import normalize_name


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, provider_id: UUID) -> Provider | None:
        return self.db.get(Provider, provider_id)

    def get_by_name_normalized(self, name: str) -> Provider | None:
        normalized = normalize_name(name).lower()
        return self.db.scalar(select(Provider).where(func.lower(Provider.name) == normalized))

    def list_providers(self, search: str | None, is_active: bool | None, page: int, page_size: int):
        query = select(Provider)
        if search:
            query = query.where(func.lower(Provider.name).like(f"%{search.lower()}%"))
        if is_active is not None:
            query = query.where(Provider.is_active == is_active)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(Provider.name).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return items, total

    def create(self, provider: Provider) -> Provider:
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def update(self, provider: Provider) -> Provider:
        self.db.commit()
        self.db.refresh(provider)
        return provider
