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
    category: Optional['CategorySchema'] = Field(default=None, exclude=True)
    reviews: Optional[List['ReviewSchema']] = Field(default_factory=list, exclude=True)
    order_details: Optional[List['OrderDetailSchema']] = Field(default_factory=list, exclude=True)


