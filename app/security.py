import hmac
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db

# Config
SECRET_KEY = "super-secret-jwt-key-change-this"  #we just used this very simple key for the sake of ease and testing
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HMAC secret key encoded as bytes...
HMAC_SECRET_KEY = "super-secret-hmac-key".encode("utf-8") #we just used this very simple key for the sake of ease and testing

# data at rest encryption key
ENCRYPTION_KEY = "uP8Xy9k6H4A_wZ9vL1_R3T5Y7U9I1O3P5Q7R9S1T3U4=".encode("utf-8")
cipher = Fernet(ENCRYPTION_KEY)

#password hashing config
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#http bearer scheme
security_scheme = HTTPBearer()


# Password Hashing and Verification
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# data at rest encryption with fernet
def encrypt_sensitive_data(data: str) -> str:
    return cipher.encrypt(data.encode("utf-8")).decode("utf-8")


def decrypt_sensitive_data(token: str) -> str:
    return cipher.decrypt(token.encode("utf-8")).decode("utf-8")


# HMAC-SHA256 payload
def generate_hmac_signature(payload_bytes: bytes) -> str:
    if isinstance(payload_bytes, str):
        payload_bytes = payload_bytes.encode("utf-8")
    return hmac.new(HMAC_SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload_bytes: bytes, signature: str) -> bool:
    expected_signature = generate_hmac_signature(payload_bytes)
    return hmac.compare_digest(expected_signature, signature)


# JWT authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    from app import models  #import here to prevent circular dependency

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = auth.credentials  # extract the raw token string

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    if getattr(user, "is_locked", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")

    return user