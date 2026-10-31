from datetime import date

from pydantic import BaseModel, ConfigDict


class ForecastPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_date: date
    predicted_quantity: float


class ModelMetricsResponse(BaseModel):
    mae: float
    wape: float | None


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    selected_method: str
    history_end_date: date
    forecast: list[ForecastPointResponse]


class ForecastMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    selected_method: str
    evaluation_start_date: date
    evaluation_end_date: date
    baseline_metrics: ModelMetricsResponse
    regression_metrics: ModelMetricsResponse
