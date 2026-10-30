"""Create initial restaurant data schema."""

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            unique=True,
        ),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "restaurant_id",
            sa.Integer(),
            sa.ForeignKey("restaurants.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_products_restaurant_name",
        ),
    )

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "restaurant_id",
            sa.Integer(),
            sa.ForeignKey("restaurants.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_ingredients_restaurant_name",
        ),
    )

    op.create_table(
        "daily_sales",
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            primary_key=True,
        ),
        sa.Column("sale_date", sa.Date(), primary_key=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantity >= 0",
            name="ck_daily_sales_quantity_nonnegative",
        ),
    )

    op.create_table(
        "recipe_items",
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            primary_key=True,
        ),
        sa.Column(
            "ingredient_id",
            sa.Integer(),
            sa.ForeignKey("ingredients.id"),
            primary_key=True,
        ),
        sa.Column(
            "quantity_per_unit",
            sa.Numeric(12, 3),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity_per_unit > 0",
            name="ck_recipe_items_quantity_positive",
        ),
    )

    op.create_table(
        "inventory",
        sa.Column(
            "ingredient_id",
            sa.Integer(),
            sa.ForeignKey("ingredients.id"),
            primary_key=True,
        ),
        sa.Column(
            "quantity_available",
            sa.Numeric(12, 3),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity_available >= 0",
            name="ck_inventory_quantity_nonnegative",
        ),
    )


def downgrade() -> None:
    op.drop_table("inventory")
    op.drop_table("recipe_items")
    op.drop_table("daily_sales")
    op.drop_table("ingredients")
    op.drop_table("products")
    op.drop_table("restaurants")
