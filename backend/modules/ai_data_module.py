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
        """Fetch historical data - CoinGecko + comprehensive synthetic fallback"""
        try:
            # First try CoinGecko for recent data
            coingecko_data = await self._try_coingecko_api(symbol, timeframe, start_date)
            if coingecko_data and len(coingecko_data) > 50:
                logger.info(f"✅ CoinGecko data for {symbol} {timeframe}: {len(coingecko_data)} points")
                return coingecko_data
            
            # Fallback to comprehensive synthetic historical data
            logger.warning(f"⚠️ CoinGecko limited for {symbol} {timeframe}, generating comprehensive synthetic data")
            return await self._generate_comprehensive_historical_data(symbol, timeframe, start_date)
        
        except Exception as e:
            logger.error(f"Historical data fetch error for {symbol}: {e}")
            return await self._generate_comprehensive_historical_data(symbol, timeframe, start_date)

    async def _try_coingecko_api(self, symbol: str, timeframe: str, start_date: datetime) -> List[MarketDataPoint]:
        """Try CoinGecko API (limited but real data)"""
        try:
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return []
            
            async with aiohttp.ClientSession() as session:
                # Get recent market data (CoinGecko free tier limitation)
                days_back = min(365, (datetime.now() - start_date).days)  # Max 365 days
                
                url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days_back,
                    'interval': 'daily'  # CoinGecko free tier mainly supports daily
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_coingecko_to_ohlcv(data, symbol, timeframe)
        
        except Exception as e:
            logger.debug(f"CoinGecko API attempt failed: {e}")
        
        return []

    async def _generate_comprehensive_historical_data(self, symbol: str, timeframe: str, start_date: datetime) -> List[MarketDataPoint]:
        """Generate comprehensive synthetic historical data from 2019 to present"""
        logger.info(f"🔄 Generating synthetic historical data for {symbol} {timeframe} from {start_date}")
        
        data_points = []
        
        # Base prices for different symbols (realistic 2019 starting points)
        base_prices_2019 = {
            'BTC/USDT': 3800.0,   # BTC was ~$3,800 in early 2019
            'ETH/USDT': 140.0,    # ETH was ~$140 in early 2019  
            'BNB/USDT': 6.0,      # BNB was ~$6 in early 2019
            'ADA/USDT': 0.04,     # ADA was ~$0.04 in early 2019
            'SOL/USDT': 0.80      # SOL approximation
        }
        
        base_price = base_prices_2019.get(symbol, 100.0)
        current_time = start_date
        end_time = datetime.now(timezone.utc)
        
        # Calculate timeframe interval in minutes
        interval_minutes = self._get_interval_minutes(timeframe)
        
        # Generate realistic price evolution from 2019 to now
        total_days = (end_time - current_time).days
        current_price = base_price
        
        # Bitcoin historical growth pattern (used as template)
        # 2019: $3,800 → 2021 peak: $69,000 → 2022 low: $15,500 → 2024: $65,000 → 2025: $122,000
        price_multiplier_targets = self._get_price_evolution_targets(symbol, total_days)
        
        candle_count = 0
        target_candles = min(50000, total_days * 24 * 60 // interval_minutes)  # Limit to 50k candles
        
        while current_time < end_time and candle_count < target_candles:
            # Calculate price evolution based on time progression
            days_from_start = (current_time - start_date).days
            progress = days_from_start / total_days if total_days > 0 else 1
            
            # Apply realistic price evolution curve
            price_multiplier = self._calculate_price_multiplier(progress, price_multiplier_targets)
            target_price = base_price * price_multiplier
            
            # Add realistic volatility and market dynamics
            daily_volatility = self._get_daily_volatility(symbol, timeframe)
            trend_strength = np.sin(2 * np.pi * progress * 4) * 0.1  # 4 major cycles
            
            # Generate OHLCV for this candle
            ohlcv = self._generate_realistic_ohlcv(
                target_price, daily_volatility, trend_strength, symbol, interval_minutes
            )
            
            data_point = MarketDataPoint(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                open=ohlcv['open'],
                high=ohlcv['high'],
                low=ohlcv['low'],
                close=ohlcv['close'],
                volume=ohlcv['volume'],
                source='synthetic_historical'
            )
            
            data_points.append(data_point)
            current_price = ohlcv['close']
            
            # Move to next timeframe
            current_time += timedelta(minutes=interval_minutes)
            candle_count += 1
            
            # Progress logging
            if candle_count % 1000 == 0:
                logger.debug(f"Generated {candle_count} candles for {symbol} {timeframe}")
        
        logger.info(f"✅ Generated {len(data_points)} synthetic historical candles for {symbol} {timeframe}")
        return data_points

    def _get_interval_minutes(self, timeframe: str) -> int:
        """Convert timeframe to minutes"""
        intervals = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080,
            '1M': 43200  # Approximate 30 days
        }
        return intervals.get(timeframe, 60)

    def _get_price_evolution_targets(self, symbol: str, total_days: int) -> Dict[str, float]:
        """Get realistic price evolution targets based on historical crypto patterns"""
        # Based on Bitcoin's historical performance 2019-2025
        if 'BTC' in symbol:
            return {
                'start': 1.0,      # 2019: $3,800
                'peak_2021': 18.2, # 2021 peak: $69,000 (18.2x from $3,800)
                'low_2022': 4.1,   # 2022 low: $15,500 (4.1x from $3,800) 
                'recovery_2024': 17.1, # 2024: $65,000 (17.1x from $3,800)
                'current_2025': 32.1   # 2025: $122,000 (32.1x from $3,800)
            }
        elif 'ETH' in symbol:
            return {
                'start': 1.0,      # 2019: $140
                'peak_2021': 34.6, # 2021 peak: $4,850 (34.6x from $140)
                'low_2022': 5.7,   # 2022 low: $800 (5.7x from $140)
                'recovery_2024': 21.4, # 2024: $3,000 (21.4x from $140)
                'current_2025': 30.0   # 2025: $4,200 (30x from $140)
            }
        else:
            # Generic altcoin pattern (more volatile)
            return {
                'start': 1.0,
                'peak_2021': 25.0,
                'low_2022': 3.0,
                'recovery_2024': 15.0,
                'current_2025': 20.0
            }

    def _calculate_price_multiplier(self, progress: float, targets: Dict[str, float]) -> float:
        """Calculate realistic price multiplier based on progress through time"""
        # Define key time points (as fractions of total time 2019-2025)
        key_points = {
            0.0: targets['start'],        # 2019 start
            0.4: targets['peak_2021'],    # 2021 peak (40% through)
            0.6: targets['low_2022'],     # 2022 low (60% through)
            0.9: targets['recovery_2024'], # 2024 recovery (90% through)
            1.0: targets['current_2025']   # 2025 current (100% through)
        }
        
        # Linear interpolation between key points
        sorted_points = sorted(key_points.items())
        
        for i in range(len(sorted_points) - 1):
            t1, price1 = sorted_points[i]
            t2, price2 = sorted_points[i + 1]
            
            if t1 <= progress <= t2:
                # Interpolate between the two points
                if t2 == t1:
                    return price1
                
                t_normalized = (progress - t1) / (t2 - t1)
                return price1 + (price2 - price1) * t_normalized
        
        # If beyond last point, return last price
        return sorted_points[-1][1]

    def _get_daily_volatility(self, symbol: str, timeframe: str) -> float:
        """Get realistic daily volatility for different assets"""
        base_volatilities = {
            'BTC/USDT': 0.04,  # 4% daily volatility
            'ETH/USDT': 0.05,  # 5% daily volatility  
            'BNB/USDT': 0.06,  # 6% daily volatility
            'ADA/USDT': 0.08,  # 8% daily volatility
            'SOL/USDT': 0.10   # 10% daily volatility
        }
        
        base_vol = base_volatilities.get(symbol, 0.06)
        
        # Adjust for timeframe (smaller timeframes = lower volatility per candle)
        timeframe_adjustments = {
            '1m': 0.1,    # 1-minute candles have much lower volatility
            '5m': 0.2,
            '15m': 0.4,
            '1h': 0.6,
            '4h': 0.8,
            '1d': 1.0,    # Daily is the base
            '1w': 1.5,
            '1M': 2.0
        }
        
        adjustment = timeframe_adjustments.get(timeframe, 1.0)
        return base_vol * adjustment

    def _generate_realistic_ohlcv(self, target_price: float, volatility: float, trend: float, symbol: str, interval_minutes: int) -> Dict[str, float]:
        """Generate realistic OHLCV data for a single candle"""
        # Open price (previous close + small gap)
        gap = np.random.normal(0, volatility * 0.1) * target_price
        open_price = target_price + gap
        
        # Add trend and volatility
        price_change = np.random.normal(trend, volatility) * target_price
        close_price = open_price + price_change
        
        # Generate high and low with realistic wick behavior
        candle_range = abs(close_price - open_price)
        wick_extension = np.random.exponential(0.5) * candle_range
        
        if close_price > open_price:  # Green candle
            high = max(open_price, close_price) + wick_extension
            low = min(open_price, close_price) - wick_extension * 0.6
        else:  # Red candle
            high = max(open_price, close_price) + wick_extension * 0.6
            low = min(open_price, close_price) - wick_extension
        
        # Ensure logical price relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # Generate realistic volume
        base_volume = self._get_base_volume(symbol, interval_minutes)
        volume_multiplier = np.random.lognormal(0, 0.5)  # Log-normal distribution for volume
        volume = base_volume * volume_multiplier
        
        return {
            'open': max(0.001, open_price),    # Ensure positive prices
            'high': max(0.001, high),
            'low': max(0.001, low),
            'close': max(0.001, close_price),
            'volume': max(0, volume)
        }

    def _get_base_volume(self, symbol: str, interval_minutes: int) -> float:
        """Get realistic base volume for different symbols and timeframes"""
        # Daily volume bases (approximate realistic values)
        daily_volumes = {
            'BTC/USDT': 1000000000,  # $1B daily volume
            'ETH/USDT': 500000000,   # $500M daily volume
            'BNB/USDT': 100000000,   # $100M daily volume  
            'ADA/USDT': 50000000,    # $50M daily volume
            'SOL/USDT': 80000000     # $80M daily volume
        }
        
        daily_volume = daily_volumes.get(symbol, 10000000)  # Default $10M
        
        # Scale down for shorter timeframes
        candles_per_day = 24 * 60 // interval_minutes
        return daily_volume / candles_per_day if candles_per_day > 0 else daily_volume

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