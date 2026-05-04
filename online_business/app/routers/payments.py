from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.subscription import SubscriptionOut, SubscriptionUpgrade
from app.middleware.auth import get_current_user, require_seller
from app.models.user import User
from app.models.subscription import Subscription
from app.services.payment_service import create_pro_subscription, cancel_subscription, boost_product
from app.models.product import Product

router = APIRouter(prefix="/payments", tags=["Payments & Subscriptions"])


@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == seller.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    return sub


@router.post("/subscription/upgrade", response_model=SubscriptionOut)
def upgrade_to_pro(
    payload: SubscriptionUpgrade,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    sub = create_pro_subscription(db, seller, payload.payment_method_id)
    return sub


@router.post("/subscription/cancel", response_model=SubscriptionOut)
def cancel_pro(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    sub = cancel_subscription(db, seller)
    if not sub:
        raise HTTPException(status_code=400, detail="No active Pro subscription to cancel")
    return sub


@router.post("/products/{product_id}/boost", response_model=dict)
def boost_listing(
    product_id: int,
    payload: SubscriptionUpgrade,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    boosted = boost_product(db, product, payload.payment_method_id)
    return {"featured_until": str(boosted.featured_until), "message": "Product boosted for 7 days"}


@router.post("/withdraw", response_model=dict)
def withdraw_balance(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    if seller.balance < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $10.00")
    amount = seller.balance
    seller.balance = 0.0
    db.commit()
    # In production: initiate Stripe payout to seller's bank account
    return {"withdrawn": amount, "message": f"${amount:.2f} payout initiated (arrives in 2-3 business days)"}
