
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    name: str
    category: str
    price: Decimal
    specifications: dict[str, Any]
    intended_uses: list[str]
    features: list[str]
    description: str
    is_available: bool


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
