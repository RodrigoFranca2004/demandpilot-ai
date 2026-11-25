from datetime import date, datetime
from zoneinfo import ZoneInfo

DEFAULT_FORECAST_HORIZON = 7
DEFAULT_INVENTORY_HORIZON = 1
BUSINESS_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def planning_today() -> date:
    return datetime.now(BUSINESS_TIMEZONE).date()
