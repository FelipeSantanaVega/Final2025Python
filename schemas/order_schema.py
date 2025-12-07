"""Order schema with validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import Field
from pydantic import BaseModel

from schemas.base_schema import BaseSchema
from models.enums import DeliveryMethod, Status


class OrderItemInput(BaseModel):
    product_id: int = Field(..., description="Product ID reference")
    quantity: int = Field(..., gt=0, description="Quantity (>0)")


class OrderSchema(BaseSchema):
    """Schema for Order entity with validations."""

    date: Optional[datetime] = Field(default=None, description="Order date (auto-set if missing)")
    total: float = Field(..., ge=0, description="Total amount (must be >= 0, required)")
    delivery_method: DeliveryMethod = Field(..., description="Delivery method (required)")
    status: Status = Field(default=Status.PENDING, description="Order status")
    client_id: int = Field(..., description="Client ID reference (required)")
    bill_id: Optional[int] = Field(default=None, description="Bill ID reference (optional, auto-created if missing)")
    items: Optional[List[OrderItemInput]] = Field(default=None, description="Order items to create order details and update stock")
    discount_pct: Optional[float] = Field(default=0, ge=0, le=100, description="Discount percentage (0-100)")
