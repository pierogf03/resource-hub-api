from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class InitiativeAllocationRequest(BaseModel):
    initiative_id: UUID
    allocation_percentage: Decimal = Field(gt=0, le=100)
    is_primary: bool = False
    is_funding_source: bool = False


class AssignmentCreateRequest(BaseModel):
    resource_id: UUID
    provider_id: UUID
    main_initiative_id: UUID
    manager_id: UUID
    analyst_responsible_id: UUID | None = None
    start_date: date
    end_date: date
    duration_months: int = Field(gt=0)
    monthly_cost: Decimal = Field(ge=0)
    currency: str = Field(pattern="^(USD|PEN)$")
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    comments: str | None = None
    initiatives: list[InitiativeAllocationRequest] = Field(default_factory=list)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return end_date


class AssignmentCreateResponse(BaseModel):
    id: UUID
    resource_id: UUID
    monthly_cost_usd: Decimal
    total_cost_usd: Decimal
    status: str


class AssignmentListItem(BaseModel):
    id: UUID
    consultant_name: str
    technical_profile: str
    provider_name: str
    main_initiative_name: str
    manager_name: str
    analyst_responsible_name: str | None
    start_date: date
    end_date: date
    duration_months: int
    monthly_cost: Decimal
    currency: str
    exchange_rate: Decimal | None
    monthly_cost_usd: Decimal
    total_cost_usd: Decimal
    status: str
    days_to_end: int
    expiration_alert: str
    purchase_orders_count: int


class GeneratePurchaseOrdersRequest(BaseModel):
    overwrite_existing: bool = False


class GeneratedPurchaseOrderItem(BaseModel):
    id: UUID
    period_month: date
    status: str
    amount_usd: Decimal


class GeneratePurchaseOrdersResponse(BaseModel):
    assignment_id: UUID
    generated_count: int
    skipped_count: int
    items: list[GeneratedPurchaseOrderItem]

class AssignmentUpdateRequest(BaseModel):
    resource_id: UUID | None = None
    provider_id: UUID | None = None
    main_initiative_id: UUID | None = None
    manager_id: UUID | None = None
    analyst_responsible_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_months: int | None = None
    monthly_cost: Decimal | None = None
    currency: str | None = None
    exchange_rate: Decimal | None = None
    comments: str | None = None

class AssignmentResponse(BaseModel):
    id: UUID
    resource_id: UUID
    monthly_cost_usd: Decimal
    total_cost_usd: Decimal
    status: str