from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ProductCategory(str, enum.Enum):
    template = "template"
    ebook = "ebook"
    tool = "tool"
    course = "course"
    graphic = "graphic"
    plugin = "plugin"
    other = "other"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    price = Column(Float, nullable=False)          # in USD
    file_url = Column(String, nullable=True)       # downloadable file (S3, etc.)
    thumbnail_url = Column(String, nullable=True)
    is_featured = Column(Boolean, default=False)
    featured_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    sales_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    seller = relationship("User", back_populates="products")
    orders = relationship("Order", back_populates="product")
    reviews = relationship("Review", back_populates="product")
