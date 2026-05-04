from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.services.auth_service import hash_password, authenticate_user, create_access_token, get_user_by_email
from app.services.email_service import send_welcome

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    # Provision a free subscription record for sellers
    if payload.role.value in ("seller", "admin"):
        db.add(Subscription(user_id=user.id, plan=SubscriptionPlan.free))

    db.commit()
    db.refresh(user)
    send_welcome(user.email, user.username)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    return Token(access_token=create_access_token(user.id))
