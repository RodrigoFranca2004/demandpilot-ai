from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_products_restaurant_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    name: Mapped[str] = mapped_column(String(100))


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_ingredients_restaurant_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(16))


class RecipeItem(Base):
    __tablename__ = "recipe_items"
    __table_args__ = (
        CheckConstraint(
            "quantity_per_unit > 0",
            name="ck_recipe_items_quantity_positive",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        primary_key=True,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        primary_key=True,
    )
    quantity_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 3))


class DailySale(Base):
    __tablename__ = "daily_sales"
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="ck_daily_sales_quantity_nonnegative",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        primary_key=True,
    )
    sale_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
    )
    quantity: Mapped[int]


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint(
            "quantity_available >= 0",
            name="ck_inventory_quantity_nonnegative",
        ),
    )

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        primary_key=True,
    )
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(12, 3))
