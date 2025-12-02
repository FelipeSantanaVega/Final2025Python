"""Product schema for request/response validation."""
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field

from schemas.base_schema import BaseSchema

if TYPE_CHECKING:
    from schemas.category_schema import CategorySchema
    from schemas.order_detail_schema import OrderDetailSchema
    from schemas.review_schema import ReviewSchema


from pydantic import Field

class ProductSchema(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200, description="Product name (required)")
    price: float = Field(..., gt=0, description="Product price (must be greater than 0, required)")
    stock: int = Field(default=0, ge=0, description="Product stock quantity (must be >= 0)")
    category_id: int = Field(..., description="Category ID reference (required)")

    # Break cycles and fix mutable defaults
    category: Optional['CategorySchema'] = Field(default=None, exclude=True)
    reviews: Optional[List['ReviewSchema']] = Field(default_factory=list, exclude=True)
    order_details: Optional[List['OrderDetailSchema']] = Field(default_factory=list, exclude=True)

