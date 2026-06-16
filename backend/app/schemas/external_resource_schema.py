from uuid import UUID

from pydantic import BaseModel, Field


class ExternalResourceCreateRequest(BaseModel):
    consultant_name: str = Field(min_length=1, max_length=150)
    technical_profile: str = Field(min_length=1, max_length=100)
    document_number: str | None = Field(default=None, max_length=30)


class ExternalResourceResponse(BaseModel):
    id: UUID
    consultant_name: str
    technical_profile: str
    document_number: str | None
    is_active: bool

    model_config = {"from_attributes": True}

class ExternalResourceUpdateRequest(BaseModel):
    consultant_name: str = Field(min_length=1, max_length=150)
    technical_profile: str = Field(min_length=1, max_length=100)
    document_number: str | None = Field(default=None, max_length=30)
    is_active: bool = True