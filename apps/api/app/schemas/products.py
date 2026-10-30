from datetime import date

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DailySaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_date: date
    quantity: int
