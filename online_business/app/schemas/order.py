from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    product_id: int
    payment_method_id: str  # Stripe PaymentMethod ID


class OrderOut(BaseModel):
    id: int
    buyer_id: int
    product_id: int
    amount_paid: float
    platform_fee: float
    seller_earnings: float
    status: OrderStatus
    download_token: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DownloadLink(BaseModel):
    download_url: str
    expires_in_seconds: int = 3600
