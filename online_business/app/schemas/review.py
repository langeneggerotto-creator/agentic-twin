from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    order_id: int
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewOut(BaseModel):
    id: int
    order_id: int
    reviewer_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
