import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_SMOKE") != "1",
    reason="Requires a migrated and seeded PostgreSQL test database",
)
def test_migrated_postgres_supports_the_dashboard() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        demo = client.get("/demo")
        assert demo.status_code == 200
        settings = demo.json()
        restaurant_id = settings["restaurant_id"]
        day = settings["planning_date"]
        assert restaurant_id is not None

        products = client.get("/products")
        assert products.status_code == 200
        assert len(products.json()) == 5
        product_id = products.json()[0]["id"]

        sales = client.get(f"/products/{product_id}/sales")
        assert sales.status_code == 200
        assert len(sales.json()) == 180

        forecast = client.get(f"/products/{product_id}/forecast", params={"horizon": 7})
        metrics = client.get(f"/products/{product_id}/forecast/metrics")
        assert forecast.status_code == metrics.status_code == 200
        assert len(forecast.json()["forecast"]) == 7
        assert forecast.json()["selected_method"] == metrics.json()["selected_method"]

        stock = client.get(
            f"/restaurants/{restaurant_id}/inventory/analysis",
            params={"start_date": day, "horizon": 1},
        )
        assert stock.status_code == 200
        assert len(stock.json()["ingredients"]) == 10
        assert isinstance(stock.json()["ingredients"][0]["required_quantity"], str)
