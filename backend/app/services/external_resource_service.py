from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.external_resource import ExternalResource
from app.repositories.external_resource_repository import ExternalResourceRepository
from app.schemas.external_resource_schema import ExternalResourceCreateRequest
from app.utils.string_utils import normalize_name


class ExternalResourceService:
    def __init__(self, db: Session):
        self.db = db
        self.resource_repo = ExternalResourceRepository(db)

    def list_resources(
        self,
        search: str | None,
        technical_profile: str | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ):
        return self.resource_repo.list_resources(search, technical_profile, is_active, page, page_size)

    def create_resource(self, payload: ExternalResourceCreateRequest) -> ExternalResource:
        resource = ExternalResource(
            consultant_name=normalize_name(payload.consultant_name),
            technical_profile=normalize_name(payload.technical_profile),
            document_number=payload.document_number,
            is_active=True,
        )
        return self.resource_repo.create(resource)

    def get_or_create_by_name(self, consultant_name: str, technical_profile: str) -> tuple[ExternalResource, bool]:
        normalized_name = normalize_name(consultant_name)
        if not normalized_name:
            raise AppException("Consultant name is required")
        existing = self.resource_repo.get_by_consultant_name(normalized_name)
        if existing:
            return existing, False
        resource = ExternalResource(
            consultant_name=normalized_name,
            technical_profile=normalize_name(technical_profile),
            is_active=True,
        )
        return self.resource_repo.create(resource), True
