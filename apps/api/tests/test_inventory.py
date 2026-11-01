from decimal import Decimal

import pytest

from app.inventory.calculator import (
    calculate_ingredient_requirements,
)
from app.models import Inventory, RecipeItem


def test_calculates_shared_ingredient_requirements() -> None:
    recipes = [
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
    ]

    stock = [
        Inventory(
            ingredient_id=1,
            quantity_available=Decimal("75"),
        ),
        Inventory(
            ingredient_id=2,
            quantity_available=Decimal("10"),
        ),
    ]

    requirements = calculate_ingredient_requirements(
        product_demand={1: 50, 2: 30},
        recipe_items=recipes,
        inventory=stock,
    )

    buns = requirements[0]
    ingredient = requirements[1]

    assert buns.ingredient_id == 1
    assert buns.required_quantity == Decimal("80")
    assert buns.available_quantity == Decimal("75")
    assert buns.shortage_quantity == Decimal("5")
    assert buns.at_risk is True

    assert ingredient.required_quantity == Decimal("6.250")
    assert ingredient.shortage_quantity == Decimal("0")
    assert ingredient.at_risk is False


def test_zero_demand_requires_no_ingredients() -> None:
    requirements = calculate_ingredient_requirements(
        product_demand={1: 0},
        recipe_items=[
            RecipeItem(
                product_id=1,
                ingredient_id=1,
                quantity_per_unit=Decimal("2"),
            )
        ],
        inventory=[
            Inventory(
                ingredient_id=1,
                quantity_available=Decimal("10"),
            )
        ],
    )

    assert requirements[0].required_quantity == 0
    assert requirements[0].shortage_quantity == 0
    assert requirements[0].at_risk is False


def test_rejects_negative_product_demand() -> None:
    with pytest.raises(
        ValueError,
        match="non-negative integers",
    ):
        calculate_ingredient_requirements(
            product_demand={1: -5},
            recipe_items=[],
            inventory=[],
        )


def test_rejects_missing_recipe() -> None:
    with pytest.raises(
        ValueError,
        match="Missing recipes",
    ):
        calculate_ingredient_requirements(
            product_demand={1: 10},
            recipe_items=[],
            inventory=[],
        )


def test_rejects_missing_inventory() -> None:
    with pytest.raises(
        ValueError,
        match="Missing inventory",
    ):
        calculate_ingredient_requirements(
            product_demand={1: 10},
            recipe_items=[
                RecipeItem(
                    product_id=1,
                    ingredient_id=1,
                    quantity_per_unit=Decimal("1"),
                )
            ],
            inventory=[],
        )


def test_rejects_negative_inventory() -> None:
    with pytest.raises(
        ValueError,
        match="Inventory quantities cannot be negative",
    ):
        calculate_ingredient_requirements(
            product_demand={1: 10},
            recipe_items=[
                RecipeItem(
                    product_id=1,
                    ingredient_id=1,
                    quantity_per_unit=Decimal("1"),
                )
            ],
            inventory=[
                Inventory(
                    ingredient_id=1,
                    quantity_available=Decimal("-1"),
                )
            ],
        )
