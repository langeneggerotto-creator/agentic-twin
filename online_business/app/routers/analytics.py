from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/seller/dashboard")
def seller_dashboard(seller: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product_ids = [p.id for p in seller.products]
    orders = (
        db.query(Order)
        .filter(Order.product_id.in_(product_ids), Order.status == OrderStatus.completed)
        .all()
        if product_ids else []
    )
    total_revenue = sum(o.seller_earnings for o in orders)
    total_sales = len(orders)

    top_products = (
        db.query(Product.title, func.sum(Order.seller_earnings).label("revenue"), func.count(Order.id).label("sales"))
        .join(Order, Order.product_id == Product.id)
        .filter(Product.seller_id == seller.id, Order.status == OrderStatus.completed)
        .group_by(Product.id)
        .order_by(func.sum(Order.seller_earnings).desc())
        .limit(5)
        .all()
        if product_ids else []
    )

    sub = db.query(Subscription).filter(Subscription.user_id == seller.id).first()
    return {
        "total_earnings": round(total_revenue, 2),
        "wallet_balance": round(seller.balance, 2),
        "total_sales": total_sales,
        "total_products": len(seller.products),
        "subscription_plan": sub.plan if sub else "free",
        "top_products": [
            {"title": r.title, "revenue": round(r.revenue, 2), "sales": r.sales}
            for r in top_products
        ],
    }


@router.get("/admin/overview")
def admin_overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    completed_orders = db.query(Order).filter(Order.status == OrderStatus.completed).all()
    total_gmv = sum(o.amount_paid for o in completed_orders)
    total_fees = sum(o.platform_fee for o in completed_orders)

    revenue_by_category = {}
    for order in completed_orders:
        cat = order.product.category.value if order.product else "unknown"
        revenue_by_category[cat] = revenue_by_category.get(cat, 0) + order.platform_fee

    pro_subs = db.query(Subscription).filter(Subscription.plan == SubscriptionPlan.pro).count()
    monthly_sub_revenue = pro_subs * 29.0

    return {
        "total_gmv": round(total_gmv, 2),
        "total_platform_fees": round(total_fees, 2),
        "subscription_revenue": round(monthly_sub_revenue, 2),
        "total_revenue": round(total_fees + monthly_sub_revenue, 2),
        "total_orders": len(completed_orders),
        "total_products": db.query(Product).filter(Product.is_active == True).count(),
        "total_users": db.query(User).count(),
        "pro_subscribers": pro_subs,
        "revenue_by_category": {k: round(v, 2) for k, v in revenue_by_category.items()},
    }
