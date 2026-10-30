from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from app.forecasting.baseline import predict_baseline
from app.forecasting.data import load_sales_history
from app.forecasting.evaluation import (
    calculate_metrics,
    chronological_split,
)
from app.forecasting.service import forecast_product_demand
from app.models import Base, DailySale, Product, Restaurant


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            restaurant = Restaurant(name="Test Restaurant")
            session.add(restaurant)
            session.flush()

            product = Product(
                name="Classic Burger",
                restaurant_id=restaurant.id,
            )
            session.add(product)
            session.flush()

            start_date = date(2026, 1, 1)

            for offset in range(70):
                sale_date = start_date + timedelta(days=offset)

                quantity = 20 + offset + (15 if sale_date.weekday() >= 5 else 0)

                session.add(
                    DailySale(
                        product_id=product.id,
                        sale_date=sale_date,
                        quantity=quantity,
                    )
                )

            session.commit()
            yield session
    finally:
        engine.dispose()


def test_forecast_selects_regression(
    db_session: Session,
) -> None:
    report = forecast_product_demand(
        db_session,
        product_id=1,
        horizon=3,
    )

    assert report.selected_method == "linear_regression"

    assert report.regression_metrics["mae"] == pytest.approx(
        0,
        abs=1e-8,
    )

    assert report.regression_metrics["mae"] < report.baseline_metrics["mae"]

    assert len(report.forecast) == 3

    assert report.forecast[0].sale_date == date(2026, 1, 1) + timedelta(days=70)

    assert all(point.predicted_quantity >= 0 for point in report.forecast)


def test_baseline_uses_training_period_only(
    db_session: Session,
) -> None:
    report = forecast_product_demand(
        db_session,
        product_id=1,
    )

    history = load_sales_history(db_session, product_id=1)
    train, test = chronological_split(history)

    baseline_predictions = predict_baseline(
        train,
        horizon=len(test),
    )

    expected_metrics = calculate_metrics(
        test["quantity"],
        baseline_predictions["predicted_quantity"],
    )

    assert report.baseline_metrics == expected_metrics

    assert report.evaluation_start_date == test["sale_date"].iloc[0]

    assert report.evaluation_end_date == test["sale_date"].iloc[-1]


def test_forecast_selects_baseline_for_constant_sales(
    db_session: Session,
) -> None:
    db_session.execute(update(DailySale).values(quantity=30))
    db_session.commit()

    report = forecast_product_demand(
        db_session,
        product_id=1,
        horizon=2,
    )

    assert report.selected_method == "moving_average_7"

    assert [point.predicted_quantity for point in report.forecast] == [30.0, 30.0]


def test_forecast_rejects_missing_history(
    db_session: Session,
) -> None:
    with pytest.raises(
        ValueError,
        match="No sales history",
    ):
        forecast_product_demand(
            db_session,
            product_id=999,
        )


def test_forecast_rejects_invalid_horizon(
    db_session: Session,
) -> None:
    with pytest.raises(
        ValueError,
        match="Forecast horizon must be positive",
    ):
        forecast_product_demand(
            db_session,
            product_id=1,
            horizon=0,
        )
