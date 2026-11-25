from datetime import date

from pydantic import BaseModel


class DemoSettingsResponse(BaseModel):
    restaurant_id: int | None
    planning_date: date
    forecast_horizon: int
    inventory_horizon: int
    refresh_enabled: bool


class DemoRefreshResponse(BaseModel):
    planning_date: date
    added_sales: int
