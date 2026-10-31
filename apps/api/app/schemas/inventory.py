from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductDemandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    predicted_units: int
    selected_method: str
    history_end_date: date


class IngredientRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    unit: str
    required_quantity: Decimal
    available_quantity: Decimal
    shortage_quantity: Decimal
    at_risk: bool


class InventoryAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    restaurant_id: int
    start_date: date
    end_date: date
    products: list[ProductDemandResponse]
    ingredients: list[IngredientRiskResponse]
