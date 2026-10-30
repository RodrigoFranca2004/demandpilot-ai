from collections.abc import Iterator
from datetime import date
from random import Random

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.demo_data import (
    generate_daily_sales,
    seed_demo_data,
)
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
            yield session
    finally:
        engine.dispose()


def test_generated_sales_are_reproducible() -> None:
    end_date = date(2026, 10, 29)

    first = generate_daily_sales(
        product_id=1,
        base_demand=32,
        end_date=end_date,
        rng=Random(42),
    )

    second = generate_daily_sales(
        product_id=1,
        base_demand=32,
        end_date=end_date,
        rng=Random(42),
    )

    assert len(first) == 180
    assert first[-1].sale_date == end_date
    assert [sale.quantity for sale in first] == [sale.quantity for sale in second]
    assert all(sale.quantity >= 0 for sale in first)

    weekend_sales = [sale.quantity for sale in first if sale.sale_date.weekday() >= 5]
    weekday_sales = [sale.quantity for sale in first if sale.sale_date.weekday() < 5]

    weekend_average = sum(weekend_sales) / len(weekend_sales)
    weekday_average = sum(weekday_sales) / len(weekday_sales)

    assert weekend_average > weekday_average


def test_seed_creates_expected_records(db_session: Session) -> None:
    created = seed_demo_data(db_session, date(2026, 10, 29))
    db_session.flush()

    assert created is True

    expected_counts = {
        Restaurant: 1,
        Product: 5,
        Ingredient: 10,
        RecipeItem: 16,
        Inventory: 10,
        DailySale: 900,
    }

    for model, expected in expected_counts.items():
        count = db_session.scalar(select(func.count()).select_from(model))
        assert count == expected

    first_date, last_date = db_session.execute(
        select(
            func.min(DailySale.sale_date),
            func.max(DailySale.sale_date),
        )
    ).one()

    assert first_date == date(2026, 5, 3)
    assert last_date == date(2026, 10, 29)


def test_seed_does_not_duplicate_records(db_session: Session) -> None:
    end_date = date(2026, 10, 29)

    assert seed_demo_data(db_session, end_date) is True
    db_session.commit()

    assert seed_demo_data(db_session, end_date) is False

    count = db_session.scalar(select(func.count()).select_from(DailySale))

    assert count == 900
