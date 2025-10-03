from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Header
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
import google.generativeai as genai
from PIL import Image
import io
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Auth settings
import hashlib
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "hydra-secret-key-2024")
ALGORITHM = "HS256"

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Top 10 Coins
TOP_COINS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", 
             "SOL/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT", "LTC/USDT"]

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

# ============= AUTH HELPERS =============
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    from datetime import timedelta
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

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

# ============= AUTH MODELS =============
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

# ============= TRADING MODELS =============
class TradeCreate(BaseModel):
    symbol: str
    side: Literal["long", "short"]
    leverage: int = Field(ge=1, le=125, default=1)
    amount: float = Field(gt=0)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

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
    opened_at: str
    closed_at: Optional[str] = None

# ============= EXISTING MODELS =============
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

# ============= PATTERN RECOGNITION =============
def detect_candlestick_patterns(data: pd.DataFrame):
    """Detect candlestick patterns"""
    patterns = []
    
    if len(data) < 3:
        return patterns
    
    # Get last 3 candles
    last_3 = data.tail(3)
    current = last_3.iloc[-1]
    prev = last_3.iloc[-2]
    prev_prev = last_3.iloc[-3] if len(last_3) > 2 else None
    
    body_current = abs(current['close'] - current['open'])
    body_prev = abs(prev['close'] - prev['open'])
    
    # Doji
    if body_current < (current['high'] - current['low']) * 0.1:
        patterns.append({
            'name': 'Doji',
            'type': 'neutral',
            'strength': 'medium',
            'description': 'Indecision in the market'
        })
    
    # Hammer
    lower_shadow = min(current['open'], current['close']) - current['low']
    upper_shadow = current['high'] - max(current['open'], current['close'])
    if lower_shadow > body_current * 2 and upper_shadow < body_current * 0.3:
        patterns.append({
            'name': 'Hammer',
            'type': 'bullish',
            'strength': 'strong',
            'description': 'Potential bullish reversal'
        })
    
    # Shooting Star
    if upper_shadow > body_current * 2 and lower_shadow < body_current * 0.3:
        patterns.append({
            'name': 'Shooting Star',
            'type': 'bearish',
            'strength': 'strong',
            'description': 'Potential bearish reversal'
        })
    
    # Bullish Engulfing
    if (prev['close'] < prev['open'] and  # Previous bearish
        current['close'] > current['open'] and  # Current bullish
        current['open'] < prev['close'] and
        current['close'] > prev['open']):
        patterns.append({
            'name': 'Bullish Engulfing',
            'type': 'bullish',
            'strength': 'very_strong',
            'description': 'Strong bullish reversal signal'
        })
    
    # Bearish Engulfing
    if (prev['close'] > prev['open'] and  # Previous bullish
        current['close'] < current['open'] and  # Current bearish
        current['open'] > prev['close'] and
        current['close'] < prev['open']):
        patterns.append({
            'name': 'Bearish Engulfing',
            'type': 'bearish',
            'strength': 'very_strong',
            'description': 'Strong bearish reversal signal'
        })
    
    # Three White Soldiers (bullish continuation)
    if prev_prev is not None:
        if (prev_prev['close'] > prev_prev['open'] and
            prev['close'] > prev['open'] and
            current['close'] > current['open'] and
            current['close'] > prev['close'] > prev_prev['close']):
            patterns.append({
                'name': 'Three White Soldiers',
                'type': 'bullish',
                'strength': 'very_strong',
                'description': 'Strong bullish continuation'
            })
    
    return patterns

def detect_divergences(data: pd.DataFrame):
    """Detect RSI and price divergences"""
    divergences = []
    
    if len(data) < 14:
        return divergences
    
    # Calculate RSI
    rsi = RSIIndicator(close=data['close'], window=14)
    data_with_rsi = data.copy()
    data_with_rsi['rsi'] = rsi.rsi()
    
    # Look for divergences in last 20 candles
    recent = data_with_rsi.tail(20)
    
    # Bullish divergence: Price making lower lows, RSI making higher lows
    price_lows = recent['low'].values
    rsi_values = recent['rsi'].values
    
    if len(price_lows) > 5:
        # Find local minima
        for i in range(2, len(price_lows) - 2):
            if price_lows[i] < price_lows[i-1] and price_lows[i] < price_lows[i+1]:
                # Check if RSI is making higher low
                if i > 5 and rsi_values[i] > rsi_values[i-5]:
                    divergences.append({
                        'type': 'Bullish Divergence',
                        'indicator': 'RSI',
                        'strength': 'strong',
                        'description': 'Price lower low, RSI higher low - potential reversal'
                    })
                    break
    
    # Bearish divergence: Price making higher highs, RSI making lower highs
    price_highs = recent['high'].values
    for i in range(2, len(price_highs) - 2):
        if price_highs[i] > price_highs[i-1] and price_highs[i] > price_highs[i+1]:
            if i > 5 and rsi_values[i] < rsi_values[i-5]:
                divergences.append({
                    'type': 'Bearish Divergence',
                    'indicator': 'RSI',
                    'strength': 'strong',
                    'description': 'Price higher high, RSI lower high - potential reversal'
                })
                break
    
    return divergences

