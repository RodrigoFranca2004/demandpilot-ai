from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.forecasting.service import ForecastPoint
from app.inventory import service as inventory_service
from app.main import app
from app.models import (
    Base,
    DailySale,
    Ingredient,
    Inventory,
    Product,
    RecipeItem,
    Restaurant,
)


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
            session.add_all(
                [
                    Restaurant(id=1, name="Test Restaurant"),
                    Restaurant(id=2, name="Empty Restaurant"),
                ]
            )

            session.add_all(
                [
                    Product(
                        id=1,
                        restaurant_id=1,
                        name="Classic Burger",
                    ),
                    Product(
                        id=2,
                        restaurant_id=1,
                        name="Chicken Sandwich",
                    ),
                    Ingredient(
                        id=1,
                        restaurant_id=1,
                        name="Burger Bun",
                        unit="unit",
                    ),
                    Ingredient(
                        id=2,
                        restaurant_id=1,
                        name="Sauce",
                        unit="kg",
                    ),
                ]
            )

            session.flush()

            session.add_all(
                [
                    RecipeItem(
                        product_id=1,
                        ingredient_id=1,
                        quantity_per_unit=Decimal("1"),
                    ),
                    RecipeItem(
                        product_id=2,
                        ingredient_id=1,
                        quantity_per_unit=Decimal("1"),
                    ),
                    RecipeItem(
                        product_id=1,
                        ingredient_id=2,
                        quantity_per_unit=Decimal("0.125"),
                    ),
                    Inventory(
                        ingredient_id=1,
                        quantity_available=Decimal("8"),
                    ),
                    Inventory(
                        ingredient_id=2,
                        quantity_available=Decimal("1"),
                    ),
                    DailySale(
                        product_id=1,
                        sale_date=date(2026, 10, 29),
                        quantity=10,
                    ),
                    DailySale(
                        product_id=2,
                        sale_date=date(2026, 10, 29),
                        quantity=10,
                    ),
                ]
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


def test_inventory_analysis_returns_requirements(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quantities = {
        1: [99.0, 2.2, 3.1],
        2: [99.0, 1.1, 2.0],
    }

    def fake_forecast(
        session: Session,
        product_id: int,
        horizon: int,
    ) -> SimpleNamespace:
        assert horizon == 3

        dates = [
            date(2026, 10, 30),
            date(2026, 10, 31),
            date(2026, 11, 1),
        ]

        return SimpleNamespace(
            selected_method="linear_regression",
            forecast=[
                ForecastPoint(
                    sale_date=day,
                    predicted_quantity=quantity,
                )
                for day, quantity in zip(
                    dates,
                    quantities[product_id],
                    strict=True,
                )
            ],
        )

    monkeypatch.setattr(
        inventory_service,
        "forecast_product_demand",
        fake_forecast,
    )

    response = client.get(
        "/restaurants/1/inventory/analysis",
        params={
            "start_date": "2026-10-31",
            "horizon": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == 1
    assert data["start_date"] == "2026-10-31"
    assert data["end_date"] == "2026-11-01"

    assert [product["predicted_units"] for product in data["products"]] == [7, 4]

    assert all(
        product["history_end_date"] == "2026-10-29" for product in data["products"]
    )

    ingredients = {item["ingredient_name"]: item for item in data["ingredients"]}

    buns = ingredients["Burger Bun"]

    assert Decimal(buns["required_quantity"]) == 11
    assert Decimal(buns["available_quantity"]) == 8
    assert Decimal(buns["shortage_quantity"]) == 3
    assert buns["at_risk"] is True

    sauce = ingredients["Sauce"]

    assert Decimal(sauce["required_quantity"]) == Decimal("0.875")
    assert Decimal(sauce["shortage_quantity"]) == 0
    assert sauce["at_risk"] is False


def test_inventory_analysis_rejects_unknown_restaurant(
    client: TestClient,
) -> None:
    response = client.get("/restaurants/999/inventory/analysis")

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


def test_inventory_analysis_rejects_empty_restaurant(
    client: TestClient,
) -> None:
    response = client.get("/restaurants/2/inventory/analysis")

    assert response.status_code == 422
    assert "No products found" in response.json()["detail"]


@pytest.mark.parametrize("horizon", [0, 31])
def test_inventory_analysis_rejects_invalid_horizon(
    client: TestClient,
    horizon: int,
) -> None:
    response = client.get(
        "/restaurants/1/inventory/analysis",
        params={"horizon": horizon},
    )

    assert response.status_code == 422


def test_inventory_analysis_rejects_invalid_date(
    client: TestClient,
) -> None:
    response = client.get(
        "/restaurants/1/inventory/analysis",
        params={"start_date": "invalid-date"},
    )

    assert response.status_code == 422


def test_inventory_analysis_rejects_overlapping_history(
    client: TestClient,
) -> None:
    response = client.get(
        "/restaurants/1/inventory/analysis",
        params={"start_date": "2026-10-29"},
    )

    assert response.status_code == 422
    assert "after the last sales date" in response.json()["detail"]
