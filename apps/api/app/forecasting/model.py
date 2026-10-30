from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def build_calendar_features(
    dates: pd.Series,
    reference_date: date,
) -> pd.DataFrame:
    parsed_dates = pd.to_datetime(dates)

    features = pd.DataFrame(
        {
            "day_index": (parsed_dates - pd.Timestamp(reference_date)).dt.days,
        },
        index=dates.index,
    )

    for weekday in range(1, 7):
        features[f"weekday_{weekday}"] = (parsed_dates.dt.weekday == weekday).astype(
            int
        )

    return features


def train_demand_model(
    history: pd.DataFrame,
) -> tuple[LinearRegression, date]:
    if len(history) < 14:
        raise ValueError("At least 14 days of training data are required")

    reference_date = pd.Timestamp(history["sale_date"].min()).date()

    features = build_calendar_features(
        history["sale_date"],
        reference_date,
    )

    model = LinearRegression()
    model.fit(features, history["quantity"])

    return model, reference_date


def predict_demand(
    model: LinearRegression,
    reference_date: date,
    dates: pd.Series,
) -> np.ndarray:
    features = build_calendar_features(
        dates,
        reference_date,
    )

    return np.maximum(
        model.predict(features),
        0.0,
    )
