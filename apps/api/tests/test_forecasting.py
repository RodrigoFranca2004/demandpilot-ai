from datetime import date, timedelta

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.forecasting.baseline import predict_baseline
from app.forecasting.data import load_sales_history
from app.models import Base, DailySale, Product, Restaurant


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            restaurant = Restaurant(name="Test Restaurant")
            session.add(restaurant)
            session.flush()

            product = Product(
                restaurant_id=restaurant.id,
                name="Classic Burger",
            )
            session.add(product)
            session.flush()

            session.add_all(
                [
                    DailySale(
                        product_id=product.id,
                        sale_date=date(2026, 1, 3),
                        quantity=30,
                    ),
                    DailySale(
                        product_id=product.id,
                        sale_date=date(2026, 1, 1),
                        quantity=10,
                    ),
                    DailySale(
                        product_id=product.id,
                        sale_date=date(2026, 1, 2),
                        quantity=20,
                    ),
                ]
            )

            session.flush()
            yield session
    finally:
        engine.dispose()


def test_load_sales_history_is_chronological(
    db_session: Session,
) -> None:
    history = load_sales_history(db_session, product_id=1)

    assert history["sale_date"].tolist() == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]

    assert history["quantity"].tolist() == [10, 20, 30]


def test_load_sales_history_returns_empty_dataframe(
    db_session: Session,
) -> None:
    history = load_sales_history(db_session, product_id=999)

    assert history.empty
    assert history.columns.tolist() == [
        "sale_date",
        "quantity",
    ]


def test_baseline_uses_recent_observations() -> None:
    start_date = date(2026, 1, 1)

    history = pd.DataFrame(
        {
            "sale_date": [start_date + timedelta(days=i) for i in range(7)],
            "quantity": [10, 12, 14, 16, 18, 20, 22],
        }
    )

    forecast = predict_baseline(
        history,
        horizon=2,
        window=3,
    )

    assert forecast["sale_date"].tolist() == [
        date(2026, 1, 8),
        date(2026, 1, 9),
    ]

    assert forecast["predicted_quantity"].tolist() == [
        20.0,
        20.0,
    ]


def test_baseline_rejects_empty_history() -> None:
    history = pd.DataFrame(columns=["sale_date", "quantity"])

    with pytest.raises(ValueError):
        predict_baseline(history)


@pytest.mark.parametrize(
    ("horizon", "window"),
    [
        (0, 7),
        (1, 0),
    ],
)
def test_baseline_rejects_invalid_parameters(
    horizon: int,
    window: int,
) -> None:
    history = pd.DataFrame(
        {
            "sale_date": [date(2026, 1, 1)],
            "quantity": [10],
        }
    )

    with pytest.raises(ValueError):
        predict_baseline(
            history,
            horizon=horizon,
            window=window,
        )
