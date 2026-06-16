from decimal import Decimal

from pydantic import BaseModel


class ExchangeRateResponse(BaseModel):
    base: str
    target: str
    rate: Decimal
    source: str
    updated_at: str | None = None
