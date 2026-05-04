from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.buyer, nullable=False)
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0.0)  # seller earnings wallet
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    orders_as_buyer = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    reviews = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
