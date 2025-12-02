"""Category schema with validation."""
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field

from schemas.base_schema import BaseSchema

if TYPE_CHECKING:
    from schemas.product_schema import ProductSchema


from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name (required, unique)")

class CategorySchema(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100, description="Category name (required, unique)")
    # avoid recursion and mutable defaults in responses
    products: Optional[List['ProductSchema']] = Field(default_factory=list, exclude=True)
