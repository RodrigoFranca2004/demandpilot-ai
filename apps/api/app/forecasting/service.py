from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.core.planning import DEFAULT_FORECAST_HORIZON
from app.forecasting.baseline import predict_baseline
from app.forecasting.data import load_sales_history
from app.forecasting.evaluation import (
    calculate_metrics,
    chronological_split,
    evaluate_model,
)
from app.forecasting.model import predict_demand, train_demand_model


@dataclass(frozen=True)
class ForecastPoint:
    sale_date: date
    predicted_quantity: float


@dataclass(frozen=True)
class ForecastReport:
    product_id: int
    selected_method: str
    history_end_date: date
    evaluation_start_date: date
    evaluation_end_date: date
    baseline_metrics: dict[str, float | None]
    regression_metrics: dict[str, float | None]
    forecast: list[ForecastPoint]


def forecast_product_demand(
    session: Session,
    product_id: int,
    horizon: int = DEFAULT_FORECAST_HORIZON,
) -> ForecastReport:
    if horizon < 1:
        raise ValueError("Forecast horizon must be positive")

    history = load_sales_history(session, product_id)

    if history.empty:
        raise ValueError(f"No sales history found for product {product_id}")

    train, test = chronological_split(history)

    _, regression_metrics = evaluate_model(history)

    baseline_test = predict_baseline(
        train,
        horizon=len(test),
    )

    baseline_metrics = calculate_metrics(
        test["quantity"],
        baseline_test["predicted_quantity"],
    )

    selected_method = (
        "linear_regression"
        if regression_metrics["mae"] < baseline_metrics["mae"]
        else "moving_average_7"
    )

    history_end = pd.Timestamp(history["sale_date"].max()).date()

    future_dates = pd.Series(
        pd.date_range(
            start=history_end + timedelta(days=1),
            periods=horizon,
            freq="D",
        ).date
    )

    if selected_method == "linear_regression":
        model, reference_date = train_demand_model(history)

        quantities = predict_demand(
            model,
            reference_date,
            future_dates,
        )
    else:
        quantities = predict_baseline(
            history,
            horizon=horizon,
        )["predicted_quantity"].to_numpy()

    forecast = [
        ForecastPoint(
            sale_date=sale_date,
            predicted_quantity=float(quantity),
        )
        for sale_date, quantity in zip(
            future_dates,
            quantities,
            strict=True,
        )
    ]

    return ForecastReport(
        product_id=product_id,
        selected_method=selected_method,
        history_end_date=history_end,
        evaluation_start_date=pd.Timestamp(test["sale_date"].iloc[0]).date(),
        evaluation_end_date=pd.Timestamp(test["sale_date"].iloc[-1]).date(),
        baseline_metrics=baseline_metrics,
        regression_metrics=regression_metrics,
        forecast=forecast,
    )
