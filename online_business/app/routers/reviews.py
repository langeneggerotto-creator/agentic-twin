from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.review import ReviewCreate, ReviewOut
from app.middleware.auth import get_current_user
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    order = db.query(Order).filter(
        Order.id == payload.order_id,
        Order.buyer_id == buyer.id,
        Order.status == OrderStatus.completed,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Completed order not found")
    if order.review:
        raise HTTPException(status_code=409, detail="Review already submitted for this order")

    review = Review(
        order_id=order.id,
        reviewer_id=buyer.id,
        product_id=order.product_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)

    # Recalculate product avg_rating
    product = db.query(Product).filter(Product.id == order.product_id).first()
    all_ratings = [r.rating for r in product.reviews] + [payload.rating]
    product.avg_rating = round(sum(all_ratings) / len(all_ratings), 2)
    product.review_count = len(all_ratings)

    db.commit()
    db.refresh(review)
    return review


@router.get("/product/{product_id}", response_model=List[ReviewOut])
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
