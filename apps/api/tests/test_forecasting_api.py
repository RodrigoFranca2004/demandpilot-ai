from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, DailySale, Product, Restaurant


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            restaurant = Restaurant(
                id=1,
                name="Test Restaurant",
            )

            products = [
                Product(
                    id=1,
                    restaurant_id=1,
                    name="Classic Burger",
                ),
                Product(
                    id=2,
                    restaurant_id=1,
                    name="French Fries",
                ),
            ]

            session.add(restaurant)
            session.add_all(products)

            start_date = date(2026, 1, 1)

            for offset in range(70):
                sale_date = start_date + timedelta(days=offset)

                quantity = 20 + offset + (15 if sale_date.weekday() >= 5 else 0)

                session.add(
                    DailySale(
                        product_id=1,
                        sale_date=sale_date,
                        quantity=quantity,
                    )
                )

            session.commit()

        def override_get_db() -> Iterator[Session]:
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.pop(get_db, None)
    finally:
        engine.dispose()


def test_get_forecast_with_default_horizon(
    client: TestClient,
) -> None:
    response = client.get("/products/1/forecast")

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == 1
    assert data["selected_method"] == "linear_regression"
    assert data["history_end_date"] == "2026-03-11"
    assert len(data["forecast"]) == 7

    assert data["forecast"][0]["sale_date"] == "2026-03-12"

    assert all(point["predicted_quantity"] >= 0 for point in data["forecast"])


def test_get_forecast_with_custom_horizon(
    client: TestClient,
) -> None:
    response = client.get(
        "/products/1/forecast",
        params={"horizon": 3},
    )

    assert response.status_code == 200

    forecast = response.json()["forecast"]

    assert len(forecast) == 3
    assert [point["sale_date"] for point in forecast] == [
        "2026-03-12",
        "2026-03-13",
        "2026-03-14",
    ]


def test_get_forecast_metrics(
    client: TestClient,
) -> None:
    response = client.get("/products/1/forecast/metrics")

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == 1
    assert data["selected_method"] == "linear_regression"
    assert data["evaluation_start_date"] == "2026-02-26"
    assert data["evaluation_end_date"] == "2026-03-11"

    assert data["regression_metrics"]["mae"] == pytest.approx(
        0,
        abs=1e-8,
    )

    assert data["regression_metrics"]["mae"] < data["baseline_metrics"]["mae"]

    assert data["regression_metrics"]["wape"] is not None


@pytest.mark.parametrize(
    "path",
    [
        "/products/999/forecast",
        "/products/999/forecast/metrics",
    ],
)
def test_forecasting_returns_not_found(
    client: TestClient,
    path: str,
) -> None:
    response = client.get(path)

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


@pytest.mark.parametrize(
    "path",
    [
        "/products/2/forecast",
        "/products/2/forecast/metrics",
    ],
)
def test_forecasting_rejects_missing_history(
    client: TestClient,
    path: str,
) -> None:
    response = client.get(path)

    assert response.status_code == 422
    assert "No sales history" in response.json()["detail"]


@pytest.mark.parametrize(
    "horizon",
    [0, -1, 31, "invalid"],
)
def test_forecast_rejects_invalid_horizon(
    client: TestClient,
    horizon: int | str,
) -> None:
    response = client.get(
        "/products/1/forecast",
        params={"horizon": horizon},
    )

    assert response.status_code == 422
