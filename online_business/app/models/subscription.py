from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SubscriptionPlan(str, enum.Enum):
    free = "free"
    pro = "pro"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    past_due = "past_due"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.free, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscription")
