from decimal import Decimal

import httpx
from fastapi import status

from app.core.exceptions import AppException

EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"


def _parse_rate_response(data: dict) -> dict:
    rates = data.get("rates") or {}
    pen_rate = rates.get("PEN")
    if pen_rate is None:
        raise AppException("PEN exchange rate not available", status_code=status.HTTP_502_BAD_GATEWAY)
    return {
        "base": "USD",
        "target": "PEN",
        "rate": Decimal(str(pen_rate)),
        "source": "ExchangeRate-API",
        "updated_at": data.get("time_last_update_utc"),
    }


def _fetch_rate_data_sync(client: httpx.Client) -> dict:
    try:
        response = client.get(EXCHANGE_RATE_API_URL)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise AppException(
            "Failed to fetch exchange rate from external API",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    except httpx.RequestError as exc:
        raise AppException(
            "Exchange rate service is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc


async def _fetch_rate_data_async(client: httpx.AsyncClient) -> dict:
    try:
        response = await client.get(EXCHANGE_RATE_API_URL)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise AppException(
            "Failed to fetch exchange rate from external API",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    except httpx.RequestError as exc:
        raise AppException(
            "Exchange rate service is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc


async def get_usd_to_pen_rate() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        data = await _fetch_rate_data_async(client)
    return _parse_rate_response(data)


def get_usd_to_pen_rate_sync() -> dict:
    with httpx.Client(timeout=10) as client:
        data = _fetch_rate_data_sync(client)
    return _parse_rate_response(data)


def resolve_pen_exchange_rate(exchange_rate: Decimal | None) -> Decimal:
    if exchange_rate is not None and exchange_rate > 0:
        return exchange_rate
    return get_usd_to_pen_rate_sync()["rate"]
