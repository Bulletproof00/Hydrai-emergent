from fastapi import APIRouter, HTTPException, Header
from .models import TradeCreate, TradeClose, Trade, Portfolio
from datetime import datetime, timezone
import ccxt.async_support as ccxt

exchange_instance = None

def get_exchange():
    global exchange_instance
    if not exchange_instance:
        exchange_instance = ccxt.kraken({'enableRateLimit': True})
    return exchange_instance

def create_trading_router(db):
    router = APIRouter(prefix="/trading", tags=["paper-trading"])
    
    # Import get_current_user function
    from ..auth.utils import decode_access_token
    
    async def get_current_user(authorization: str = Header(None)):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = authorization.split(' ')[1]
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("sub")
        user = await db.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    @router.post("/open-trade", response_model=Trade)
    async def open_trade(trade_data: TradeCreate, authorization: str = Header(None)):
    """Open a new paper trade"""
    exchange = get_exchange()
    
    # Get current market price if not provided
    if trade_data.entry_price is None:
        ticker = await exchange.fetch_ticker(trade_data.symbol)
        trade_data.entry_price = ticker['last']
    
    # Calculate position size with leverage
    position_value = trade_data.amount * trade_data.leverage
    required_balance = trade_data.amount
    
    # Check if user has enough balance
    user_balance = current_user.get("paper_trading_balance", 10000.0)
    if required_balance > user_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create trade
    trade = Trade(
        user_id=current_user["_id"],
        symbol=trade_data.symbol,
        side=trade_data.side,
        leverage=trade_data.leverage,
        amount=trade_data.amount,
        entry_price=trade_data.entry_price,
        stop_loss=trade_data.stop_loss,
        take_profit=trade_data.take_profit
    )
    
    # Save trade to database
    trade_dict = trade.dict()
    trade_dict["opened_at"] = trade_dict["opened_at"].isoformat()
    await db.trades.insert_one(trade_dict)
    
    # Update user balance
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"paper_trading_balance": -required_balance}}
    )
    
    return trade

@router.post("/close-trade", response_model=Trade)
async def close_trade(close_data: TradeClose, current_user = Depends(get_current_user), db = None):
    """Close an open paper trade"""
    trade = await db.trades.find_one({"id": close_data.trade_id, "user_id": current_user["_id"]})
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade["status"] == "closed":
        raise HTTPException(status_code=400, detail="Trade already closed")
    
    exchange = get_exchange()
    
    # Get current market price if not provided
    exit_price = close_data.exit_price
    if exit_price is None:
        ticker = await exchange.fetch_ticker(trade["symbol"])
        exit_price = ticker['last']
    
    # Calculate PnL
    price_diff = exit_price - trade["entry_price"]
    if trade["side"] == "short":
        price_diff = -price_diff
    
    pnl_percentage = (price_diff / trade["entry_price"]) * 100 * trade["leverage"]
    pnl = (trade["amount"] * pnl_percentage) / 100
    
    # Update trade
    closed_at = datetime.now(timezone.utc)
    await db.trades.update_one(
        {"id": close_data.trade_id},
        {"$set": {
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_percentage": pnl_percentage,
            "status": "closed",
            "closed_at": closed_at.isoformat()
        }}
    )
    
    # Update user balance (return initial amount + pnl)
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"paper_trading_balance": trade["amount"] + pnl}}
    )
    
    # Return updated trade
    trade["exit_price"] = exit_price
    trade["pnl"] = pnl
    trade["pnl_percentage"] = pnl_percentage
    trade["status"] = "closed"
    trade["closed_at"] = closed_at.isoformat()
    
    return Trade(**trade)

@router.get("/portfolio", response_model=Portfolio)
async def get_portfolio(current_user = Depends(get_current_user), db = None):
    """Get user's trading portfolio"""
    trades = await db.trades.find({"user_id": current_user["_id"]}).to_list(None)
    
    open_trades = [Trade(**t) for t in trades if t["status"] == "open"]
    closed_trades = [t for t in trades if t["status"] == "closed"]
    
    total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
    winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
    losing_trades = len([t for t in closed_trades if t.get("pnl", 0) < 0])
    win_rate = (winning_trades / len(closed_trades) * 100) if closed_trades else 0
    
    return Portfolio(
        balance=current_user.get("paper_trading_balance", 10000.0),
        open_trades=open_trades,
        total_pnl=total_pnl,
        total_trades=len(trades),
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate
    )

@router.get("/trades")
async def get_trades(current_user = Depends(get_current_user), db = None):
    """Get all user trades"""
    trades = await db.trades.find({"user_id": current_user["_id"]}).sort("opened_at", -1).to_list(None)
    return trades
