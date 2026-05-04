from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserOut, UserUpdate, UserPublic
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.bio is not None:
        current_user.bio = payload.bio
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}", response_model=UserPublic)
def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
