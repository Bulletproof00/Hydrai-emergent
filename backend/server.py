from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import ccxt.async_support as ccxt
import redis.asyncio as redis
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator
from ta.volume import MFIIndicator, OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
from ta.volatility import BollingerBands
from ta.trend import EMAIndicator
import asyncio
import yfinance as yf
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Redis connection
redis_client = None

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Exchange instance (Binance)
exchange = None

# Active WebSocket connections
active_connections: List[WebSocket] = []

# ============= MODELS =============
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessageCreate(BaseModel):
    session_id: str
    content: str

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = "New Session"

class IndicatorRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    limit: int = 100
    indicators: List[str]  # ['rsi', 'mfi', 'bollinger']

class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy: str = "rsi_crossover"
    params: Dict[str, Any] = {}

class PluginInfo(BaseModel):
    name: str
    type: str  # 'indicator', 'strategy', 'datasource'
    status: str  # 'active', 'inactive'
    description: str
    version: str = "1.0.0"

# ============= PLUGIN SYSTEM =============
class PluginManager:
    def __init__(self):
        self.plugins = {
            'indicators': {
                'rsi': {
                    'name': 'RSI',
                    'description': 'Relative Strength Index - Momentum indicator',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'mfi': {
                    'name': 'MFI',
                    'description': 'Money Flow Index - Volume-weighted momentum',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'bollinger': {
                    'name': 'Bollinger Bands',
                    'description': 'Volatility indicator with upper and lower bands',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'stochastic': {
                    'name': 'Stochastic Oscillator',
                    'description': 'Momentum indicator comparing closing price to price range',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'stoch_rsi': {
                    'name': 'Stochastic RSI',
                    'description': 'Stochastic applied to RSI values',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'obv': {
                    'name': 'OBV',
                    'description': 'On Balance Volume - Cumulative volume indicator',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'vwap': {
                    'name': 'VWAP',
                    'description': 'Volume Weighted Average Price',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'ema50': {
                    'name': 'EMA 50',
                    'description': 'Exponential Moving Average (50 periods)',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'ema200': {
                    'name': 'EMA 200',
                    'description': 'Exponential Moving Average (200 periods)',
                    'status': 'active',
                    'version': '1.0.0'
                }
            },
            'strategies': {
                'rsi_crossover': {
                    'name': 'RSI Crossover',
                    'description': 'Simple RSI-based strategy',
                    'status': 'active',
                    'version': '1.0.0'
                }
            },
            'datasources': {
                'kraken': {
                    'name': 'Kraken',
                    'description': 'Kraken exchange data feed',
                    'status': 'active',
                    'version': '1.0.0'
                },
                'tradfi': {
                    'name': 'TradFi Markets',
                    'description': 'Traditional finance markets (stocks, indices, commodities)',
                    'status': 'active',
                    'version': '1.0.0'
                }
            }
        }
    
    def get_all_plugins(self):
        result = []
        for plugin_type, plugins in self.plugins.items():
            for key, plugin in plugins.items():
                result.append({
                    'id': key,
                    'type': plugin_type,
                    **plugin
                })
        return result
    
    async def calculate_rsi(self, data: pd.DataFrame, period: int = 14):
        rsi = RSIIndicator(close=data['close'], window=period)
        return rsi.rsi().iloc[-1] if len(data) > 0 else None
    
    async def calculate_mfi(self, data: pd.DataFrame, period: int = 14):
        mfi = MFIIndicator(
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume'],
            window=period
        )
        return mfi.money_flow_index().iloc[-1] if len(data) > 0 else None
    
    async def calculate_bollinger(self, data: pd.DataFrame, period: int = 20, std: int = 2):
        bb = BollingerBands(close=data['close'], window=period, window_dev=std)
        if len(data) > 0:
            return {
                'upper': bb.bollinger_hband().iloc[-1],
                'middle': bb.bollinger_mavg().iloc[-1],
                'lower': bb.bollinger_lband().iloc[-1]
            }
        return None
    
    async def calculate_stochastic(self, data: pd.DataFrame, period: int = 14):
        stoch = StochasticOscillator(
            high=data['high'],
            low=data['low'],
            close=data['close'],
            window=period
        )
        if len(data) > 0:
            return {
                'k': stoch.stoch().iloc[-1],
                'd': stoch.stoch_signal().iloc[-1]
            }
        return None
    
    async def calculate_stoch_rsi(self, data: pd.DataFrame, period: int = 14):
        stoch_rsi = StochRSIIndicator(close=data['close'], window=period)
        if len(data) > 0:
            return {
                'k': stoch_rsi.stochrsi_k().iloc[-1],
                'd': stoch_rsi.stochrsi_d().iloc[-1]
            }
        return None
    
    async def calculate_obv(self, data: pd.DataFrame):
        obv = OnBalanceVolumeIndicator(close=data['close'], volume=data['volume'])
        return obv.on_balance_volume().iloc[-1] if len(data) > 0 else None
    
    async def calculate_vwap(self, data: pd.DataFrame):
        vwap = VolumeWeightedAveragePrice(
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume']
        )
        return vwap.volume_weighted_average_price().iloc[-1] if len(data) > 0 else None
    
    async def calculate_ema(self, data: pd.DataFrame, period: int = 50):
        ema = EMAIndicator(close=data['close'], window=period)
        return ema.ema_indicator().iloc[-1] if len(data) > 0 else None
    
    async def calculate_volume_pvsra(self, data: pd.DataFrame):
        """Volume Profile with Support and Resistance Areas"""
        if len(data) < 20:
            return None
        
        volumes = data['volume'].values
        avg_volume = np.mean(volumes[-20:])
        std_volume = np.std(volumes[-20:])
        
        current_volume = volumes[-1]
        
        # Classify volume
        if current_volume > avg_volume + 2 * std_volume:
            classification = 'climax'
            strength = 'very_high'
        elif current_volume > avg_volume + std_volume:
            classification = 'rising'
            strength = 'high'
        elif current_volume > avg_volume:
            classification = 'normal'
            strength = 'medium'
        else:
            classification = 'low'
            strength = 'low'
        
        return {
            'current_volume': float(current_volume),
            'average_volume': float(avg_volume),
            'classification': classification,
            'strength': strength
        }

plugin_manager = PluginManager()

# ============= DATA SOURCES =============
async def get_market_data(symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100):
    """Fetch OHLCV data from Binance"""
    try:
        if exchange is None:
            raise HTTPException(status_code=500, detail="Exchange not initialized")
        
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    except Exception as e:
        logging.error(f"Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_live_price(symbol: str = "BTC/USDT"):
    """Get current ticker price"""
    try:
        if exchange is None:
            raise HTTPException(status_code=500, detail="Exchange not initialized")
        
        ticker = await exchange.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'volume_24h': ticker['quoteVolume'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logging.error(f"Error fetching live price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_macro_data():
    """Fetch macro market data for correlation analysis"""
    try:
        macro_data = {}
        
        # Traditional Markets using yfinance (synchronous, run in thread)
        def fetch_tradfi():
            tickers = {
                'NASDAQ': '^IXIC',
                'SPX': '^GSPC',
                'DXY': 'DX-Y.NYB',  # US Dollar Index
                'Gold': 'GC=F',
                'Russell2000': '^RUT'
            }
            
            data = {}
            for name, symbol in tickers.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Open'].iloc[-1]
                        change = ((current - prev) / prev) * 100
                        data[name] = {
                            'price': float(current),
                            'change_24h': float(change)
                        }
                except Exception as e:
                    logging.warning(f"Error fetching {name}: {str(e)}")
                    data[name] = {'price': 0, 'change_24h': 0}
            return data
        
        # Run tradfi fetch in thread pool
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tradfi_data = await asyncio.get_event_loop().run_in_executor(executor, fetch_tradfi)
        
        macro_data.update(tradfi_data)
        
        # Crypto market data from exchange
        if exchange:
            try:
                # Bitcoin
                btc_ticker = await exchange.fetch_ticker('BTC/USDT')
                macro_data['Bitcoin'] = {
                    'price': btc_ticker['last'],
                    'change_24h': btc_ticker['percentage']
                }
                
                # Ethereum
                eth_ticker = await exchange.fetch_ticker('ETH/USDT')
                macro_data['Ethereum'] = {
                    'price': eth_ticker['last'],
                    'change_24h': eth_ticker['percentage']
                }
                
                # Calculate Total Crypto Market Cap (approximate)
                btc_market_cap = btc_ticker['last'] * 19_500_000  # ~19.5M BTC
                eth_market_cap = eth_ticker['last'] * 120_000_000  # ~120M ETH
                total_market_cap = btc_market_cap + eth_market_cap * 1.5  # Rough estimate
                
                macro_data['TotalCryptoMarketCap'] = {
                    'value': float(total_market_cap),
                    'unit': 'USD'
                }
                
                # Bitcoin Dominance (BTC market cap / Total market cap)
                btc_dominance = (btc_market_cap / total_market_cap) * 100
                macro_data['BitcoinDominance'] = {
                    'percentage': float(btc_dominance)
                }
                
                # USDT Market Cap (mock - would need CoinGecko API for real data)
                macro_data['USDTDominance'] = {
                    'percentage': 7.5  # Approximate
                }
                
            except Exception as e:
                logging.warning(f"Error fetching crypto data: {str(e)}")
        
        return macro_data
        
    except Exception as e:
        logging.error(f"Error fetching macro data: {str(e)}")
        return {}

async def calculate_correlations(timeframe: str = "1d", period: int = 30):
    """Calculate correlations between different assets"""
    try:
        correlations = {}
        
        # Fetch historical data for multiple assets
        def fetch_historical_tradfi():
            symbols = {
                'BTC': yf.Ticker('BTC-USD'),
                'ETH': yf.Ticker('ETH-USD'),
                'SPX': yf.Ticker('^GSPC'),
                'NASDAQ': yf.Ticker('^IXIC'),
                'Gold': yf.Ticker('GC=F'),
                'DXY': yf.Ticker('DX-Y.NYB')
            }
            
            data = {}
            for name, ticker in symbols.items():
                try:
                    hist = ticker.history(period='30d')
                    if not hist.empty:
                        data[name] = hist['Close'].values
                except:
                    pass
            return data
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            historical_data = await asyncio.get_event_loop().run_in_executor(executor, fetch_historical_tradfi)
        
        # Calculate correlations
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC']
            min_length = len(btc_data)
            
            for asset, asset_data in historical_data.items():
                if asset != 'BTC' and len(asset_data) >= min_length:
                    # Align lengths
                    length = min(len(btc_data), len(asset_data))
                    btc_aligned = btc_data[-length:]
                    asset_aligned = asset_data[-length:]
                    
                    # Calculate Pearson correlation
                    if length > 1:
                        corr, _ = pearsonr(btc_aligned, asset_aligned)
                        correlations[f'BTC_vs_{asset}'] = float(corr)
        
        return correlations
        
    except Exception as e:
        logging.error(f"Error calculating correlations: {str(e)}")
        return {}

# ============= AI ANALYSIS =============
async def analyze_with_ai(user_message: str, market_data: Optional[Dict] = None):
    """Use LLM to analyze trading data"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        system_message = """Du bist Hydra AI, ein hochentwickelter Trading-Analyse-Assistent. 
        Du analysierst Kryptowährungsmärkte, technische Indikatoren und gibst fundierte Einschätzungen.
        Antworte präzise, professionell und in deutscher Sprache."""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Add market context if available
        context = ""
        if market_data:
            context = f"\n\nAktuelle Marktdaten:\n{json.dumps(market_data, indent=2)}"
        
        user_msg = UserMessage(text=user_message + context)
        response = await chat.send_message(user_msg)
        
        return response
    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        return f"Fehler bei der KI-Analyse: {str(e)}"

# ============= BACKTESTING =============
async def run_backtest(request: BacktestRequest):
    """Run a simple backtest"""
    try:
        # Fetch historical data
        data = await get_market_data(request.symbol, request.timeframe, limit=500)
        
        if request.strategy == "rsi_crossover":
            # Calculate RSI
            rsi_period = request.params.get('rsi_period', 14)
            oversold = request.params.get('oversold', 30)
            overbought = request.params.get('overbought', 70)
            
            rsi = RSIIndicator(close=data['close'], window=rsi_period)
            data['rsi'] = rsi.rsi()
            
            # Simple strategy: Buy when RSI < oversold, Sell when RSI > overbought
            data['signal'] = 0
            data.loc[data['rsi'] < oversold, 'signal'] = 1  # Buy
            data.loc[data['rsi'] > overbought, 'signal'] = -1  # Sell
            
            # Calculate returns
            data['returns'] = data['close'].pct_change()
            data['strategy_returns'] = data['signal'].shift(1) * data['returns']
            
            total_return = (1 + data['strategy_returns']).prod() - 1
            win_rate = len(data[data['strategy_returns'] > 0]) / len(data[data['strategy_returns'] != 0])
            
            trades = data[data['signal'] != 0].to_dict('records')
            
            return {
                'strategy': request.strategy,
                'total_return': float(total_return * 100),
                'win_rate': float(win_rate * 100),
                'total_trades': len(trades),
                'profitable_trades': len(data[data['strategy_returns'] > 0]),
                'params': request.params,
                'last_signal': int(data['signal'].iloc[-1]),
                'last_rsi': float(data['rsi'].iloc[-1]) if not pd.isna(data['rsi'].iloc[-1]) else None
            }
    except Exception as e:
        logging.error(f"Backtest error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= ROUTES =============
@api_router.get("/")
async def root():
    return {"message": "Hydra AI Trading System"}

@api_router.get("/plugins")
async def get_plugins():
    """Get all available plugins"""
    return plugin_manager.get_all_plugins()

@api_router.get("/price/{symbol}")
async def get_price(symbol: str = "BTC/USDT"):
    """Get live price for a symbol"""
    return await get_live_price(symbol.replace("-", "/"))

@api_router.post("/indicators")
async def calculate_indicators(request: IndicatorRequest):
    """Calculate technical indicators"""
    try:
        data = await get_market_data(request.symbol, request.timeframe, request.limit)
        
        result = {
            'symbol': request.symbol,
            'timeframe': request.timeframe,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'current_price': float(data['close'].iloc[-1]),
            'indicators': {}
        }
        
        for indicator in request.indicators:
            if indicator.lower() == 'rsi':
                rsi_value = await plugin_manager.calculate_rsi(data)
                result['indicators']['rsi'] = float(rsi_value) if rsi_value else None
            elif indicator.lower() == 'mfi':
                mfi_value = await plugin_manager.calculate_mfi(data)
                result['indicators']['mfi'] = float(mfi_value) if mfi_value else None
            elif indicator.lower() == 'bollinger':
                bb_values = await plugin_manager.calculate_bollinger(data)
                if bb_values:
                    result['indicators']['bollinger'] = {
                        'upper': float(bb_values['upper']),
                        'middle': float(bb_values['middle']),
                        'lower': float(bb_values['lower'])
                    }
        
        return result
    except Exception as e:
        logging.error(f"Indicator calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/backtest")
async def backtest(request: BacktestRequest):
    """Run a backtest"""
    return await run_backtest(request)

@api_router.get("/sessions")
async def get_sessions():
    """Get all chat sessions"""
    sessions = await db.chat_sessions.find().sort("created_at", -1).to_list(100)
    return [ChatSession(**session) for session in sessions]

@api_router.post("/sessions")
async def create_session():
    """Create a new chat session"""
    session = ChatSession()
    await db.chat_sessions.insert_one(session.dict())
    return session

@api_router.get("/messages/{session_id}")
async def get_messages(session_id: str):
    """Get messages for a session"""
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**msg) for msg in messages]

@api_router.post("/chat")
async def chat(message: ChatMessageCreate):
    """Send a chat message and get AI response"""
    try:
        # Save user message
        user_msg = ChatMessage(
            session_id=message.session_id,
            role="user",
            content=message.content
        )
        await db.chat_messages.insert_one(user_msg.dict())
        
        # Get live market data for context
        try:
            live_price = await get_live_price()
            market_data = await get_market_data(limit=50)
            
            # Calculate indicators
            rsi = await plugin_manager.calculate_rsi(market_data)
            mfi = await plugin_manager.calculate_mfi(market_data)
            bb = await plugin_manager.calculate_bollinger(market_data)
            
            context_data = {
                'price': live_price,
                'rsi': float(rsi) if rsi else None,
                'mfi': float(mfi) if mfi else None,
                'bollinger': bb
            }
        except Exception as e:
            logging.warning(f"Could not fetch market context: {str(e)}")
            context_data = None
        
        # Get AI response
        ai_response = await analyze_with_ai(message.content, context_data)
        
        # Save assistant response
        assistant_msg = ChatMessage(
            session_id=message.session_id,
            role="assistant",
            content=ai_response
        )
        await db.chat_messages.insert_one(assistant_msg.dict())
        
        return assistant_msg
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for live price updates
@app.websocket("/ws/price")
async def websocket_price(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            try:
                price_data = await get_live_price()
                await websocket.send_json(price_data)
            except Exception as e:
                logging.error(f"WebSocket error: {str(e)}")
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    global exchange, redis_client
    logger.info("Starting Hydra AI...")
    
    # Initialize exchange - Try Kraken as it has less restrictions
    try:
        exchange = ccxt.kraken({
            'enableRateLimit': True,
        })
        logger.info("Kraken exchange initialized")
    except Exception as e:
        logger.warning(f"Kraken initialization failed, trying Binance: {str(e)}")
        try:
            exchange = ccxt.binance({
                'enableRateLimit': True,
            })
            logger.info("Binance exchange initialized")
        except Exception as e2:
            logger.error(f"Exchange initialization failed: {str(e2)}")
            # Use mock data as fallback
            exchange = None
    
    # Initialize Redis
    try:
        redis_client = await redis.from_url('redis://localhost:6379')
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {str(e)}")
    
    logger.info("Hydra AI started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    if exchange:
        await exchange.close()
    if redis_client:
        await redis_client.close()
    client.close()
    logger.info("Hydra AI shutdown complete")