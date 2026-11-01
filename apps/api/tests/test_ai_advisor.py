from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.agents import advisor
from app.models import Base, Product, Restaurant


@dataclass(frozen=True)
class FakeForecastReport:
    product_id: int
    selected_method: str
    forecast: list[dict]


@dataclass(frozen=True)
class FakeInventoryReport:
    restaurant_id: int
    start_date: date
    ingredients: list[dict]


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
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

            yield session
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-api-key"),
        gemini_model="gemini-3.5-flash-lite",
    )

    monkeypatch.setattr(
        advisor,
        "get_settings",
        lambda: settings,
    )


def make_tool_response(
    name: str,
    arguments: dict,
) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name=name,
                                args=arguments,
                            )
                        )
                    ],
                )
            )
        ]
    )


def make_text_response(
    answer: str,
) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=answer)],
                )
            )
        ]
    )


def make_client(*responses: types.GenerateContentResponse):
    return SimpleNamespace(
        models=SimpleNamespace(generate_content=Mock(side_effect=responses))
    )


def test_advisor_calls_forecast_tool(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = FakeForecastReport(
        product_id=1,
        selected_method="linear_regression",
        forecast=[
            {
                "sale_date": date(2026, 10, 30),
                "predicted_quantity": 44.58,
            }
        ],
    )

    forecast_mock = Mock(return_value=report)

    monkeypatch.setattr(
        advisor,
        "forecast_product_demand",
        forecast_mock,
    )

    client = make_client(
        make_tool_response(
            "get_product_forecast",
            {"product_id": 1, "horizon": 1},
        ),
        make_text_response("The forecast is 44.58 units for October 30."),
    )

    answer = advisor.ask_advisor(
        session=db_session,
        restaurant_id=1,
        question="What is the Classic Burger forecast?",
        client=client,
    )

    assert answer == ("The forecast is 44.58 units for October 30.")

    forecast_mock.assert_called_once_with(
        session=db_session,
        product_id=1,
        horizon=1,
    )

    assert client.models.generate_content.call_count == 2

    second_call = client.models.generate_content.call_args_list[1].kwargs

    tool_response_content = second_call["contents"][-1]

    assert tool_response_content.role == "user"
    assert len(tool_response_content.parts) == 1

    function_response = tool_response_content.parts[0].function_response

    assert function_response is not None
    assert function_response.name == "get_product_forecast"

    tool_result = (
        second_call["contents"][-1].parts[0].function_response.response["result"]
    )

    assert tool_result["selected_method"] == "linear_regression"
    assert tool_result["forecast"][0]["sale_date"] == "2026-10-30"
    assert tool_result["forecast"][0]["predicted_quantity"] == 44.58


def test_advisor_calls_inventory_tool(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = FakeInventoryReport(
        restaurant_id=1,
        start_date=date.today(),
        ingredients=[
            {
                "ingredient_name": "Burger Bun",
                "unit": "unit",
                "required_quantity": Decimal("120"),
                "available_quantity": Decimal("75"),
                "shortage_quantity": Decimal("45"),
                "at_risk": True,
            }
        ],
    )

    inventory_mock = Mock(return_value=analysis)

    monkeypatch.setattr(
        advisor,
        "analyze_inventory",
        inventory_mock,
    )

    client = make_client(
        make_tool_response(
            "get_inventory_analysis",
            {"horizon": 1},
        ),
        make_text_response("Burger buns are at risk of shortage."),
    )

    answer = advisor.ask_advisor(
        session=db_session,
        restaurant_id=1,
        question="Which ingredients are at risk?",
        client=client,
    )

    assert answer == "Burger buns are at risk of shortage."

    inventory_mock.assert_called_once_with(
        session=db_session,
        restaurant_id=1,
        start_date=None,
        horizon=1,
    )

    second_call = client.models.generate_content.call_args_list[1].kwargs

    tool_response_content = second_call["contents"][-1]

    assert tool_response_content.role == "user"
    assert len(tool_response_content.parts) == 1

    function_response = tool_response_content.parts[0].function_response

    assert function_response is not None
    assert function_response.name == "get_inventory_analysis"

    tool_result = (
        second_call["contents"][-1].parts[0].function_response.response["result"]
    )

    ingredient = tool_result["ingredients"][0]

    assert ingredient["ingredient_name"] == "Burger Bun"
    assert ingredient["shortage_quantity"] == "45"
    assert ingredient["at_risk"] is True


def test_advisor_rejects_invalid_tool_arguments(
    db_session: Session,
) -> None:
    result = advisor.execute_tool(
        session=db_session,
        restaurant_id=1,
        name="get_product_forecast",
        arguments={
            "product_id": 1,
            "horizon": 99,
        },
    )

    assert "error" in result


def test_advisor_rejects_unknown_product(
    db_session: Session,
) -> None:
    result = advisor.execute_tool(
        session=db_session,
        restaurant_id=1,
        name="get_product_forecast",
        arguments={
            "product_id": 999,
            "horizon": 1,
        },
    )

    assert result == {"error": "Product not found"}


def test_advisor_rejects_past_inventory_date(
    db_session: Session,
) -> None:
    result = advisor.execute_tool(
        session=db_session,
        restaurant_id=1,
        name="get_inventory_analysis",
        arguments={
            "start_date": "2020-01-01",
            "horizon": 1,
        },
    )

    assert result == {"error": "Planning start date cannot be in the past"}


def test_advisor_rejects_empty_question(
    db_session: Session,
) -> None:
    with pytest.raises(
        ValueError,
        match="Question must contain",
    ):
        advisor.ask_advisor(
            session=db_session,
            restaurant_id=1,
            question="   ",
            client=make_client(),
        )


def test_advisor_requires_tool_call(
    db_session: Session,
) -> None:
    client = make_client(make_text_response("An unsupported answer."))

    with pytest.raises(
        RuntimeError,
        match="did not consult application tools",
    ):
        advisor.ask_advisor(
            session=db_session,
            restaurant_id=1,
            question="What should I prepare?",
            client=client,
        )


def test_advisor_limits_tool_calling_rounds(
    db_session: Session,
) -> None:
    client = make_client(
        *[
            make_tool_response(
                "unsupported_tool",
                {},
            )
            for _ in range(advisor.MAX_ROUNDS)
        ]
    )

    with pytest.raises(
        RuntimeError,
        match="exceeded the function calling limit",
    ):
        advisor.ask_advisor(
            session=db_session,
            restaurant_id=1,
            question="Analyze my inventory.",
            client=client,
        )

    assert client.models.generate_content.call_count == advisor.MAX_ROUNDS
