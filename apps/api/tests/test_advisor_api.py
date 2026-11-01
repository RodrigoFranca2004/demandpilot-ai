from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from google.genai import errors
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, Product, Restaurant
from app.routes import advisor as advisor_routes


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            Restaurant(
                id=1,
                name="Test Restaurant",
            )
        )
        session.flush()

        session.add(
            Product(
                id=1,
                restaurant_id=1,
                name="Classic Burger",
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
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def advisor_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> Mock:
    mock = Mock(return_value="Burger buns are at risk of shortage.")

    monkeypatch.setattr(
        advisor_routes,
        "ask_advisor",
        mock,
    )

    return mock


def test_advisor_chat_returns_answer(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    response = client.post(
        "/restaurants/1/advisor/chat",
        json={
            "message": "Which ingredients are at risk?",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Burger buns are at risk of shortage."}

    advisor_mock.assert_called_once()

    arguments = advisor_mock.call_args.kwargs

    assert isinstance(arguments["session"], Session)
    assert arguments["restaurant_id"] == 1
    assert arguments["question"] == "Which ingredients are at risk?"


def test_advisor_chat_trims_message(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    response = client.post(
        "/restaurants/1/advisor/chat",
        json={
            "message": "  Analyze my inventory.  ",
        },
    )

    assert response.status_code == 200
    assert advisor_mock.call_args.kwargs["question"] == "Analyze my inventory."


def test_advisor_chat_returns_404_for_unknown_restaurant(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    response = client.post(
        "/restaurants/999/advisor/chat",
        json={
            "message": "Analyze my inventory.",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}

    advisor_mock.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 1001},
        {"message": 123},
    ],
)
def test_advisor_chat_rejects_invalid_messages(
    client: TestClient,
    advisor_mock: Mock,
    payload: dict,
) -> None:
    response = client.post(
        "/restaurants/1/advisor/chat",
        json=payload,
    )

    assert response.status_code == 422
    advisor_mock.assert_not_called()


def test_advisor_chat_handles_missing_products(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    advisor_mock.side_effect = ValueError("No products found for this restaurant")

    response = client.post(
        "/restaurants/1/advisor/chat",
        json={"message": "Analyze demand."},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "No products found for this restaurant"}


def test_advisor_chat_handles_missing_api_key(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    advisor_mock.side_effect = ValueError("GEMINI_API_KEY is not configured")

    response = client.post(
        "/restaurants/1/advisor/chat",
        json={"message": "Analyze demand."},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Gemini API key is not configured"}


def test_advisor_chat_handles_gemini_rate_limit(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    advisor_mock.side_effect = errors.ClientError(
        429,
        {
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "message": "Quota exceeded",
            }
        },
    )

    response = client.post(
        "/restaurants/1/advisor/chat",
        json={"message": "Analyze demand."},
    )

    assert response.status_code == 429
    assert response.json() == {"detail": "Gemini API quota or rate limit exceeded"}


def test_advisor_chat_handles_gemini_failure(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    advisor_mock.side_effect = errors.ServerError(
        503,
        {
            "error": {
                "code": 503,
                "status": "UNAVAILABLE",
                "message": "Service unavailable",
            }
        },
    )

    response = client.post(
        "/restaurants/1/advisor/chat",
        json={"message": "Analyze demand."},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Gemini API request failed"}


def test_advisor_chat_handles_invalid_model_response(
    client: TestClient,
    advisor_mock: Mock,
) -> None:
    advisor_mock.side_effect = RuntimeError(
        "The assistant exceeded the function calling limit"
    )

    response = client.post(
        "/restaurants/1/advisor/chat",
        json={"message": "Analyze demand."},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": ("The AI advisor could not generate a valid response")
    }
