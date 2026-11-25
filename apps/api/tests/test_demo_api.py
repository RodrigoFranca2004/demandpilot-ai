from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.demo_data import seed_demo_data
from app.inventory import service as inventory_service
from app.main import app
from app.models import Base, DailySale, Product, Restaurant
from app.routes import demo


@pytest.fixture
def demo_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, Session, Settings]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    settings = Settings(database_url="sqlite+pysqlite:///:memory:")
    settings.demo_refresh_enabled = True
    monkeypatch.setattr(demo, "planning_today", lambda: date(2026, 11, 3))
    monkeypatch.setattr(inventory_service, "planning_today", demo.planning_today)

    def override_get_db() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: settings

    try:
        with Session(engine) as session, TestClient(app) as client:
            yield client, session, settings
    finally:
        app.dependency_overrides.pop(get_db)
        app.dependency_overrides.pop(get_settings)
        engine.dispose()


def test_demo_settings_and_refresh(
    demo_client: tuple[TestClient, Session, Settings],
) -> None:
    client, session, _ = demo_client
    other = Restaurant(name="Other restaurant")
    session.add(other)
    session.flush()
    product = Product(name="Classic Burger", restaurant_id=other.id)
    session.add(product)
    session.flush()
    other_product_id = product.id
    session.add(
        DailySale(
            product_id=other_product_id, sale_date=date(2026, 10, 31), quantity=28
        )
    )
    seed_demo_data(session, date(2026, 10, 31))
    session.commit()

    response = client.get("/demo")
    assert response.status_code == 200
    assert response.json() == {
        "restaurant_id": 2,
        "planning_date": "2026-11-03",
        "forecast_horizon": 7,
        "inventory_horizon": 1,
        "refresh_enabled": True,
    }

    demo_product_id = session.scalar(
        select(Product.id).where(Product.restaurant_id == 2)
    )
    assert demo_product_id is not None
    previous_sale = session.get(DailySale, (demo_product_id, date(2026, 10, 31)))
    assert previous_sale is not None
    previous_quantity = previous_sale.quantity
    session.rollback()

    response = client.post("/demo/sales/refresh")
    assert response.status_code == 200
    assert response.json() == {"planning_date": "2026-11-03", "added_sales": 10}
    assert client.post("/demo/sales/refresh").json()["added_sales"] == 0

    forecast = client.get(f"/products/{demo_product_id}/forecast").json()
    assert forecast["history_end_date"] == "2026-11-02"
    assert forecast["forecast"][0]["sale_date"] == "2026-11-03"
    assert len(forecast["forecast"]) == 7
    stock = client.get("/restaurants/2/inventory/analysis").json()
    assert stock["start_date"] == stock["end_date"] == "2026-11-03"
    assert session.get(DailySale, (demo_product_id, date(2026, 11, 2))) is not None
    previous_sale = session.get(DailySale, (demo_product_id, date(2026, 10, 31)))
    assert previous_sale is not None
    assert previous_sale.quantity == previous_quantity
    assert session.get(DailySale, (other_product_id, date(2026, 11, 2))) is None


def test_refresh_requires_initial_seed_and_opt_in(
    demo_client: tuple[TestClient, Session, Settings],
) -> None:
    client, _, settings = demo_client
    assert client.get("/demo").json()["restaurant_id"] is None
    assert client.post("/demo/sales/refresh").status_code == 404

    settings.demo_refresh_enabled = False
    assert client.get("/demo").json()["refresh_enabled"] is False
    assert client.post("/demo/sales/refresh").status_code == 403
