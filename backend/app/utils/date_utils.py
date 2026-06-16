from datetime import date


def days_to_end(end_date: date, reference: date | None = None) -> int:
    today = reference or date.today()
    return (end_date - today).days


def expiration_alert(end_date: date, reference: date | None = None) -> str:
    remaining = days_to_end(end_date, reference)
    if remaining > 30:
        return "GREEN"
    if remaining >= 15:
        return "AMBER"
    return "RED"


def first_day_of_month(value: date) -> date:
    return value.replace(day=1)


def months_in_range(start_date: date, end_date: date) -> list[date]:
    months: list[date] = []
    current = first_day_of_month(start_date)
    end_month = first_day_of_month(end_date)
    while current <= end_month:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months
