"""
Enhanced Real-Time Data Fetcher
Combines HTTP polling with WebSocket broadcasting for free-tier APIs
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class EnhancedRealTimeStreamer:
    def __init__(self, db):
        self.db = db
        self.subscribers = {}
        self.latest_prices = {}
        self.is_running = False
        
        # Free API endpoints and keys
        self.apis = {
            'crypto': {
                'coinbase': 'https://api.coinbase.com/v2/exchange-rates',
                'coingecko': 'https://api.coingecko.com/api/v3/simple/price'
            },
            'traditional': {
                'iex': 'https://cloud.iexapis.com/stable/stock/{symbol}/quote',
                'finnhub': 'https://finnhub.io/api/v1/quote',
                'yahoo_chart': 'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
            }
        }
        
        # Symbol mappings
        self.crypto_symbols = {
            'BTC/USDT': {'coinbase': 'BTC', 'coingecko': 'bitcoin'},
            'ETH/USDT': {'coinbase': 'ETH', 'coingecko': 'ethereum'},
            'BNB/USDT': {'coinbase': 'BNB', 'coingecko': 'binancecoin'},
            'XRP/USDT': {'coinbase': 'XRP', 'coingecko': 'ripple'},
            'ADA/USDT': {'coinbase': 'ADA', 'coingecko': 'cardano'},
            'SOL/USDT': {'coinbase': 'SOL', 'coingecko': 'solana'},
            'DOGE/USDT': {'coinbase': 'DOGE', 'coingecko': 'dogecoin'},
            'DOT/USDT': {'coinbase': 'DOT', 'coingecko': 'polkadot'},
            'MATIC/USDT': {'coinbase': 'MATIC', 'coingecko': 'matic-network'},
            'LTC/USDT': {'coinbase': 'LTC', 'coingecko': 'litecoin'}
        }
        
        self.traditional_symbols = {
            'SPX': {'yahoo': '^GSPC', 'iex': 'SPY'},
            'NASDAQ': {'yahoo': '^IXIC', 'iex': 'QQQ'},
            'DXY': {'yahoo': 'DX-Y.NYB', 'iex': 'UUP'},
            'GOLD': {'yahoo': 'GC=F', 'iex': 'GLD'}
        }
    
    async def start_polling_streams(self):
        """Start polling-based streams for all assets"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🚀 Starting enhanced real-time polling streams...")
        
        # Start crypto polling
        asyncio.create_task(self._poll_crypto_data())
        
        # Start traditional markets polling
        asyncio.create_task(self._poll_traditional_data())
        
        # Start price simulation for demonstration
        asyncio.create_task(self._simulate_price_movements())
        
        logger.info("✅ Enhanced polling streams started")
    
    async def _poll_crypto_data(self):
        """Poll crypto data from free APIs"""
        while self.is_running:
            try:
                await self._fetch_coingecko_data()
                await asyncio.sleep(10)  # Poll every 10 seconds
            except Exception as e:
                logger.error(f"Crypto polling error: {e}")
                await asyncio.sleep(30)
    
    async def _poll_traditional_data(self):
        """Poll traditional market data"""
        while self.is_running:
            try:
                await self._fetch_yahoo_data()
                await asyncio.sleep(15)  # Poll every 15 seconds
            except Exception as e:
                logger.error(f"Traditional polling error: {e}")
                await asyncio.sleep(30)
    
    async def _simulate_price_movements(self):
        """Simulate realistic price movements between API calls"""
        while self.is_running:
            try:
                # Add small random movements to existing prices
                import random
                
                for symbol, price_data in self.latest_prices.items():
                    if 'price' in price_data:
                        current_price = price_data['price']
                        
                        # Small random movement (±0.05%)
                        movement = random.uniform(-0.0005, 0.0005)
                        new_price = current_price * (1 + movement)
                        
                        # Update price with simulation
                        updated_data = price_data.copy()
                        updated_data.update({
                            'price': new_price,
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'simulated': True
                        })
                        
                        self.latest_prices[symbol] = updated_data
                        
                        # Broadcast update
                        await self._broadcast_price_update(symbol, updated_data)
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Price simulation error: {e}")
                await asyncio.sleep(5)
    
    async def _fetch_coingecko_data(self):
        """Fetch crypto data from CoinGecko (free, no API key required)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all coins in one request
                coin_ids = ','.join([data['coingecko'] for data in self.crypto_symbols.values()])
                url = f"{self.apis['crypto']['coingecko']}"
                params = {
                    'ids': coin_ids,
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for symbol, mapping in self.crypto_symbols.items():
                            coingecko_id = mapping['coingecko']
                            
                            if coingecko_id in data:
                                coin_data = data[coingecko_id]
                                price_data = {
                                    'symbol': symbol,
                                    'price': coin_data['usd'],
                                    'change_24h': coin_data.get('usd_24h_change', 0),
                                    'volume_24h': coin_data.get('usd_24h_vol', 0),
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'source': 'coingecko',
                                    'asset_type': 'crypto'
                                }
                                
                                self.latest_prices[symbol] = price_data
                                await self._store_tick_data(price_data)
                                await self._broadcast_price_update(symbol, price_data)
                                
                                logger.info(f"📈 {symbol}: ${price_data['price']:.2f} ({price_data['change_24h']:.2f}%)")
                    else:
                        logger.warning(f"CoinGecko API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")
    
    async def _fetch_yahoo_data(self):
        """Fetch traditional market data from Yahoo Finance"""
        try:
            async with aiohttp.ClientSession() as session:
                for symbol, mapping in self.traditional_symbols.items():
                    try:
                        yahoo_symbol = mapping['yahoo']
                        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
                        params = {'interval': '1m', 'range': '1d'}
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        async with session.get(url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                chart = data.get('chart', {})
                                result = chart.get('result', [])
                                
                                if result:
                                    meta = result[0].get('meta', {})
                                    current_price = meta.get('regularMarketPrice')
                                    previous_close = meta.get('previousClose')
                                    
                                    if current_price:
                                        change = ((current_price - previous_close) / previous_close * 100) if previous_close else 0
                                        
                                        price_data = {
                                            'symbol': symbol,
                                            'price': current_price,
                                            'change': current_price - previous_close if previous_close else 0,
                                            'change_percent': change,
                                            'previous_close': previous_close,
                                            'timestamp': datetime.now(timezone.utc).isoformat(),
                                            'source': 'yahoo',
                                            'asset_type': 'traditional'
                                        }
                                        
                                        self.latest_prices[symbol] = price_data
                                        await self._store_tick_data(price_data)
                                        await self._broadcast_price_update(symbol, price_data)
                                        
                                        logger.info(f"📊 {symbol}: ${price_data['price']:.2f} ({change:.2f}%)")
                            else:
                                logger.warning(f"Yahoo API error for {symbol}: {response.status}")
                                
                        await asyncio.sleep(1)  # Small delay between requests
                        
                    except Exception as e:
                        logger.error(f"Yahoo fetch error for {symbol}: {e}")
                        
        except Exception as e:
            logger.error(f"Yahoo fetch error: {e}")
    
    async def _store_tick_data(self, tick_data):
        """Store tick data in database"""
        try:
            tick_doc = {
                'symbol': tick_data['symbol'],
                'price': tick_data['price'],
                'timestamp': tick_data['timestamp'],
                'source': tick_data['source'],
                'asset_type': tick_data['asset_type'],
                'metadata': {
                    'change_24h': tick_data.get('change_24h'),
                    'change_percent': tick_data.get('change_percent'),
                    'volume_24h': tick_data.get('volume_24h'),
                    'previous_close': tick_data.get('previous_close'),
                    'simulated': tick_data.get('simulated', False)
                }
            }
            
            await self.db.real_time_ticks.insert_one(tick_doc)
            
            # Keep only last hour of data per symbol
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            await self.db.real_time_ticks.delete_many({
                'symbol': tick_data['symbol'],
                'timestamp': {'$lt': one_hour_ago.isoformat()}
            })
            
        except Exception as e:
            logger.error(f"Error storing tick data: {e}")
    
    async def _broadcast_price_update(self, symbol, price_data):
        """Broadcast price update to WebSocket subscribers"""
        try:
            message = {
                'type': 'price_update',
                'symbol': symbol,
                'data': price_data
            }
            
            # Remove disconnected subscribers
            disconnected = []
            for subscriber_id, websocket in self.subscribers.items():
                try:
                    await websocket.send(json.dumps(message))
                except:
                    disconnected.append(subscriber_id)
            
            # Clean up disconnected subscribers
            for subscriber_id in disconnected:
                self.subscribers.pop(subscriber_id, None)
                
        except Exception as e:
            logger.error(f"Error broadcasting price update: {e}")
    
    def add_subscriber(self, subscriber_id: str, websocket):
        """Add WebSocket subscriber"""
        self.subscribers[subscriber_id] = websocket
        logger.info(f"Added subscriber: {subscriber_id} (Total: {len(self.subscribers)})")
    
    def remove_subscriber(self, subscriber_id: str):
        """Remove WebSocket subscriber"""
        self.subscribers.pop(subscriber_id, None)
        logger.info(f"Removed subscriber: {subscriber_id} (Total: {len(self.subscribers)})")
    
    async def get_latest_prices(self, symbols: List[str] = None) -> Dict:
        """Get latest price data"""
        try:
            if symbols:
                return {symbol: self.latest_prices.get(symbol) for symbol in symbols if symbol in self.latest_prices}
            else:
                return self.latest_prices.copy()
                
        except Exception as e:
            logger.error(f"Error getting latest prices: {e}")
            return {}
    
    async def get_price_history(self, symbol: str, minutes: int = 60) -> List[Dict]:
        """Get price history for a symbol"""
        try:
            start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            
            cursor = self.db.real_time_ticks.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_time.isoformat()}
            }).sort('timestamp', 1)
            
            history = await cursor.to_list(length=None)
            
            # Remove MongoDB _id
            for item in history:
                if '_id' in item:
                    del item['_id']
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return []
    
    async def stop_streams(self):
        """Stop all streams"""
        self.is_running = False
        self.subscribers.clear()
        logger.info("🛑 Enhanced streams stopped")