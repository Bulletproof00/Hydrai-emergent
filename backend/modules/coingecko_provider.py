"""
CoinGecko Data Provider - Alternative to Binance for geographic restrictions
Provides free cryptocurrency price data and OHLCV without geographic limitations
"""
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class CoinGeckoProvider:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = None
        self.rate_limit_delay = 1.2  # CoinGecko free tier: 50 calls/minute
        
        # Symbol mapping from CHAiNALYZE format to CoinGecko IDs
        self.symbol_map = {
            'BTC/USDT': 'bitcoin',
            'ETH/USDT': 'ethereum',
            'BNB/USDT': 'binancecoin',
            'XRP/USDT': 'ripple',
            'ADA/USDT': 'cardano',
            'SOL/USDT': 'solana',
            'DOGE/USDT': 'dogecoin',
            'DOT/USDT': 'polkadot',
            'MATIC/USDT': 'matic-network',
            'LTC/USDT': 'litecoin',
            'AVAX/USDT': 'avalanche-2',
            'SHIB/USDT': 'shiba-inu',
            'UNI/USDT': 'uniswap',
            'ATOM/USDT': 'cosmos',
            'LINK/USDT': 'chainlink',
            'TRX/USDT': 'tron',
            'ETC/USDT': 'ethereum-classic',
            'XLM/USDT': 'stellar',
            'ICP/USDT': 'internet-computer',
            'VET/USDT': 'vechain',
            'BCH/USDT': 'bitcoin-cash',
        }
        
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

    async def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price for a symbol"""
        try:
            if symbol not in self.symbol_map:
                logger.warning(f"Symbol {symbol} not supported by CoinGecko provider")
                return None
            
            coin_id = self.symbol_map[symbol]
            session = await self.get_session()
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            'symbol': symbol,
                            'price': coin_data['usd'],
                            'change_24h': coin_data.get('usd_24h_change', 0),
                            'volume_24h': coin_data.get('usd_24h_vol', 0),
                            'last_updated': coin_data.get('last_updated_at', int(datetime.now().timestamp())),
                            'source': 'coingecko'
                        }
                        
            await asyncio.sleep(self.rate_limit_delay)
            return None
                        
        except Exception as e:
            logger.error(f"CoinGecko price fetch error for {symbol}: {e}")
            return None

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current prices for multiple symbols efficiently"""
        try:
            # Map symbols to coin IDs
            valid_symbols = [s for s in symbols if s in self.symbol_map]
            if not valid_symbols:
                return {}
                
            coin_ids = [self.symbol_map[s] for s in valid_symbols]
            session = await self.get_session()
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}
                    
                    for symbol in valid_symbols:
                        coin_id = self.symbol_map[symbol]
                        if coin_id in data:
                            coin_data = data[coin_id]
                            result[symbol] = {
                                'symbol': symbol,
                                'price': coin_data['usd'],
                                'change_24h': coin_data.get('usd_24h_change', 0),
                                'volume_24h': coin_data.get('usd_24h_vol', 0),
                                'last_updated': coin_data.get('last_updated_at', int(datetime.now().timestamp())),
                                'source': 'coingecko'
                            }
                    
                    await asyncio.sleep(self.rate_limit_delay)
                    return result
                    
        except Exception as e:
            logger.error(f"CoinGecko multiple prices error: {e}")
            
        return {}

    async def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """Get OHLCV data for a symbol"""
        try:
            if symbol not in self.symbol_map:
                logger.warning(f"Symbol {symbol} not supported by CoinGecko provider")
                return []
            
            coin_id = self.symbol_map[symbol]
            session = await self.get_session()
            
            # CoinGecko uses days for historical data
            days = self._get_days_from_limit(limit, timeframe)
            
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Convert CoinGecko format [timestamp, open, high, low, close] to CCXT format
                    ohlcv_data = []
                    for candle in data[-limit:]:  # Get last 'limit' candles
                        ohlcv_data.append([
                            int(candle[0]),  # timestamp
                            float(candle[1]),  # open
                            float(candle[2]),  # high
                            float(candle[3]),  # low
                            float(candle[4]),  # close
                            0  # volume (not provided in OHLC endpoint)
                        ])
                    
                    await asyncio.sleep(self.rate_limit_delay)
                    return ohlcv_data
                    
        except Exception as e:
            logger.error(f"CoinGecko OHLCV error for {symbol}: {e}")
            
        return []

    def _get_days_from_limit(self, limit: int, timeframe: str) -> int:
        """Convert limit and timeframe to days for CoinGecko API"""
        timeframe_to_hours = {
            '1m': 1/60,
            '5m': 5/60,
            '15m': 15/60,
            '1h': 1,
            '4h': 4,
            '1d': 24,
            '1w': 168,
            '1M': 720  # ~30 days
        }
        
        hours_per_candle = timeframe_to_hours.get(timeframe, 1)
        total_hours = limit * hours_per_candle
        days = max(1, int(total_hours / 24))
        
        # CoinGecko limits
        return min(days, 365)  # Max 1 year

    async def get_market_data(self, limit: int = 20) -> List[Dict]:
        """Get market overview data for top cryptocurrencies"""
        try:
            session = await self.get_session()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    markets = []
                    for coin in data:
                        # Convert to CHAiNALYZE format
                        symbol = f"{coin['symbol'].upper()}/USDT"
                        markets.append({
                            'symbol': symbol,
                            'name': coin['name'],
                            'price': coin['current_price'],
                            'change_24h': coin.get('price_change_percentage_24h', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'rank': coin.get('market_cap_rank', 999),
                            'source': 'coingecko'
                        })
                    
                    await asyncio.sleep(self.rate_limit_delay)
                    return markets
                    
        except Exception as e:
            logger.error(f"CoinGecko market data error: {e}")
            
        return []

# Global instance
coingecko_provider = CoinGeckoProvider()