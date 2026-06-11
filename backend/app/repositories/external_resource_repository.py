from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.external_resource import ExternalResource
from app.utils.string_utils import normalize_name


class ExternalResourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, resource_id: UUID) -> ExternalResource | None:
        return self.db.get(ExternalResource, resource_id)

    def get_by_consultant_name(self, consultant_name: str) -> ExternalResource | None:
        normalized = normalize_name(consultant_name).lower()
        return self.db.scalar(
            select(ExternalResource).where(func.lower(ExternalResource.consultant_name) == normalized)
        )

    def list_resources(
        self,
        search: str | None,
        technical_profile: str | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ):
        query = select(ExternalResource)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(ExternalResource.consultant_name).like(pattern),
                    func.lower(ExternalResource.technical_profile).like(pattern),
                )
            )
        if technical_profile:
            query = query.where(func.lower(ExternalResource.technical_profile) == technical_profile.lower())
        if is_active is not None:
            query = query.where(ExternalResource.is_active == is_active)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(ExternalResource.consultant_name).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return items, total

    def create(self, resource: ExternalResource) -> ExternalResource:
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource
