"""
KI-gestütztes Datenmodul für historische und Echtzeit-Marktanalyse
Umfassende Integration von OHLCV, Indikatoren, On-Chain, Sentiment und Makro-Daten
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
import json
from dataclasses import dataclass, asdict
import time

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Standardized market data structure"""
    timestamp: datetime
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str

@dataclass
class IndicatorData:
    """Technical indicator data structure"""
    timestamp: datetime
    symbol: str
    timeframe: str
    rsi: Optional[float] = None
    sma_20: Optional[float] = None
    ema_50: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    stochastic_k: Optional[float] = None
    mfi: Optional[float] = None

@dataclass
class OnChainData:
    """Bitcoin On-Chain data structure"""
    timestamp: datetime
    hash_rate: Optional[float] = None
    difficulty: Optional[float] = None
    active_addresses: Optional[int] = None
    transaction_count: Optional[int] = None
    network_value: Optional[float] = None
    mvrv_ratio: Optional[float] = None
    realized_cap: Optional[float] = None
    nvt_ratio: Optional[float] = None

@dataclass
class MacroData:
    """Macroeconomic data structure"""
    timestamp: datetime
    symbol: str  # M2, DXY, Russell2000, etc.
    value: float
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    change_30d: Optional[float] = None

@dataclass
class NewsData:
    """News and sentiment data structure"""
    timestamp: datetime
    title: str
    content: str
    source: str
    sentiment_score: Optional[float] = None  # -1 to 1
    impact_score: Optional[float] = None     # 0 to 1
    category: str = "general"

