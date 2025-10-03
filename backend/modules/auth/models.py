from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str = Field(min_length=3)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: str
    paper_trading_balance: float = 10000.0

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserInDB(BaseModel):
    email: str
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paper_trading_balance: float = 10000.0
    trades: list = []
    saved_analyses: list = []
    backtest_results: list = []
