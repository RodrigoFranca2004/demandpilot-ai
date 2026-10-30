from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.forecasting.evaluation import (
    calculate_metrics,
    chronological_split,
    evaluate_model,
)


def make_history(days: int = 70) -> pd.DataFrame:
    start = date(2026, 1, 1)

    dates = [start + timedelta(days=offset) for offset in range(days)]

    weekday_demands = [20, 22, 24, 26, 28, 45, 38]

    return pd.DataFrame(
        {
            "sale_date": dates,
            "quantity": [
                weekday_demands[value.weekday()] + offset
                for offset, value in enumerate(dates)
            ],
        }
    )


def test_chronological_split_preserves_time_order() -> None:
    history = make_history(30).sample(
        frac=1,
        random_state=42,
    )

    train, test = chronological_split(history)

    assert len(train) == 24
    assert len(test) == 6
    assert train["sale_date"].max() < test["sale_date"].min()
    assert train["sale_date"].is_monotonic_increasing
    assert test["sale_date"].is_monotonic_increasing


def test_model_learns_calendar_patterns() -> None:
    results, metrics = evaluate_model(make_history())

    assert len(results) == 14
    assert metrics["mae"] == pytest.approx(0, abs=1e-8)
    assert metrics["wape"] == pytest.approx(0, abs=1e-8)
    assert (results["predicted_quantity"] >= 0).all()


def test_test_targets_do_not_affect_predictions() -> None:
    history = make_history()

    original, original_metrics = evaluate_model(history)

    modified = history.copy()

    modified.loc[
        modified.index[-14:],
        "quantity",
    ] += 500

    changed, changed_metrics = evaluate_model(modified)

    np.testing.assert_allclose(
        original["predicted_quantity"],
        changed["predicted_quantity"],
    )

    assert changed_metrics["mae"] > original_metrics["mae"]


def test_calculate_mae_and_wape() -> None:
    metrics = calculate_metrics(
        np.array([10, 20]),
        np.array([8, 25]),
    )

    assert metrics["mae"] == pytest.approx(3.5)
    assert metrics["wape"] == pytest.approx(7 / 30 * 100)


def test_wape_unavailable_when_demand_is_zero() -> None:
    metrics = calculate_metrics(
        np.array([0, 0]),
        np.array([1, 1]),
    )

    assert metrics == {
        "mae": 1.0,
        "wape": None,
    }


def test_short_history_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="14 training days",
    ):
        evaluate_model(make_history(10))


def test_invalid_test_fraction_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="test_fraction",
    ):
        chronological_split(
            make_history(),
            test_fraction=1.0,
        )