class AIDataModule:
    """Comprehensive AI-powered market data module"""
    
    def __init__(self, db):
        self.db = db
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        self.macro_symbols = ['M2', 'DXY', 'SPX', 'RUSSELL2000', 'GOLD', 'DJI', 'NASDAQ']
        
        # API endpoints
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.alpha_vantage_key = None  # Will be set via environment
        self.newsapi_key = None
        
        # Data quality tracking
        self.data_quality_scores = {}
        self.missing_data_ranges = {}
        
    async def initialize(self):
        """Initialize data collections and indices"""
        logger.info("🚀 Initializing AI Data Module...")
        
        # Create MongoDB collections with indices
        await self._create_collections()
        await self._create_indices()
        
        # Load initial data quality assessment
        await self.assess_data_quality()
        
        logger.info("✅ AI Data Module initialized")

    async def _create_collections(self):
        """Create MongoDB collections for different data types"""
        collections = [
            'market_data_historical',
            'indicator_data', 
            'onchain_data',
            'macro_data',
            'news_sentiment',
            'correlations',
            'data_quality_log',
            'backtesting_results'
        ]
        
        for collection in collections:
            if collection not in await self.db.list_collection_names():
                await self.db.create_collection(collection)
                logger.info(f"📊 Created collection: {collection}")

    async def _create_indices(self):
        """Create database indices for efficient queries"""
        indices = [
            ('market_data_historical', [('timestamp', 1), ('symbol', 1), ('timeframe', 1)]),
            ('indicator_data', [('timestamp', 1), ('symbol', 1), ('timeframe', 1)]),
            ('onchain_data', [('timestamp', 1)]),
            ('macro_data', [('timestamp', 1), ('symbol', 1)]),
            ('news_sentiment', [('timestamp', 1), ('sentiment_score', 1)]),
            ('correlations', [('timestamp', 1), ('asset_pair', 1)])
        ]
        
        for collection, index_spec in indices:
            await self.db[collection].create_index(index_spec)
            logger.debug(f"📊 Created index for {collection}")

    # ==================== DATA LOADING METHODS ====================
    
    async def load_historical_ohlcv_data(self, start_date: str = "2019-01-01") -> Dict[str, Any]:
        """Load comprehensive historical OHLCV data from 2019 to present"""
        logger.info(f"📈 Loading historical OHLCV data from {start_date}")
        
        results = {
            'loaded_symbols': [],
            'loaded_timeframes': [],
            'total_records': 0,
            'data_quality': {}
        }
        
        start_datetime = datetime.fromisoformat(start_date)
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                try:
                    # Load data from CoinGecko (free tier)
                    data_points = await self._fetch_coingecko_historical(
                        symbol, timeframe, start_datetime
                    )
                    
                    if data_points:
                        # Store in database
                        await self._store_market_data(data_points)
                        
                        results['loaded_symbols'].append(symbol)
                        results['loaded_timeframes'].append(f"{symbol}_{timeframe}")
                        results['total_records'] += len(data_points)
                        
                        # Calculate data quality
                        quality_score = await self._calculate_data_quality(data_points)
                        results['data_quality'][f"{symbol}_{timeframe}"] = quality_score
                        
                        logger.info(f"✅ Loaded {len(data_points)} records for {symbol} {timeframe}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)  # CoinGecko free tier protection
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load {symbol} {timeframe}: {e}")
        
        return results

    async def _fetch_coingecko_historical(self, symbol: str, timeframe: str, start_date: datetime) -> List[MarketDataPoint]:
        """Fetch historical data from CoinGecko API"""
        try:
            # Convert symbol to CoinGecko format
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return []
            
            # Calculate days from start_date to now
            days = (datetime.now() - start_date).days
            
            async with aiohttp.ClientSession() as session:
                # Get historical data
                url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': min(days, 365),  # CoinGecko limits
                    'interval': self._timeframe_to_interval(timeframe)
                }
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_coingecko_to_ohlcv(
                            data, symbol, timeframe
                        )
                    else:
                        logger.warning(f"CoinGecko API error {response.status} for {symbol}")
                        return []
        
        except Exception as e:
            logger.error(f"CoinGecko fetch error for {symbol}: {e}")
            return []

    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko ID"""
        symbol_map = {
            'BTC/USDT': 'bitcoin',
            'ETH/USDT': 'ethereum', 
            'BNB/USDT': 'binancecoin',
            'ADA/USDT': 'cardano',
            'SOL/USDT': 'solana'
        }
        return symbol_map.get(symbol)

    def _timeframe_to_interval(self, timeframe: str) -> str:
        """Convert timeframe to CoinGecko interval"""
        interval_map = {
            '1m': 'minutely',
            '5m': '5minutely', 
            '15m': '15minutely',
            '1h': 'hourly',
            '4h': '4hourly',
            '1d': 'daily',
            '1w': 'weekly',
            '1M': 'monthly'
        }
        return interval_map.get(timeframe, 'hourly')

    def _convert_coingecko_to_ohlcv(self, data: Dict, symbol: str, timeframe: str) -> List[MarketDataPoint]:
        """Convert CoinGecko data to standardized OHLCV format"""
        data_points = []
        
        if 'prices' in data and len(data['prices']) > 0:
            for i, price_point in enumerate(data['prices']):
                timestamp = datetime.fromtimestamp(price_point[0] / 1000, tz=timezone.utc)
                price = price_point[1]
                volume = data['total_volumes'][i][1] if i < len(data['total_volumes']) else 0
                
                # For CoinGecko, we only have price and volume, so we'll create OHLC
                data_points.append(MarketDataPoint(
                    timestamp=timestamp,
                    symbol=symbol,
                    timeframe=timeframe,
                    open=price,
                    high=price * 1.002,  # Approximate high
                    low=price * 0.998,   # Approximate low
                    close=price,
                    volume=volume,
                    source='coingecko'
                ))
        
        return data_points

    async def _store_market_data(self, data_points: List[MarketDataPoint]):
        """Store market data points in MongoDB"""
        if not data_points:
            return
        
        documents = []
        for point in data_points:
            doc = asdict(point)
            doc['_id'] = f"{point.symbol}_{point.timeframe}_{int(point.timestamp.timestamp())}"
            documents.append(doc)
        
        try:
            # Use upsert to avoid duplicates
            for doc in documents:
                await self.db.market_data_historical.update_one(
                    {'_id': doc['_id']},
                    {'$set': doc},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error storing market data: {e}")

    # ==================== INDICATOR CALCULATION ====================
    
    async def calculate_indicators_for_all_data(self) -> Dict[str, Any]:
        """Calculate technical indicators for all historical data"""
        logger.info("📊 Calculating technical indicators for all data...")
        
        results = {
            'processed_symbols': [],
            'indicator_counts': {},
            'calculation_time': 0
        }
        
        start_time = time.time()
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                try:
                    # Get market data
                    market_data = await self._get_market_data_for_calculation(symbol, timeframe)
                    
                    if len(market_data) >= 200:  # Need sufficient data for indicators
                        # Calculate indicators
                        indicators = await self._calculate_technical_indicators(market_data)
                        
                        # Store indicators
                        await self._store_indicator_data(indicators, symbol, timeframe)
                        
                        results['processed_symbols'].append(f"{symbol}_{timeframe}")
                        results['indicator_counts'][f"{symbol}_{timeframe}"] = len(indicators)
                        
                        logger.info(f"✅ Calculated {len(indicators)} indicators for {symbol} {timeframe}")
                    
                except Exception as e:
                    logger.error(f"❌ Indicator calculation failed for {symbol} {timeframe}: {e}")
        
        results['calculation_time'] = time.time() - start_time
        return results

    async def _get_market_data_for_calculation(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get market data as DataFrame for indicator calculation"""
        cursor = self.db.market_data_historical.find(
            {'symbol': symbol, 'timeframe': timeframe},
            sort=[('timestamp', 1)]
        )
        
        data = []
        async for doc in cursor:
            data.append({
                'timestamp': doc['timestamp'],
                'open': doc['open'],
                'high': doc['high'],
                'low': doc['low'],
                'close': doc['close'],
                'volume': doc['volume']
            })
        
        return pd.DataFrame(data)

    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> List[IndicatorData]:
        """Calculate comprehensive technical indicators"""
        indicators = []
        
        if len(df) < 200:
            return indicators
        
        # RSI (14 period)
        rsi_values = self._calculate_rsi(df['close'].values, 14)
        
        # Moving Averages
        sma_20 = df['close'].rolling(window=20).mean().values
        ema_50 = df['close'].ewm(span=50).mean().values
        
        # Bollinger Bands (20 period, 2 std)
        bb_middle = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        bb_upper = (bb_middle + (bb_std * 2)).values
        bb_lower = (bb_middle - (bb_std * 2)).values
        
        # MACD (12, 26, 9)
        macd_line, macd_signal = self._calculate_macd(df['close'].values)
        
        # Stochastic K% (14 period)
        stoch_k = self._calculate_stochastic(df['high'].values, df['low'].values, df['close'].values)
        
        # Money Flow Index (14 period)
        mfi = self._calculate_mfi(df['high'].values, df['low'].values, df['close'].values, df['volume'].values)
        
        # Combine all indicators
        for i in range(len(df)):
            if i >= 200:  # Ensure all indicators have valid values
                indicators.append(IndicatorData(
                    timestamp=df.iloc[i]['timestamp'],
                    symbol="",  # Will be set in caller
                    timeframe="",  # Will be set in caller
                    rsi=rsi_values[i] if i < len(rsi_values) else None,
                    sma_20=sma_20[i] if not np.isnan(sma_20[i]) else None,
                    ema_50=ema_50[i] if not np.isnan(ema_50[i]) else None,
                    bollinger_upper=bb_upper[i] if not np.isnan(bb_upper[i]) else None,
                    bollinger_lower=bb_lower[i] if not np.isnan(bb_lower[i]) else None,
                    macd=macd_line[i] if i < len(macd_line) else None,
                    macd_signal=macd_signal[i] if i < len(macd_signal) else None,
                    stochastic_k=stoch_k[i] if i < len(stoch_k) else None,
                    mfi=mfi[i] if i < len(mfi) else None
                ))
        
        return indicators

    def _calculate_rsi(self, prices: np.array, period: int = 14) -> np.array:
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.convolve(gains, np.ones(period), 'valid') / period
        avg_losses = np.convolve(losses, np.ones(period), 'valid') / period
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Pad with NaN for initial periods
        return np.concatenate([np.full(period, np.nan), rsi])

    def _calculate_macd(self, prices: np.array, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.array, np.array]:
        """Calculate MACD indicator"""
        prices_series = pd.Series(prices)
        
        ema_fast = prices_series.ewm(span=fast).mean()
        ema_slow = prices_series.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        
        return macd_line.values, macd_signal.values

    def _calculate_stochastic(self, highs: np.array, lows: np.array, closes: np.array, period: int = 14) -> np.array:
        """Calculate Stochastic K% indicator"""
        stoch_k = np.zeros_like(closes)
        
        for i in range(period - 1, len(closes)):
            highest_high = np.max(highs[i - period + 1:i + 1])
            lowest_low = np.min(lows[i - period + 1:i + 1])
            
            if highest_high != lowest_low:
                stoch_k[i] = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
            else:
                stoch_k[i] = 50
        
        return stoch_k

    def _calculate_mfi(self, highs: np.array, lows: np.array, closes: np.array, volumes: np.array, period: int = 14) -> np.array:
        """Calculate Money Flow Index"""
        typical_prices = (highs + lows + closes) / 3
        money_flow = typical_prices * volumes
        
        mfi = np.zeros_like(closes)
        
        for i in range(period, len(closes)):
            positive_flow = 0
            negative_flow = 0
            
            for j in range(i - period + 1, i + 1):
                if j > 0 and typical_prices[j] > typical_prices[j - 1]:
                    positive_flow += money_flow[j]
                elif j > 0 and typical_prices[j] < typical_prices[j - 1]:
                    negative_flow += money_flow[j]
            
            if negative_flow == 0:
                mfi[i] = 100
            else:
                money_flow_ratio = positive_flow / negative_flow
                mfi[i] = 100 - (100 / (1 + money_flow_ratio))
        
        return mfi

    async def _store_indicator_data(self, indicators: List[IndicatorData], symbol: str, timeframe: str):
        """Store calculated indicators in database"""
        documents = []
        
        for indicator in indicators:
            indicator.symbol = symbol
            indicator.timeframe = timeframe
            
            doc = asdict(indicator)
            doc['_id'] = f"{symbol}_{timeframe}_{int(indicator.timestamp.timestamp())}"
            documents.append(doc)
        
        try:
            for doc in documents:
                await self.db.indicator_data.update_one(
                    {'_id': doc['_id']},
                    {'$set': doc},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error storing indicator data: {e}")

    # ==================== DATA QUALITY ASSESSMENT ====================
    
    async def assess_data_quality(self) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        logger.info("🔍 Assessing data quality...")
        
        quality_report = {
            'overall_score': 0,
            'symbol_scores': {},
            'missing_data_ranges': {},
            'data_completeness': {},
            'bitcoin_dominance_check': {}
        }
        
        total_score = 0
        symbol_count = 0
        
        for symbol in self.symbols:
            symbol_quality = await self._assess_symbol_data_quality(symbol)
            quality_report['symbol_scores'][symbol] = symbol_quality
            total_score += symbol_quality['overall_score']
            symbol_count += 1
        
        quality_report['overall_score'] = total_score / symbol_count if symbol_count > 0 else 0
        
        # Check Bitcoin Dominance
        btc_dominance = await self._check_bitcoin_dominance()
        quality_report['bitcoin_dominance_check'] = btc_dominance
        
        # Store quality report
        await self._store_quality_report(quality_report)
        
        return quality_report

    async def _assess_symbol_data_quality(self, symbol: str) -> Dict[str, Any]:
        """Assess data quality for a specific symbol"""
        quality_metrics = {
            'overall_score': 0,
            'completeness': 0,
            'consistency': 0,
            'timeliness': 0,
            'missing_ranges': []
        }
        
        try:
            # Get data count per timeframe
            total_expected = 0
            total_actual = 0
            
            for timeframe in self.timeframes:
                expected_count = self._calculate_expected_data_points(timeframe)
                actual_count = await self.db.market_data_historical.count_documents({
                    'symbol': symbol,
                    'timeframe': timeframe
                })
                
                total_expected += expected_count
                total_actual += actual_count
            
            # Calculate completeness
            quality_metrics['completeness'] = (total_actual / total_expected * 100) if total_expected > 0 else 0
            
            # Calculate overall score (simplified)
            quality_metrics['overall_score'] = quality_metrics['completeness']
            
        except Exception as e:
            logger.error(f"Error assessing quality for {symbol}: {e}")
        
        return quality_metrics

    def _calculate_expected_data_points(self, timeframe: str) -> int:
        """Calculate expected number of data points since 2019"""
        start_date = datetime(2019, 1, 1)
        now = datetime.now()
        total_minutes = (now - start_date).total_seconds() / 60
        
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080,
            '1M': 43200  # Approximate
        }
        
        return int(total_minutes / timeframe_minutes.get(timeframe, 60))

    async def _check_bitcoin_dominance(self) -> Dict[str, Any]:
        """Check and correct Bitcoin Dominance (should be 59%)"""
        logger.info("₿ Checking Bitcoin Dominance...")
        
        try:
            # Fetch current Bitcoin dominance from CoinGecko
            async with aiohttp.ClientSession() as session:
                url = f"{self.coingecko_base}/global"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        current_dominance = data['data']['market_cap_percentage'].get('btc', 0)
                        
                        dominance_check = {
                            'current_dominance': current_dominance,
                            'expected_dominance': 59.0,
                            'difference': abs(current_dominance - 59.0),
                            'needs_correction': abs(current_dominance - 59.0) > 2.0,
                            'timestamp': datetime.now(timezone.utc)
                        }
                        
                        if dominance_check['needs_correction']:
                            logger.warning(f"⚠️ Bitcoin Dominance correction needed: {current_dominance}% vs expected 59%")
                        else:
                            logger.info(f"✅ Bitcoin Dominance check passed: {current_dominance}%")
                        
                        return dominance_check
        
        except Exception as e:
            logger.error(f"Error checking Bitcoin Dominance: {e}")
        
        return {
            'current_dominance': 59.0,
            'expected_dominance': 59.0,
            'difference': 0.0,
            'needs_correction': False,
            'timestamp': datetime.now(timezone.utc),
            'error': 'Could not fetch live data, using expected value'
        }

    async def _store_quality_report(self, quality_report: Dict[str, Any]):
        """Store data quality report in database"""
        try:
            quality_doc = {
                '_id': f"quality_report_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now(timezone.utc),
                'report': quality_report
            }
            
            await self.db.data_quality_log.insert_one(quality_doc)
            logger.info("📊 Data quality report stored")
            
        except Exception as e:
            logger.error(f"Error storing quality report: {e}")

    def _calculate_data_quality(self, data_points: List[MarketDataPoint]) -> float:
        """Calculate data quality score for data points"""
        if not data_points:
            return 0.0
        
        # Basic quality metrics
        valid_points = 0
        total_points = len(data_points)
        
        for point in data_points:
            # Check if all OHLCV values are valid
            if (point.open > 0 and point.high > 0 and point.low > 0 and 
                point.close > 0 and point.volume >= 0 and
                point.high >= max(point.open, point.close) and
                point.low <= min(point.open, point.close)):
                valid_points += 1
        
        return (valid_points / total_points) * 100 if total_points > 0 else 0.0

# Global instance
ai_data_module = None

async def get_ai_data_module(db) -> AIDataModule:
    """Get or create AI Data Module instance"""
    global ai_data_module
    if ai_data_module is None:
        ai_data_module = AIDataModule(db)
        await ai_data_module.initialize()
    return ai_data_module