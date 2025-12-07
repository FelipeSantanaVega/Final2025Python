"""Product schema for request/response validation."""
from typing import Optional

from pydantic import Field

from schemas.base_schema import BaseSchema


class ProductSchema(BaseSchema):
    """Schema for Product entity with validations."""

    name: str = Field(..., min_length=1, max_length=200, description="Product name (required)")
    description: Optional[str] = Field(
        None, max_length=500, description="Product description (optional)"
    )
    price: float = Field(..., gt=0, description="Product price (must be greater than 0, required)")
    stock: int = Field(default=0, ge=0, description="Product stock quantity (must be >= 0)")
    active: Optional[bool] = Field(default=True, description="Product active flag")

    category_id: int = Field(..., description="Category ID reference (required)")
