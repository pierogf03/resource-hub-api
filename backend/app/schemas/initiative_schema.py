from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InitiativeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    responsible_manager_id: UUID | None = None
    budget_usd: Decimal | None = Field(default=None, ge=0)


class InitiativeResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    responsible_manager_id: UUID | None
    budget_usd: Decimal | None
    is_active: bool

    model_config = {"from_attributes": True}
