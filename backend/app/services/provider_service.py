from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.provider import Provider
from app.repositories.provider_repository import ProviderRepository
from app.schemas.provider_schema import ProviderCreateRequest, ProviderUpdateRequest
from app.utils.string_utils import normalize_name


class ProviderService:
    def __init__(self, db: Session):
        self.db = db
        self.provider_repo = ProviderRepository(db)

    def list_providers(self, search: str | None, is_active: bool | None, page: int, page_size: int):
        return self.provider_repo.list_providers(search, is_active, page, page_size)

    def create_provider(self, payload: ProviderCreateRequest) -> Provider:
        normalized_name = normalize_name(payload.name)
        existing = self.provider_repo.get_by_name_normalized(normalized_name)
        if existing:
            raise AppException(
                "Provider already exists",
                errors=[{"field": "name", "message": "Provider with this name already exists"}],
            )
        provider = Provider(
            name=normalized_name,
            ruc=payload.ruc,
            contact_name=payload.contact_name,
            contact_email=str(payload.contact_email) if payload.contact_email else None,
            is_active=True,
        )
        return self.provider_repo.create(provider)

    def update_provider(self, provider_id: UUID, payload: ProviderUpdateRequest) -> Provider:
        provider = self.provider_repo.get_by_id(provider_id)
        if not provider:
            raise AppException("Provider not found", status_code=404)
        normalized_name = normalize_name(payload.name)
        existing = self.provider_repo.get_by_name_normalized(normalized_name)
        if existing and existing.id != provider_id:
            raise AppException(
                "Provider already exists",
                errors=[{"field": "name", "message": "Provider with this name already exists"}],
            )
        provider.name = normalized_name
        provider.ruc = payload.ruc
        provider.contact_name = payload.contact_name
        provider.contact_email = str(payload.contact_email) if payload.contact_email else None
        provider.is_active = payload.is_active
        return self.provider_repo.update(provider)

    def get_or_create_by_name(self, name: str) -> tuple[Provider, bool]:
        normalized_name = normalize_name(name)
        if not normalized_name:
            raise AppException("Provider name is required")
        existing = self.provider_repo.get_by_name_normalized(normalized_name)
        if existing:
            return existing, False
        provider = Provider(name=normalized_name, is_active=True)
        return self.provider_repo.create(provider), True
