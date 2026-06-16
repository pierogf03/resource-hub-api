from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ProviderCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    ruc: str | None = Field(default=None, max_length=20)
    contact_name: str | None = Field(default=None, max_length=150)
    contact_email: EmailStr | None = None


class ProviderUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    ruc: str | None = Field(default=None, max_length=20)
    contact_name: str | None = Field(default=None, max_length=150)
    contact_email: EmailStr | None = None
    is_active: bool = True


class ProviderResponse(BaseModel):
    id: UUID
    name: str
    ruc: str | None
    contact_name: str | None
    contact_email: str | None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