def detect_chart_patterns(data: pd.DataFrame):
    """Detect chart patterns like triangles, head and shoulders, etc."""
    patterns = []
    
    if len(data) < 20:
        return patterns
    
    recent = data.tail(20)
    highs = recent['high'].values
    lows = recent['low'].values
    closes = recent['close'].values
    
    # Ascending Triangle
    upper_resistance = np.max(highs[-10:])
    if np.std(highs[-10:]) < (upper_resistance * 0.02):  # Flat top
        lower_lows = lows[-10:]
        if lower_lows[-1] > lower_lows[0]:  # Rising lows
            patterns.append({
                'name': 'Ascending Triangle',
                'type': 'bullish',
                'description': 'Bullish continuation pattern'
            })
    
    # Descending Triangle
    lower_support = np.min(lows[-10:])
    if np.std(lows[-10:]) < (lower_support * 0.02):  # Flat bottom
        upper_highs = highs[-10:]
        if upper_highs[-1] < upper_highs[0]:  # Falling highs
            patterns.append({
                'name': 'Descending Triangle',
                'type': 'bearish',
                'description': 'Bearish continuation pattern'
            })
    
    # Simple trend detection
    if closes[-1] > closes[-10] and all(closes[i] >= closes[i-1] for i in range(-5, 0, 1)):
        patterns.append({
            'name': 'Strong Uptrend',
            'type': 'bullish',
            'description': 'Consistent upward movement'
        })
    elif closes[-1] < closes[-10] and all(closes[i] <= closes[i-1] for i in range(-5, 0, 1)):
        patterns.append({
            'name': 'Strong Downtrend',
            'type': 'bearish',
            'description': 'Consistent downward movement'
        })
    
    return patterns

async def analyze_chart_with_gemini(data: pd.DataFrame, indicators_data: dict):
    """Use Gemini Vision API to analyze chart patterns"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            return "Gemini API key not configured"
        
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Prepare analysis prompt
        prompt = f"""Analysiere diesen Bitcoin Trading-Chart professionell.

Aktuelle Daten:
- Preis: ${data['close'].iloc[-1]:.2f}
- 24h Änderung: {((data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2] * 100):.2f}%
- Volumen: {data['volume'].iloc[-1]:.2f}

Indikatoren:
{json.dumps(indicators_data, indent=2)}

Bitte analysiere:
1. Candlestick-Muster (Doji, Hammer, Engulfing, etc.)
2. Chart-Patterns (Triangles, Head & Shoulders, Wedges, Flags)
3. Divergenzen zwischen Preis und Indikatoren
4. Support/Resistance Levels
5. Trend-Richtung und Stärke
6. Trading-Empfehlung (Long/Short/Neutral)

