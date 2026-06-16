from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import AppUser
from app.schemas.common_schema import success_response
from app.schemas.exchange_rate_schema import ExchangeRateResponse
from app.services.exchange_rate_service import get_usd_to_pen_rate

router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])


@router.get("/usd-pen")
async def get_usd_pen_exchange_rate(
    _: Annotated[AppUser, Depends(get_current_user)],
):
    rate_data = await get_usd_to_pen_rate()
    data = ExchangeRateResponse.model_validate(rate_data).model_dump(mode="json")
    return success_response("USD to PEN exchange rate retrieved successfully", data)
