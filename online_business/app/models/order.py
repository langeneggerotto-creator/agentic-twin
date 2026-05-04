from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    disputed = "disputed"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    amount_paid = Column(Float, nullable=False)       # total buyer paid (USD)
    platform_fee = Column(Float, nullable=False)      # platform's cut
    seller_earnings = Column(Float, nullable=False)   # seller's net
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_intent_id = Column(String, nullable=True) # Stripe PaymentIntent ID
    download_token = Column(String, nullable=True)    # secure one-time download link token
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    product = relationship("Product", back_populates="orders")
    review = relationship("Review", back_populates="order", uselist=False)
