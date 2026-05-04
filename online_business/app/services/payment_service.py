"""
Stripe payment integration. In production replace mock responses with real stripe calls:
  pip install stripe
  import stripe; stripe.api_key = settings.stripe_secret_key
"""
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.config import settings
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus


def _get_commission_rate(seller: User) -> float:
    sub = seller.subscription
    if sub and sub.plan == SubscriptionPlan.pro and sub.status == SubscriptionStatus.active:
        return settings.pro_commission_rate
    return settings.platform_commission_rate


def create_payment_intent(amount_cents: int, payment_method_id: str) -> dict:
    """
    Mock Stripe PaymentIntent creation.
    Replace with: stripe.PaymentIntent.create(amount=amount_cents, currency="usd", ...)
    """
    return {
        "id": f"pi_mock_{secrets.token_hex(8)}",
        "status": "succeeded",
        "amount": amount_cents,
    }


def process_order(
    db: Session,
    buyer: User,
    product: Product,
    payment_method_id: str,
) -> Optional[Order]:
    intent = create_payment_intent(
        amount_cents=int(product.price * 100),
        payment_method_id=payment_method_id,
    )

    if intent["status"] != "succeeded":
        return None

    seller = db.query(User).filter(User.id == product.seller_id).first()
    commission = _get_commission_rate(seller)
    platform_fee = round(product.price * commission, 2)
    seller_earnings = round(product.price - platform_fee, 2)

    order = Order(
        buyer_id=buyer.id,
        product_id=product.id,
        amount_paid=product.price,
        platform_fee=platform_fee,
        seller_earnings=seller_earnings,
        status=OrderStatus.completed,
        payment_intent_id=intent["id"],
        download_token=secrets.token_urlsafe(32),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(order)

    # Credit seller wallet
    seller.balance = round(seller.balance + seller_earnings, 2)
    product.sales_count += 1

    db.commit()
    db.refresh(order)
    return order


def create_pro_subscription(db: Session, user: User, payment_method_id: str) -> Subscription:
    """
    Mock Stripe Subscription creation for Pro plan.
    Replace internals with real stripe.Subscription.create(...)
    """
    from datetime import timedelta
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    period_end = datetime.now(timezone.utc) + timedelta(days=30)

    if sub:
        sub.plan = SubscriptionPlan.pro
        sub.status = SubscriptionStatus.active
        sub.stripe_subscription_id = f"sub_mock_{secrets.token_hex(8)}"
        sub.current_period_end = period_end
        sub.cancel_at_period_end = False
    else:
        sub = Subscription(
            user_id=user.id,
            plan=SubscriptionPlan.pro,
            status=SubscriptionStatus.active,
            stripe_subscription_id=f"sub_mock_{secrets.token_hex(8)}",
            stripe_customer_id=f"cus_mock_{secrets.token_hex(8)}",
            current_period_end=period_end,
        )
        db.add(sub)

    db.commit()
    db.refresh(sub)
    return sub


def cancel_subscription(db: Session, user: User) -> Optional[Subscription]:
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub or sub.plan == SubscriptionPlan.free:
        return None
    sub.cancel_at_period_end = True
    # In production: stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
    db.commit()
    db.refresh(sub)
    return sub


def boost_product(db: Session, product: Product, payment_method_id: str) -> Product:
    """Charge $9.99 to feature a product for 7 days."""
    from datetime import timedelta
    intent = create_payment_intent(
        amount_cents=settings.featured_listing_price_cents,
        payment_method_id=payment_method_id,
    )
    if intent["status"] == "succeeded":
        product.is_featured = True
        product.featured_until = datetime.now(timezone.utc) + timedelta(days=7)
        db.commit()
        db.refresh(product)
    return product
