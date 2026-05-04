from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.middleware.auth import get_current_user, require_seller
from app.models.product import Product, ProductCategory
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[ProductCategory] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", enum=["created_at", "price", "sales_count", "avg_rating"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)
    if category:
        q = q.filter(Product.category == category)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if featured is not None:
        q = q.filter(Product.is_featured == featured)
    if search:
        q = q.filter(Product.title.ilike(f"%{search}%"))

    sort_col = getattr(Product, sort_by)
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    return q.offset(offset).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    product = Product(seller_id=seller.id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")
    product.is_active = False  # soft delete
    db.commit()


@router.get("/seller/{seller_id}", response_model=List[ProductOut])
def seller_products(seller_id: int, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.seller_id == seller_id, Product.is_active == True).all()
