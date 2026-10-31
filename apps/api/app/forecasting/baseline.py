import pandas as pd


def predict_baseline(
    history: pd.DataFrame,
    horizon: int = 1,
    window: int = 7,
) -> pd.DataFrame:
    if history.empty:
        raise ValueError("Sales history cannot be empty")

    if horizon < 1:
        raise ValueError("Forecast horizon must be positive")

    if window < 1:
        raise ValueError("Baseline window must be positive")

    history = history.sort_values("sale_date")

    average_demand = float(history["quantity"].tail(window).mean())

    last_date = pd.Timestamp(history["sale_date"].iloc[-1])

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )

    return pd.DataFrame(
        {
            "sale_date": future_dates.date,
            "predicted_quantity": [average_demand] * horizon,
        }
    )
