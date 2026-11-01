from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from math import ceil, isfinite

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.forecasting.service import forecast_product_demand
from app.inventory.calculator import calculate_ingredient_requirements
from app.models import DailySale, Ingredient, Inventory, Product, RecipeItem


@dataclass(frozen=True)
class ProductDemand:
    product_id: int
    product_name: str
    predicted_units: int
    selected_method: str
    history_end_date: date


@dataclass(frozen=True)
class IngredientRisk:
    ingredient_id: int
    ingredient_name: str
    unit: str
    required_quantity: Decimal
    available_quantity: Decimal
    shortage_quantity: Decimal
    at_risk: bool


@dataclass(frozen=True)
class InventoryAnalysis:
    restaurant_id: int
    start_date: date
    end_date: date
    products: list[ProductDemand]
    ingredients: list[IngredientRisk]


def analyze_inventory(
    session: Session,
    restaurant_id: int,
    horizon: int = 1,
    start_date: date | None = None,
) -> InventoryAnalysis:
    if not 1 <= horizon <= 30:
        raise ValueError("Planning horizon must be between 1 and 30 days")

    start = start_date if start_date is not None else date.today()
    end = start + timedelta(days=horizon - 1)

    products = session.scalars(
        select(Product)
        .where(Product.restaurant_id == restaurant_id)
        .order_by(Product.id)
    ).all()

    if not products:
        raise ValueError(f"No products found for restaurant {restaurant_id}")

    demand_by_product: dict[int, int] = {}
    product_results: list[ProductDemand] = []

    for product in products:
        history_end = session.scalar(
            select(func.max(DailySale.sale_date)).where(
                DailySale.product_id == product.id
            )
        )

        if history_end is None:
            raise ValueError(f"No sales history for product {product.id}")

        if start <= history_end:
            raise ValueError(
                "Planning start date must be after the last sales date "
                f"for product {product.id}"
            )

        report = forecast_product_demand(
            session=session,
            product_id=product.id,
            horizon=(end - history_end).days,
        )

        forecasts = {
            point.sale_date: point.predicted_quantity for point in report.forecast
        }

        predicted_units = 0

        for offset in range(horizon):
            day = start + timedelta(days=offset)
            predicted = forecasts.get(day)

            if predicted is None or not isfinite(predicted) or predicted < 0:
                raise ValueError(
                    f"Missing or invalid forecast for product {product.id} on {day}"
                )

            predicted_units += ceil(predicted)

        demand_by_product[product.id] = predicted_units

        product_results.append(
            ProductDemand(
                product_id=product.id,
                product_name=product.name,
                predicted_units=predicted_units,
                selected_method=report.selected_method,
                history_end_date=history_end,
            )
        )

    product_ids = [product.id for product in products]

    recipe_items = session.scalars(
        select(RecipeItem).where(RecipeItem.product_id.in_(product_ids))
    ).all()

    ingredient_ids = {item.ingredient_id for item in recipe_items}

    ingredients = session.scalars(
        select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
    ).all()

    stock = session.scalars(
        select(Inventory).where(Inventory.ingredient_id.in_(ingredient_ids))
    ).all()

    requirements = calculate_ingredient_requirements(
        product_demand=demand_by_product,
        recipe_items=recipe_items,
        inventory=stock,
    )

    ingredients_by_id = {ingredient.id: ingredient for ingredient in ingredients}

    ingredient_results = []

    for requirement in requirements:
        ingredient = ingredients_by_id.get(requirement.ingredient_id)

        if ingredient is None:
            raise ValueError(f"Missing ingredient {requirement.ingredient_id}")

        ingredient_results.append(
            IngredientRisk(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                unit=ingredient.unit,
                required_quantity=requirement.required_quantity,
                available_quantity=requirement.available_quantity,
                shortage_quantity=requirement.shortage_quantity,
                at_risk=requirement.at_risk,
            )
        )

    return InventoryAnalysis(
        restaurant_id=restaurant_id,
        start_date=start,
        end_date=end,
        products=product_results,
        ingredients=ingredient_results,
    )
