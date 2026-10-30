from collections.abc import Iterator
from datetime import date

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

        sales = [
            DailySale(
                product_id=1,
                sale_date=date(2026, 1, 3),
                quantity=30,
            ),
            DailySale(
                product_id=1,
                sale_date=date(2026, 1, 1),
                quantity=20,
            ),
            DailySale(
                product_id=1,
                sale_date=date(2026, 1, 2),
                quantity=25,
            ),
        ]

        session.add(restaurant)
        session.add_all(products)
        session.add_all(sales)
        session.commit()

    def override_get_db() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_list_products(client: TestClient) -> None:
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Classic Burger"},
        {"id": 2, "name": "French Fries"},
    ]


def test_list_product_sales(client: TestClient) -> None:
    response = client.get("/products/1/sales")

    assert response.status_code == 200
    assert response.json() == [
        {"sale_date": "2026-01-01", "quantity": 20},
        {"sale_date": "2026-01-02", "quantity": 25},
        {"sale_date": "2026-01-03", "quantity": 30},
    ]


def test_list_product_sales_with_date_filters(
    client: TestClient,
) -> None:
    response = client.get(
        "/products/1/sales",
        params={
            "start_date": "2026-01-02",
            "end_date": "2026-01-02",
        },
    )

    assert response.status_code == 200
    assert response.json() == [{"sale_date": "2026-01-02", "quantity": 25}]


def test_list_product_sales_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get("/products/999/sales")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


def test_list_product_sales_rejects_invalid_date_range(
    client: TestClient,
) -> None:
    response = client.get(
        "/products/1/sales",
        params={
            "start_date": "2026-01-03",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422


def test_list_product_sales_returns_empty_list(
    client: TestClient,
) -> None:
    response = client.get("/products/2/sales")

    assert response.status_code == 200
    assert response.json() == []


def test_list_product_sales_rejects_invalid_date(
    client: TestClient,
) -> None:
    response = client.get(
        "/products/1/sales",
        params={"start_date": "invalid-date"},
    )

    assert response.status_code == 422
