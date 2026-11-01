from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.models import Inventory, RecipeItem


@dataclass(frozen=True)
class IngredientRequirement:
    ingredient_id: int
    required_quantity: Decimal
    available_quantity: Decimal
    shortage_quantity: Decimal

    @property
    def at_risk(self) -> bool:
        return self.shortage_quantity > 0


def calculate_ingredient_requirements(
    product_demand: dict[int, int],
    recipe_items: Sequence[RecipeItem],
    inventory: Sequence[Inventory],
) -> list[IngredientRequirement]:
    if any(
        not isinstance(quantity, int) or quantity < 0
        for quantity in product_demand.values()
    ):
        raise ValueError("Product demand must contain non-negative integers")

    required_by_ingredient: dict[int, Decimal] = defaultdict(Decimal)
    products_with_recipes: set[int] = set()

    for item in recipe_items:
        if item.product_id not in product_demand:
            continue

        if item.quantity_per_unit <= 0:
            raise ValueError("Recipe quantities must be positive")

        products_with_recipes.add(item.product_id)

        required_by_ingredient[item.ingredient_id] += (
            item.quantity_per_unit * product_demand[item.product_id]
        )

    missing_recipes = {
        product_id
        for product_id, quantity in product_demand.items()
        if quantity > 0 and product_id not in products_with_recipes
    }

    if missing_recipes:
        raise ValueError(f"Missing recipes for products: {sorted(missing_recipes)}")

    stock_by_ingredient = {
        item.ingredient_id: item.quantity_available for item in inventory
    }

    if any(quantity < 0 for quantity in stock_by_ingredient.values()):
        raise ValueError("Inventory quantities cannot be negative")

    requirements = []

    for ingredient_id in sorted(required_by_ingredient):
        if ingredient_id not in stock_by_ingredient:
            raise ValueError(f"Missing inventory for ingredient {ingredient_id}")

        required = required_by_ingredient[ingredient_id]
        available = stock_by_ingredient[ingredient_id]

        shortage = max(
            required - available,
            Decimal("0"),
        )

        requirements.append(
            IngredientRequirement(
                ingredient_id=ingredient_id,
                required_quantity=required,
                available_quantity=available,
                shortage_quantity=shortage,
            )
        )

    return requirements
