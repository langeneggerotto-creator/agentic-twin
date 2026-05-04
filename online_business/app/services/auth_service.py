"""
JWT auth using stdlib hmac + hashlib (HS256). No cryptography package needed.
Password hashing via bcrypt directly.
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.schemas.user import TokenData


# ---- Password hashing ----

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---- JWT (HS256) — pure stdlib ----

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def create_access_token(user_id: int) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    exp = int(time.time()) + settings.access_token_expire_minutes * 60
    payload = _b64url_encode(json.dumps({"sub": str(user_id), "exp": exp}).encode())
    signing_input = f"{header}.{payload}".encode()
    sig = hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url_encode(sig)}"


def decode_token(token: str) -> Optional[TokenData]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        signing_input = f"{header}.{payload}".encode()
        expected_sig = hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_decode(sig), expected_sig):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return TokenData(user_id=int(data["sub"]))
    except Exception:
        return None


# ---- DB helpers ----

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
