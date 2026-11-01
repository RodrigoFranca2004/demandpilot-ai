from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.forecasting.service import ForecastPoint
from app.inventory import service as inventory_service
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
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            session.add(Restaurant(id=1, name="Test Restaurant"))

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
            yield session
    finally:
        engine.dispose()


def test_inventory_aggregates_shared_ingredients_and_skips_past_forecasts(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    quantities = {
        1: [99.0, 2.2, 3.1],
        2: [99.0, 1.1, 2.0],
    }

    def fake_forecast(
        session: Session,
        product_id: int,
        horizon: int,
    ) -> SimpleNamespace:
        calls.append((product_id, horizon))

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

    analysis = inventory_service.analyze_inventory(
        db_session,
        restaurant_id=1,
        horizon=2,
        start_date=date(2026, 10, 31),
    )

    assert calls == [(1, 3), (2, 3)]

    assert analysis.start_date == date(2026, 10, 31)
    assert analysis.end_date == date(2026, 11, 1)

    assert [item.predicted_units for item in analysis.products] == [7, 4]

    assert all(
        item.history_end_date == date(2026, 10, 29) for item in analysis.products
    )

    buns, sauce = analysis.ingredients

    assert buns.ingredient_name == "Burger Bun"
    assert buns.required_quantity == Decimal("11")
    assert buns.available_quantity == Decimal("8")
    assert buns.shortage_quantity == Decimal("3")
    assert buns.at_risk is True

    assert sauce.required_quantity == Decimal("0.875")
    assert sauce.shortage_quantity == 0
    assert sauce.at_risk is False


def test_inventory_rejects_plan_overlapping_history(
    db_session: Session,
) -> None:
    with pytest.raises(
        ValueError,
        match="after the last sales date",
    ):
        inventory_service.analyze_inventory(
            db_session,
            restaurant_id=1,
            start_date=date(2026, 10, 29),
        )


@pytest.mark.parametrize("horizon", [0, 31])
def test_inventory_rejects_invalid_horizon(
    db_session: Session,
    horizon: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 1 and 30",
    ):
        inventory_service.analyze_inventory(
            db_session,
            restaurant_id=1,
            horizon=horizon,
        )


def test_inventory_rejects_product_without_sales(
    db_session: Session,
) -> None:
    db_session.execute(delete(DailySale).where(DailySale.product_id == 1))
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="No sales history for product 1",
    ):
        inventory_service.analyze_inventory(
            db_session,
            restaurant_id=1,
            start_date=date(2026, 10, 31),
        )


def test_inventory_rejects_restaurant_without_products(
    db_session: Session,
) -> None:
    db_session.add(Restaurant(id=2, name="Empty Restaurant"))
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="No products found",
    ):
        inventory_service.analyze_inventory(
            db_session,
            restaurant_id=2,
        )
