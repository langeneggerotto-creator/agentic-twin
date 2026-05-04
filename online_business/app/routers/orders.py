from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.order import OrderCreate, OrderOut, DownloadLink
from app.middleware.auth import get_current_user
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.payment_service import process_order
from app.services.email_service import send_order_confirmation, send_sale_notification

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot purchase your own product")

    # Prevent duplicate purchase
    existing = db.query(Order).filter(
        Order.buyer_id == buyer.id,
        Order.product_id == product.id,
        Order.status == OrderStatus.completed,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already own this product")

    order = process_order(db, buyer, product, payload.payment_method_id)
    if not order:
        raise HTTPException(status_code=402, detail="Payment failed")

    seller = db.query(User).filter(User.id == product.seller_id).first()
    send_order_confirmation(buyer.email, product.title, order.download_token)
    send_sale_notification(seller.email, product.title, order.seller_earnings)
    return order


@router.get("/my", response_model=List[OrderOut])
def my_orders(buyer: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.buyer_id == buyer.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}/download", response_model=DownloadLink)
def get_download_link(
    order_id: int,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == buyer.id,
        Order.status == OrderStatus.completed,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    product = db.query(Product).filter(Product.id == order.product_id).first()
    if not product or not product.file_url:
        raise HTTPException(status_code=404, detail="No file available for this product")

    # In production generate a signed S3 URL using the download_token
    return DownloadLink(
        download_url=f"{product.file_url}?token={order.download_token}",
        expires_in_seconds=3600,
    )


@router.get("/seller/sales", response_model=List[OrderOut])
def my_sales(seller: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product_ids = [p.id for p in seller.products]
    if not product_ids:
        return []
    return (
        db.query(Order)
        .filter(Order.product_id.in_(product_ids), Order.status == OrderStatus.completed)
        .order_by(Order.created_at.desc())
        .all()
    )
