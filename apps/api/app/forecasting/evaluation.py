import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

from app.forecasting.model import predict_demand, train_demand_model


def chronological_split(
    history: pd.DataFrame,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")

    ordered = history.sort_values("sale_date").reset_index(drop=True)

    split_index = int(len(ordered) * (1 - test_fraction))

    if split_index < 14 or split_index >= len(ordered):
        raise ValueError("At least 14 training days and 1 test day are required")

    return (
        ordered.iloc[:split_index].copy(),
        ordered.iloc[split_index:].copy(),
    )


def calculate_metrics(
    actual: pd.Series | np.ndarray,
    predicted: pd.Series | np.ndarray,
) -> dict[str, float | None]:
    actual_values = np.asarray(
        actual,
        dtype=float,
    )
    predicted_values = np.asarray(
        predicted,
        dtype=float,
    )

    mae = float(
        mean_absolute_error(
            actual_values,
            predicted_values,
        )
    )

    total_demand = float(np.abs(actual_values).sum())

    wape = (
        float(np.abs(actual_values - predicted_values).sum() / total_demand * 100)
        if total_demand > 0
        else None
    )

    return {
        "mae": mae,
        "wape": wape,
    }


def evaluate_model(
    history: pd.DataFrame,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, dict[str, float | None]]:
    train, test = chronological_split(
        history,
        test_fraction,
    )

    model, reference_date = train_demand_model(train)

    predicted = predict_demand(
        model,
        reference_date,
        test["sale_date"],
    )

    results = pd.DataFrame(
        {
            "sale_date": test["sale_date"].to_list(),
            "actual_quantity": test["quantity"].to_list(),
            "predicted_quantity": predicted,
        }
    )

    return results, calculate_metrics(
        test["quantity"],
        predicted,
    )