Gib eine präzise, professionelle Analyse auf Deutsch."""
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini analysis error: {str(e)}")
        return f"Fehler bei der KI-Analyse: {str(e)}"

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

# ============= AUTH ROUTES =============
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    user_dict = {
        "_id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_balance": 10000.0,
        "trades": [],
        "saved_analyses": []
    }
    
    await db.users.insert_one(user_dict)
    access_token = create_access_token(data={"sub": user_id})
    
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        created_at=user_dict["created_at"],
        paper_trading_balance=10000.0
    )
    
    return Token(access_token=access_token, user=user_response)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user["_id"]})
    
    user_response = UserResponse(
        id=user["_id"],
        email=user["email"],
        username=user["username"],
        created_at=user["created_at"],
        paper_trading_balance=user.get("paper_trading_balance", 10000.0)
    )
    
    return Token(access_token=access_token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    return UserResponse(
        id=user["_id"],
        email=user["email"],
        username=user["username"],
        created_at=user["created_at"],
        paper_trading_balance=user.get("paper_trading_balance", 10000.0)
    )

# ============= TRADING ROUTES =============
@api_router.post("/trading/open", response_model=Trade)
async def open_trade(trade_data: TradeCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    # Get current market price if not provided
    if trade_data.entry_price is None:
        ticker = await exchange.fetch_ticker(trade_data.symbol)
        trade_data.entry_price = ticker['last']
    
    required_balance = trade_data.amount
    user_balance = user.get("paper_trading_balance", 10000.0)
    
    if required_balance > user_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    trade = Trade(
        user_id=user["_id"],
        symbol=trade_data.symbol,
        side=trade_data.side,
        leverage=trade_data.leverage,
        amount=trade_data.amount,
        entry_price=trade_data.entry_price,
        stop_loss=trade_data.stop_loss,
        take_profit=trade_data.take_profit,
        opened_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.trades.insert_one(trade.dict())
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$inc": {"paper_trading_balance": -required_balance}}
    )
    
    return trade

@api_router.post("/trading/close/{trade_id}")
async def close_trade(trade_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    trade = await db.trades.find_one({"id": trade_id, "user_id": user["_id"]})
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] == "closed":
        raise HTTPException(status_code=400, detail="Trade already closed")
    
    ticker = await exchange.fetch_ticker(trade["symbol"])
    exit_price = ticker['last']
    
    price_diff = exit_price - trade["entry_price"]
    if trade["side"] == "short":
        price_diff = -price_diff
    
    pnl_percentage = (price_diff / trade["entry_price"]) * 100 * trade["leverage"]
    pnl = (trade["amount"] * pnl_percentage) / 100
    
    closed_at = datetime.now(timezone.utc).isoformat()
    
    await db.trades.update_one(
        {"id": trade_id},
        {"$set": {
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_percentage": pnl_percentage,
            "status": "closed",
            "closed_at": closed_at
        }}
    )
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$inc": {"paper_trading_balance": trade["amount"] + pnl}}
    )
    
    return {"success": True, "pnl": pnl, "pnl_percentage": pnl_percentage}

@api_router.get("/trading/portfolio")
async def get_portfolio(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    trades = await db.trades.find({"user_id": user["_id"]}).to_list(None)
    
    # Remove MongoDB ObjectId
    for trade in trades:
        if '_id' in trade:
            del trade['_id']
    
    open_trades = [t for t in trades if t["status"] == "open"]
    closed_trades = [t for t in trades if t["status"] == "closed"]
    
    total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
    winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
    losing_trades = len([t for t in closed_trades if t.get("pnl", 0) < 0])
    win_rate = (winning_trades / len(closed_trades) * 100) if closed_trades else 0
    
    return {
        "balance": user.get("paper_trading_balance", 10000.0),
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "total_pnl": total_pnl,
        "total_trades": len(trades),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate
    }

@api_router.get("/coins")
async def get_available_coins():
    return {"coins": TOP_COINS}

# ============= EXISTING ROUTES =============
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
            ind_lower = indicator.lower()
            
            if ind_lower == 'rsi':
                rsi_value = await plugin_manager.calculate_rsi(data)
                result['indicators']['rsi'] = float(rsi_value) if rsi_value else None
            elif ind_lower == 'mfi':
                mfi_value = await plugin_manager.calculate_mfi(data)
                result['indicators']['mfi'] = float(mfi_value) if mfi_value else None
            elif ind_lower == 'bollinger':
                bb_values = await plugin_manager.calculate_bollinger(data)
                if bb_values:
                    result['indicators']['bollinger'] = {
                        'upper': float(bb_values['upper']),
                        'middle': float(bb_values['middle']),
                        'lower': float(bb_values['lower'])
                    }
            elif ind_lower == 'stochastic':
                stoch_values = await plugin_manager.calculate_stochastic(data)
                if stoch_values:
                    result['indicators']['stochastic'] = {
                        'k': float(stoch_values['k']),
                        'd': float(stoch_values['d'])
                    }
            elif ind_lower == 'stoch_rsi':
                stoch_rsi_values = await plugin_manager.calculate_stoch_rsi(data)
                if stoch_rsi_values:
                    result['indicators']['stoch_rsi'] = {
                        'k': float(stoch_rsi_values['k']),
                        'd': float(stoch_rsi_values['d'])
                    }
            elif ind_lower == 'obv':
                obv_value = await plugin_manager.calculate_obv(data)
                result['indicators']['obv'] = float(obv_value) if obv_value else None
            elif ind_lower == 'vwap':
                vwap_value = await plugin_manager.calculate_vwap(data)
                result['indicators']['vwap'] = float(vwap_value) if vwap_value else None
            elif ind_lower == 'ema50':
                ema50_value = await plugin_manager.calculate_ema(data, 50)
                result['indicators']['ema50'] = float(ema50_value) if ema50_value else None
            elif ind_lower == 'ema200':
                ema200_value = await plugin_manager.calculate_ema(data, 200)
                result['indicators']['ema200'] = float(ema200_value) if ema200_value else None
            elif ind_lower == 'volume_pvsra':
                pvsra_value = await plugin_manager.calculate_volume_pvsra(data)
                result['indicators']['volume_pvsra'] = pvsra_value
        
        return result
    except Exception as e:
        logging.error(f"Indicator calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/backtest")
async def backtest(request: BacktestRequest):
    """Run a backtest"""
    return await run_backtest(request)

@api_router.get("/macro-data")
async def get_macro_data_endpoint():
    """Get macro market data"""
    return await get_macro_data()

@api_router.get("/correlations")
async def get_correlations_endpoint():
    """Get asset correlations"""
    return await calculate_correlations()

@api_router.get("/market-overview")
async def get_market_overview():
    """Get comprehensive market overview"""
    try:
        # Fetch all data concurrently
        macro_data_task = asyncio.create_task(get_macro_data())
        correlations_task = asyncio.create_task(calculate_correlations())
        btc_price_task = asyncio.create_task(get_live_price("BTC/USDT"))
        
        macro_data = await macro_data_task
        correlations = await correlations_task
        btc_price = await btc_price_task
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'bitcoin': btc_price,
            'macro_data': macro_data,
            'correlations': correlations,
            'summary': {
                'market_sentiment': 'bullish' if btc_price.get('change_24h', 0) > 0 else 'bearish',
                'btc_dominance': macro_data.get('BitcoinDominance', {}).get('percentage', 0),
                'correlation_with_spx': correlations.get('BTC_vs_SPX', 0)
            }
        }
    except Exception as e:
        logging.error(f"Market overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chart-data/{symbol}")
async def get_chart_data(symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100):
    """Get OHLCV chart data for candlestick display"""
    try:
        # Convert symbol format (BTC-USDT to BTC/USDT)
        symbol = symbol.replace('-', '/')
        data = await get_market_data(symbol, timeframe, limit)
        
        # Convert to chart-friendly format
        chart_data = []
        for idx, row in data.iterrows():
            chart_data.append({
                'time': int(row['timestamp'].timestamp()),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'data': chart_data
        }
    except Exception as e:
        logging.error(f"Chart data error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze-patterns")
async def analyze_patterns_endpoint(request: IndicatorRequest):
    """Analyze candlestick patterns, divergences, and chart patterns"""
    try:
        data = await get_market_data(request.symbol, request.timeframe, request.limit)
        
        # Detect patterns
        candlestick_patterns = detect_candlestick_patterns(data)
        divergences = detect_divergences(data)
        chart_patterns = detect_chart_patterns(data)
        
        # Get indicators for context
        indicators = {}
        rsi = await plugin_manager.calculate_rsi(data)
        if rsi and not (np.isnan(rsi) or np.isinf(rsi)):
            indicators['rsi'] = float(rsi)
        
        ema50 = await plugin_manager.calculate_ema(data, 50)
        if ema50 and not (np.isnan(ema50) or np.isinf(ema50)):
            indicators['ema50'] = float(ema50)
        
        ema200 = await plugin_manager.calculate_ema(data, 200)
        if ema200 and not (np.isnan(ema200) or np.isinf(ema200)):
            indicators['ema200'] = float(ema200)
        
        # Gemini AI Analysis
        gemini_analysis = await analyze_chart_with_gemini(data, indicators)
        
        return {
            'symbol': request.symbol,
            'timeframe': request.timeframe,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'current_price': float(data['close'].iloc[-1]),
            'candlestick_patterns': candlestick_patterns,
            'divergences': divergences,
            'chart_patterns': chart_patterns,
            'indicators': indicators,
            'ai_analysis': gemini_analysis,
            'summary': {
                'bullish_signals': len([p for p in candlestick_patterns if p['type'] == 'bullish']) + len([p for p in chart_patterns if p['type'] == 'bullish']),
                'bearish_signals': len([p for p in candlestick_patterns if p['type'] == 'bearish']) + len([p for p in chart_patterns if p['type'] == 'bearish']),
                'has_divergence': len(divergences) > 0
            }
        }
    except Exception as e:
        logging.error(f"Pattern analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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