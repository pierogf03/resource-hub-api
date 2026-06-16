from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.initiative import Initiative
from app.repositories.initiative_repository import InitiativeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.initiative_schema import InitiativeCreateRequest
from app.utils.string_utils import normalize_name


class InitiativeService:
    def __init__(self, db: Session):
        self.db = db
        self.initiative_repo = InitiativeRepository(db)
        self.user_repo = UserRepository(db)

    def list_initiatives(
        self,
        search: str | None,
        responsible_manager_id: UUID | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ):
        return self.initiative_repo.list_initiatives(search, responsible_manager_id, is_active, page, page_size)

    def create_initiative(self, payload: InitiativeCreateRequest) -> Initiative:
        normalized_name = normalize_name(payload.name)
        if self.initiative_repo.get_by_name(normalized_name):
            raise AppException(
                "Initiative already exists",
                errors=[{"field": "name", "message": "Initiative with this name already exists"}],
            )
        if payload.responsible_manager_id and not self.user_repo.get_by_id(payload.responsible_manager_id):
            raise AppException("Responsible manager not found", status_code=404)
        initiative = Initiative(
            name=normalized_name,
            description=payload.description,
            responsible_manager_id=payload.responsible_manager_id,
            budget_usd=payload.budget_usd,
            is_active=True,
        )
        return self.initiative_repo.create(initiative)

    def get_or_create_by_name(self, name: str) -> tuple[Initiative, bool]:
        normalized_name = normalize_name(name)
        if not normalized_name:
            raise AppException("Initiative name is required")
        existing = self.initiative_repo.get_by_name(normalized_name)
        if existing:
            return existing, False
        initiative = Initiative(name=normalized_name, is_active=True)
        return self.initiative_repo.create(initiative), True

    def update_initiative(self, initiative_id: UUID, payload: InitiativeCreateRequest) -> Initiative:
        initiative = self.initiative_repo.get_by_id(initiative_id)
        if not initiative:
            raise AppException("Initiative not found")
        initiative.name = normalize_name(payload.name)
        existing = self.initiative_repo.get_by_name(initiative.name)
        if existing and existing.id != initiative_id:
            raise AppException(
                "Initiative already exists",
                errors=[{"field": "name", "message": "Initiative with this name already exists"}],
            )
        initiative.description = payload.description
        initiative.responsible_manager_id = payload.responsible_manager_id
        initiative.budget_usd = payload.budget_usd
        return self.initiative_repo.update(initiative)