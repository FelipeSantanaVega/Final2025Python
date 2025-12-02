"""Category schema with validation."""
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field
from schemas.base_schema import BaseSchema

if TYPE_CHECKING:
    from schemas.product_schema import ProductSchema

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name (required, unique)")

class CategorySchema(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100, description="Category name (required, unique)")
    products: Optional[List['ProductSchema']] = Field(default_factory=list, exclude=True)  # exclude to avoid cycles
