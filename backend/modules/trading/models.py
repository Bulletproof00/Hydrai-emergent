from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid

class TradeCreate(BaseModel):
    symbol: str
    side: Literal["long", "short"]
    leverage: int = Field(ge=1, le=125, default=1)
    amount: float = Field(gt=0)
    entry_price: Optional[float] = None  # If None, use current market price
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class TradeClose(BaseModel):
    trade_id: str
    exit_price: Optional[float] = None  # If None, use current market price

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symbol: str
    side: Literal["long", "short"]
    leverage: int
    amount: float
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: Literal["open", "closed"] = "open"
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None

class Portfolio(BaseModel):
    balance: float
    open_trades: list[Trade]
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
