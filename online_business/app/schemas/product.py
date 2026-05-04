from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from app.models.product import ProductCategory


class ProductCreate(BaseModel):
    title: str
    description: str
    category: ProductCategory
    price: float
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 9999:
            raise ValueError("Price cannot exceed $9,999")
        return round(v, 2)

    @field_validator("title")
    @classmethod
    def title_length(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Title must be at least 5 characters")
        return v.strip()


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    price: Optional[float] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    seller_id: int
    title: str
    description: str
    category: ProductCategory
    price: float
    thumbnail_url: Optional[str]
    is_featured: bool
    is_active: bool
    sales_count: int
    avg_rating: float
    review_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductDetail(ProductOut):
    file_url: Optional[str] = None  # only included after purchase
