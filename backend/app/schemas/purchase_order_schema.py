from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PurchaseOrderCreateRequest(BaseModel):
    assignment_id: UUID
    period_month: date
    po_number: str | None = Field(default=None, max_length=80)
    status: str = Field(default="PENDING", pattern="^(PENDING|COUPA_GENERATED|SENT|APPROVED|CLOSED|CANCELLED)$")
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern="^(USD|PEN)$")
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    comments: str | None = None


class PurchaseOrderUpdateRequest(BaseModel):
    po_number: str | None = Field(default=None, max_length=80)
    status: str = Field(pattern="^(PENDING|COUPA_GENERATED|SENT|APPROVED|CLOSED|CANCELLED)$")
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern="^(USD|PEN)$")
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    comments: str | None = None


class PurchaseOrderResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    consultant_name: str | None = None
    provider_name: str | None = None
    period_month: date
    po_number: str | None
    status: str
    amount: Decimal
    currency: str
    exchange_rate: Decimal | None
    amount_usd: Decimal
    comments: str | None

    model_config = {"from_attributes": True}


class PurchaseOrderCreateResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    period_month: date
    po_number: str | None
    status: str
    amount_usd: Decimal
