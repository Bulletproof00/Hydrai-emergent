"""
Enhanced Real-Time Market Data Module 
Uses multiple data sources for reliable real-time traditional market data
"""
import aiohttp
import asyncio
import yfinance as yf
from datetime import datetime, timezone, timedelta
import logging
import os
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Traditional market symbols mapping for different providers
FINNHUB_SYMBOLS = {
    'SPX': '^GSPC',
    'NASDAQ': '^IXIC', 
    'DXY': 'DXY',
    'GOLD': 'XAUUSD',
    'EURUSD': 'OANDA:EUR_USD',
    'US2000': '^RUT',
    'US10Y': '^TNX',
    'DAX': '^GDAXI',
    'NIKKEI': '^N225'
}

YAHOO_SYMBOLS = {
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

class RealTimeMarketDataFetcher:
    def __init__(self, db):
        self.db = db
        self.finnhub_api_key = os.environ.get('FINNHUB_API_KEY', 'free')  # Free tier for now
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_finnhub_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time quote from Finnhub API"""
        try:
            finnhub_symbol = FINNHUB_SYMBOLS.get(symbol)
            if not finnhub_symbol:
                return None
            
            session = await self.get_session()
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                'symbol': finnhub_symbol,
                'token': self.finnhub_api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Finnhub returns: c (current), h (high), l (low), o (open), pc (previous close), t (timestamp)
                    if 'c' in data and data['c'] != 0:
                        return {
                            'symbol': symbol,
                            'price': data['c'],
                            'open': data.get('o'),
                            'high': data.get('h'),
                            'low': data.get('l'),
                            'previous_close': data.get('pc'),
                            'timestamp': data.get('t', int(datetime.now().timestamp())),
                            'source': 'finnhub'
                        }
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub data for {symbol}: {str(e)}")
        
        return None
    
    async def fetch_yahoo_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch quote from Yahoo Finance with cache clearing"""
        try:
            yahoo_symbol = YAHOO_SYMBOLS.get(symbol)
            if not yahoo_symbol:
                return None
            
            # Try to get fresh data with very short period
            ticker = yf.Ticker(yahoo_symbol)
            
            # Get intraday data first to ensure fresh data
            hist = ticker.history(period='1d', interval='1m', prepost=False, auto_adjust=True)
            
            if hist.empty:
                # Fallback to daily data
                hist = ticker.history(period='2d', interval='1d', prepost=False, auto_adjust=True)
            
            if not hist.empty:
                latest = hist.iloc[-1]
                
                return {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': float(latest['Volume']) if 'Volume' in latest else 0,
                    'timestamp': int(hist.index[-1].timestamp()),
                    'source': 'yahoo'
                }
                
        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {symbol}: {str(e)}")
        
        return None
    
    async def fetch_investing_com_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price from Investing.com API"""
        try:
            # Investing.com symbol mapping
            investing_symbols = {
                'SPX': '166',      # S&P 500 
                'NASDAQ': '14',    # NASDAQ Composite
                'DXY': '8827',     # US Dollar Index
                'GOLD': '8830'     # Gold Futures
            }
            
            investing_id = investing_symbols.get(symbol)
            if not investing_id:
                return None
            
            session = await self.get_session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Use Investing.com's API endpoint
            url = f'https://api.investing.com/api/financialdata/{investing_id}/historical/chart/'
            params = {
                'period': 'P1D',
                'interval': 'PT1M',
                'pointscount': '1'
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and data['data']:
                        latest = data['data'][-1]
                        price = latest.get('close') or latest.get('price', 0)
                        
                        if price > 0:
                            return {
                                'symbol': symbol,
                                'price': price,
                                'timestamp': int(datetime.now().timestamp()),
                                'source': 'investing.com'
                            }
                            
        except Exception as e:
            logger.error(f"Error fetching Investing.com data for {symbol}: {str(e)}")
        
        return None

    async def fetch_polygon_free_quote(self, symbol: str) -> Optional[Dict]:
        """Try Polygon.io free tier"""
        try:
            polygon_symbols = {
                'SPX': 'I:SPX',
                'NASDAQ': 'I:COMP', 
                'DXY': 'C:EURUSD',  # Approximate
                'GOLD': 'C:XAUUSD'
            }
            
            polygon_symbol = polygon_symbols.get(symbol)
            if not polygon_symbol:
                return None
            
            session = await self.get_session()
            url = f'https://api.polygon.io/v2/last/trade/{polygon_symbol}'
            params = {'apikey': 'demo'}  # Try demo key
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'results' in data and data['results']:
                        result = data['results']
                        price = result.get('p', 0)  # price
                        
                        if price > 0:
                            return {
                                'symbol': symbol,
                                'price': price,
                                'timestamp': result.get('t', int(datetime.now().timestamp() * 1000)) // 1000,
                                'source': 'polygon'
                            }
                            
        except Exception as e:
            logger.error(f"Error fetching Polygon data for {symbol}: {str(e)}")
        
        return None
        
    async def fetch_twelve_data_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch from Twelve Data free API"""
        try:
            # Map to tradeable symbols
            twelve_symbols = {
                'SPX': 'SPY',      # S&P 500 ETF as proxy
                'NASDAQ': 'QQQ',   # NASDAQ ETF as proxy  
                'GOLD': 'GLD',     # Gold ETF
                'DXY': 'UUP'       # Dollar ETF
            }
            
            twelve_symbol = twelve_symbols.get(symbol)
            if not twelve_symbol:
                return None
            
            session = await self.get_session()
            url = 'https://api.twelvedata.com/quote'
            params = {
                'symbol': twelve_symbol,
                'apikey': 'demo'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we got valid data
                    if 'close' in data and data['close']:
                        price = float(data['close'])
                        
                        # Convert ETF price back to index (rough approximation)
                        if symbol == 'NASDAQ' and twelve_symbol == 'QQQ':
                            # QQQ is approximately 1/40th of NASDAQ index
                            price = price * 40
                        elif symbol == 'SPX' and twelve_symbol == 'SPY':
                            # SPY is approximately 1/10th of SPX index  
                            price = price * 10
                        
                        return {
                            'symbol': symbol,
                            'price': price,
                            'timestamp': int(datetime.now().timestamp()),
                            'source': 'twelve_data',
                            'proxy_symbol': twelve_symbol
                        }
                        
        except Exception as e:
            logger.error(f"Error fetching Twelve Data for {symbol}: {str(e)}")
        
        return None
    
    async def get_real_time_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote using multiple sources with fallback"""
        logger.info(f"Fetching real-time quote for {symbol}")
        
        # Try sources in order of preference
        sources = [
            self.fetch_twelve_data_quote,
            self.fetch_polygon_free_quote,
            self.fetch_investing_com_price,
            self.fetch_finnhub_quote,
            self.fetch_yahoo_quote
        ]
        
        for source_func in sources:
            try:
                data = await source_func(symbol)
                if data and data.get('price'):
                    logger.info(f"Got {symbol} price ${data['price']:.2f} from {data['source']}")
                    return data
            except Exception as e:
                logger.warning(f"Source failed for {symbol}: {str(e)}")
                continue
        
        logger.error(f"All sources failed for {symbol}")
        return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get quotes for multiple symbols concurrently"""
        tasks = [self.get_real_time_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = {}
        for i, result in enumerate(results):
            if isinstance(result, dict) and result:
                quotes[symbols[i]] = result
            else:
                logger.warning(f"Failed to get quote for {symbols[i]}: {result}")
        
        return quotes
    
    def format_for_ohlcv(self, quote_data: Dict, timeframe: str = '1h') -> List[Dict]:
        """Convert quote data to OHLCV format for compatibility"""
        if not quote_data:
            return []
        
        # Create a single candle from the quote
        price = quote_data['price']
        open_price = quote_data.get('open', price)
        high_price = quote_data.get('high', price) 
        low_price = quote_data.get('low', price)
        volume = quote_data.get('volume', 0)
        
        candle = {
            'timestamp': quote_data['timestamp'] * 1000,  # Convert to milliseconds
            'open': open_price,
            'high': high_price,
            'low': low_price, 
            'close': price,
            'volume': volume
        }
        
        return [candle]
    
    async def fetch_enhanced_traditional_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 1000) -> List[Dict]:
        """Enhanced fetch that combines real-time with historical data"""
        try:
            # Get real-time quote first
            real_time_quote = await self.get_real_time_quote(symbol)
            
            # Get historical data from Yahoo (for historical context)
            yahoo_symbol = YAHOO_SYMBOLS.get(symbol)
            if yahoo_symbol:
                interval_map = {
                    '1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h',
                    '4h': '4h', '1d': '1d', '1w': '1wk', '1M': '1mo'
                }
                interval = interval_map.get(timeframe, '1h')
                
                # Get historical data
                ticker = yf.Ticker(yahoo_symbol)
                
                if interval in ['1m', '5m', '15m']:
                    period = '7d'
                elif interval in ['1h', '4h']:
                    period = '30d'  
                else:
                    period = '1y'
                
                hist = ticker.history(period=period, interval=interval, auto_adjust=True, prepost=False)
                
                if not hist.empty:
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
                    
                    # Update the latest candle with real-time data if available
                    if real_time_quote and formatted_data:
                        latest_candle = formatted_data[-1]
                        # Update close price with real-time data
                        latest_candle['close'] = real_time_quote['price']
                        
                        # Adjust high/low if needed
                        if real_time_quote['price'] > latest_candle['high']:
                            latest_candle['high'] = real_time_quote['price']
                        if real_time_quote['price'] < latest_candle['low']:
                            latest_candle['low'] = real_time_quote['price']
                    
                    # Log the latest price for verification
                    if formatted_data:
                        latest_price = formatted_data[-1]['close']
                        logger.info(f"{symbol} enhanced price: ${latest_price:.2f} (real-time: {real_time_quote is not None})")
                    
                    return formatted_data[-limit:] if len(formatted_data) > limit else formatted_data
            
            # Fallback: use just the real-time quote as a single candle
            if real_time_quote:
                return self.format_for_ohlcv(real_time_quote, timeframe)
            
        except Exception as e:
            logger.error(f"Error in enhanced traditional OHLCV for {symbol}: {str(e)}")
        
        return []