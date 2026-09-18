from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccountOut(BaseModel):
    id: int
    account_number: str
    balance: float

    class Config:
        from_attributes = True

class TransferRequest(BaseModel):
    sender_account_id: int
    receiver_account_id: int
    amount: float = Field(..., gt=0)

class TransactionOut(BaseModel):
    id: int
    sender_account_id: int
    receiver_account_id: int
    amount: float
    timestamp: datetime
    hmac_signature: str

    class Config:
        from_attributes = True