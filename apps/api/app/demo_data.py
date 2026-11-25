from datetime import date, timedelta
from decimal import Decimal
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.core.planning import planning_today
from app.models import (
    DailySale,
    Ingredient,
    Inventory,
    Product,
    RecipeItem,
    Restaurant,
)

RESTAURANT_NAME = "DemandPilot Demo"
HISTORY_DAYS = 180
SEED = 42

PRODUCTS = {
    "Classic Burger": 32,
    "Chicken Sandwich": 22,
    "Veggie Burger": 14,
    "French Fries": 40,
    "Lemonade": 28,
}

INGREDIENTS = {
    "Burger Bun": ("unit", "75"),
    "Beef Patty": ("unit", "40"),
    "Chicken Fillet": ("unit", "26"),
    "Veggie Patty": ("unit", "18"),
    "Cheese Slice": ("unit", "40"),
    "Lettuce": ("g", "5000"),
    "Tomato": ("g", "6000"),
    "Potato": ("g", "9000"),
    "Lemon": ("unit", "90"),
    "Sugar": ("g", "4000"),
}

RECIPES = {
    "Classic Burger": {
        "Burger Bun": "1",
        "Beef Patty": "1",
        "Cheese Slice": "1",
        "Lettuce": "30",
        "Tomato": "40",
    },
    "Chicken Sandwich": {
        "Burger Bun": "1",
        "Chicken Fillet": "1",
        "Lettuce": "25",
        "Tomato": "30",
    },
    "Veggie Burger": {
        "Burger Bun": "1",
        "Veggie Patty": "1",
        "Lettuce": "30",
        "Tomato": "40",
    },
    "French Fries": {
        "Potato": "180",
    },
    "Lemonade": {
        "Lemon": "2",
        "Sugar": "20",
    },
}

WEEKDAY_FACTORS = (0.85, 0.95, 1.0, 1.05, 1.2, 1.5, 1.3)


def generate_daily_sales(
    product_id: int,
    base_demand: int,
    end_date: date,
    rng: Random,
    days: int = HISTORY_DAYS,
) -> list[DailySale]:
    start_date = end_date - timedelta(days=days - 1)
    sales = []

    for offset in range(days):
        sale_date = start_date + timedelta(days=offset)

        weekly_factor = WEEKDAY_FACTORS[sale_date.weekday()]
        trend_factor = 1 + offset * 0.001
        noise_factor = rng.uniform(0.9, 1.1)

        quantity = max(
            0,
            round(base_demand * weekly_factor * trend_factor * noise_factor),
        )

        sales.append(
            DailySale(
                product_id=product_id,
                sale_date=sale_date,
                quantity=quantity,
            )
        )

    return sales


def seed_demo_data(session: Session, end_date: date) -> bool:
    existing = session.scalar(
        select(Restaurant.id).where(Restaurant.name == RESTAURANT_NAME)
    )

    if existing is not None:
        return False

    restaurant = Restaurant(name=RESTAURANT_NAME)
    session.add(restaurant)
    session.flush()

    products = {
        name: Product(
            name=name,
            restaurant_id=restaurant.id,
        )
        for name in PRODUCTS
    }

    ingredients = {
        name: Ingredient(
            name=name,
            unit=unit,
            restaurant_id=restaurant.id,
        )
        for name, (unit, _) in INGREDIENTS.items()
    }

    session.add_all([*products.values(), *ingredients.values()])
    session.flush()

    for product_name, recipe in RECIPES.items():
        for ingredient_name, quantity in recipe.items():
            session.add(
                RecipeItem(
                    product_id=products[product_name].id,
                    ingredient_id=ingredients[ingredient_name].id,
                    quantity_per_unit=Decimal(quantity),
                )
            )

    for name, (_, quantity) in INGREDIENTS.items():
        session.add(
            Inventory(
                ingredient_id=ingredients[name].id,
                quantity_available=Decimal(quantity),
            )
        )

    rng = Random(SEED)

    for name, demand in PRODUCTS.items():
        session.add_all(
            generate_daily_sales(
                product_id=products[name].id,
                base_demand=demand,
                end_date=end_date,
                rng=rng,
            )
        )

    return True


def refresh_demo_sales(session: Session, restaurant_id: int, end_date: date) -> int:
    products = dict(
        session.execute(
            select(Product.name, Product.id).where(
                Product.restaurant_id == restaurant_id, Product.name.in_(PRODUCTS)
            )
        ).all()
    )
    if products.keys() != PRODUCTS.keys():
        raise ValueError("Demo product catalog is incomplete")

    start_date = end_date - timedelta(days=HISTORY_DAYS - 1)
    existing = {
        (product_id, sale_date)
        for product_id, sale_date in session.execute(
            select(DailySale.product_id, DailySale.sale_date).where(
                DailySale.product_id.in_(products.values()),
                DailySale.sale_date.between(start_date, end_date),
            )
        )
    }
    rng = Random(SEED)
    missing_sales = []
    for name, demand in PRODUCTS.items():
        sales = generate_daily_sales(products[name], demand, end_date, rng)
        missing_sales.extend(
            sale for sale in sales if (sale.product_id, sale.sale_date) not in existing
        )

    session.add_all(missing_sales)
    return len(missing_sales)


def main() -> None:
    end_date = planning_today() - timedelta(days=1)

    with Session(get_engine()) as session:
        if seed_demo_data(session, end_date):
            session.commit()
            print(f"Demo data created successfully through {end_date}.")
        else:
            print("Demo data already exists. No changes made.")


if __name__ == "__main__":
    main()
