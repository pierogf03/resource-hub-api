from decimal import Decimal

from app.core.exceptions import AppException


def calculate_monthly_cost_usd(monthly_cost: Decimal, currency: str, exchange_rate: Decimal | None) -> Decimal:
    if currency == "USD":
        return monthly_cost
    if currency == "PEN":
        if exchange_rate is None or exchange_rate <= 0:
            raise AppException("Exchange rate is required and must be greater than 0 for PEN currency")
        return (monthly_cost / exchange_rate).quantize(Decimal("0.01"))
    raise AppException(f"Invalid currency: {currency}")


def calculate_total_cost_usd(monthly_cost_usd: Decimal, duration_months: int) -> Decimal:
    return (monthly_cost_usd * duration_months).quantize(Decimal("0.01"))


def calculate_amount_usd(amount: Decimal, currency: str, exchange_rate: Decimal | None) -> Decimal:
    return calculate_monthly_cost_usd(amount, currency, exchange_rate)
