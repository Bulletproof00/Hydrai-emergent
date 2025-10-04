"""
Market Data Module - Fetches and stores OHLCV data with real-time enhancements
"""
import ccxt.async_support as ccxt
import yfinance as yf
from datetime import datetime, timezone, timedelta
import logging
import asyncio
from .real_time_market_data import RealTimeMarketDataFetcher

logger = logging.getLogger(__name__)

# Traditional market symbols mapping
TRADITIONAL_MARKETS = {
    'SPX': '^GSPC',
    'NASDAQ': '^IXIC',
    'DXY': 'DX-Y.NYB',
    'GOLD': 'GC=F',
    'EURUSD': 'EURUSD=X',
    'US2000': '^RUT',
    'US10Y': '^TNX',
    'DAX': '^GDAXI',
    'NIKKEI': '^N225'
}

class MarketDataFetcher:
    def __init__(self, exchange_instance, db):
        self.exchange = exchange_instance
        self.db = db
        self.real_time_fetcher = RealTimeMarketDataFetcher(db)
    
    async def fetch_crypto_ohlcv(self, symbol, timeframe='1h', limit=1000):
        """Fetch OHLCV data from crypto exchange"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            formatted_data = []
            for candle in ohlcv:
                formatted_data.append({
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return formatted_data
        except Exception as e:
            logger.error(f"Error fetching crypto OHLCV: {str(e)}")
            return []
    
    async def fetch_traditional_ohlcv(self, symbol, timeframe='1h', limit=1000):
        """Fetch OHLCV data from traditional markets with real-time enhancement"""
        try:
            # Use the enhanced real-time fetcher
            data = await self.real_time_fetcher.fetch_enhanced_traditional_ohlcv(
                symbol, timeframe, limit
            )
            
            if data:
                logger.info(f"Enhanced traditional OHLCV for {symbol}: {len(data)} candles, latest: ${data[-1]['close']:.2f}")
                return data
            else:
                logger.warning(f"No enhanced data for {symbol}, falling back to legacy method")
                return self.fetch_traditional_ohlcv_legacy(symbol, timeframe, limit)
        
        except Exception as e:
            logger.error(f"Error in enhanced traditional OHLCV for {symbol}: {str(e)}")
            # Fallback to legacy method
            return self.fetch_traditional_ohlcv_legacy(symbol, timeframe, limit)
    
    def fetch_traditional_ohlcv_legacy(self, symbol, timeframe='1h', limit=1000):
        """Legacy OHLCV fetch method as fallback"""
        try:
            yahoo_symbol = TRADITIONAL_MARKETS.get(symbol)
            if not yahoo_symbol:
                logger.warning(f"Traditional market symbol {symbol} not found")
                return []
            
            # Map timeframe to yfinance interval
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h',
                '4h': '4h', '1d': '1d', '1w': '1wk', '1M': '1mo'
            }
            interval = interval_map.get(timeframe, '1h')
            
            # Calculate period based on limit
            if interval in ['1m', '5m', '15m']:
                period = '7d'
            elif interval in ['1h', '4h']:
                period = '60d'
            else:
                period = 'max'
            
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period, interval=interval, auto_adjust=True, prepost=False)
            
            if hist.empty:
                logger.warning(f"No data returned for {symbol}")
                return []
            
            latest_close = hist['Close'].iloc[-1]
            logger.info(f"{symbol} legacy close: ${latest_close:.2f}")
            
            formatted_data = []
            for index, row in hist.iterrows():
                formatted_data.append({
                    'timestamp': int(index.timestamp() * 1000),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']) if 'Volume' in row else 0
                })
            
            return formatted_data[-limit:] if len(formatted_data) > limit else formatted_data
        
        except Exception as e:
            logger.error(f"Error fetching legacy traditional OHLCV for {symbol}: {str(e)}")
            return []
    
    async def store_ohlcv_data(self, symbol, timeframe, data, asset_type='crypto'):
        """Store OHLCV data in database"""
        try:
            for candle in data:
                doc = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'asset_type': asset_type,
                    'timestamp': candle['timestamp'],
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle['volume'],
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Upsert (update if exists, insert if not)
                await self.db.ohlcv_data.update_one(
                    {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': candle['timestamp']
                    },
                    {'$set': doc},
                    upsert=True
                )
            
            logger.info(f"Stored {len(data)} candles for {symbol} {timeframe}")
            return True
        except Exception as e:
            logger.error(f"Error storing OHLCV data: {str(e)}")
            return False
    
    async def get_stored_ohlcv(self, symbol, timeframe, limit=1000):
        """Retrieve stored OHLCV data from database"""
        try:
            cursor = self.db.ohlcv_data.find(
                {'symbol': symbol, 'timeframe': timeframe}
            ).sort('timestamp', -1).limit(limit)
            
            data = await cursor.to_list(length=limit)
            
            # Reverse to get chronological order
            data.reverse()
            
            # Remove MongoDB _id
            for d in data:
                if '_id' in d:
                    del d['_id']
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving stored OHLCV: {str(e)}")
            return []
    
    async def fetch_and_store_crypto(self, symbol, timeframe='1h', limit=1000):
        """Fetch crypto data and store in DB"""
        data = await self.fetch_crypto_ohlcv(symbol, timeframe, limit)
        if data:
            await self.store_ohlcv_data(symbol, timeframe, data, 'crypto')
        return data
    
    async def fetch_and_store_traditional(self, symbol, timeframe='1h', limit=1000):
        """Fetch traditional market data and store in DB with real-time enhancement"""
        data = await self.fetch_traditional_ohlcv(symbol, timeframe, limit)
        if data:
            await self.store_ohlcv_data(symbol, timeframe, data, 'traditional')
        return data
    
    async def fetch_dominance_data(self):
        """Fetch crypto dominance metrics"""
        try:
            # Approximate calculation based on market caps
            btc_ticker = await self.exchange.fetch_ticker('BTC/USDT')
            eth_ticker = await self.exchange.fetch_ticker('ETH/USDT')
            
            btc_market_cap = btc_ticker['last'] * 19_500_000
            eth_market_cap = eth_ticker['last'] * 120_000_000
            total_crypto_cap = btc_market_cap + eth_market_cap * 1.8  # Approximation
            
            btc_dominance = (btc_market_cap / total_crypto_cap) * 100
            eth_dominance = (eth_market_cap / total_crypto_cap) * 100
            usdt_dominance = 7.5  # Approximate
            
            dominance_data = {
                'BTC_DOMINANCE': btc_dominance,
                'ETH_DOMINANCE': eth_dominance,
                'USDT_DOMINANCE': usdt_dominance,
                'TOTAL_CRYPTO_CAP': total_crypto_cap,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in DB
            await self.db.dominance_data.insert_one(dominance_data)
            
            return dominance_data
        except Exception as e:
            logger.error(f"Error fetching dominance data: {str(e)}")
            return {}
