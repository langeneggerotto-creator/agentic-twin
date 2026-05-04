from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionUpgrade(BaseModel):
    payment_method_id: str  # Stripe PaymentMethod ID


class AnalyticsSummary(BaseModel):
    total_revenue: float
    total_platform_fees: float
    total_orders: int
    total_products: int
    total_users: int
    top_products: list
    revenue_by_category: dict
