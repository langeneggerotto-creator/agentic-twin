from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.buyer

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed)")
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    balance: float
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: int
    username: str
    role: UserRole
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
