"""
Real-Time WebSocket Data Streamer
Provides live tick data for all crypto and traditional markets
"""
import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Callable, Optional, Any
import os

logger = logging.getLogger(__name__)

class RealTimeWebSocketStreamer:
    def __init__(self, db, data_callback: Optional[Callable] = None):
        self.db = db
        self.data_callback = data_callback
        self.connections = {}
        self.active_streams = {}
        self.subscribers = {}  # For frontend WebSocket connections
        self.finnhub_api_key = os.environ.get('FINNHUB_API_KEY', 'demo')
        
        # Symbol mappings for different providers
        self.binance_symbols = {
            'BTC/USDT': 'btcusdt',
            'ETH/USDT': 'ethusdt', 
            'BNB/USDT': 'bnbusdt',
            'XRP/USDT': 'xrpusdt',
            'ADA/USDT': 'adausdt',
            'SOL/USDT': 'solusdt',
            'DOGE/USDT': 'dogeusdt',
            'DOT/USDT': 'dotusdt',
            'MATIC/USDT': 'maticusdt',
            'LTC/USDT': 'ltcusdt'
        }
        
        self.finnhub_symbols = {
            'SPX': '^GSPC',
            'NASDAQ': '^IXIC',
            'DXY': 'DXY',
            'GOLD': 'XAUUSD'
        }
        
        self.iex_symbols = {
            'SPX': 'SPY',    # S&P 500 ETF
            'NASDAQ': 'QQQ', # NASDAQ ETF
            'GOLD': 'GLD',   # Gold ETF
            'DXY': 'UUP'     # Dollar ETF
        }
    
    async def start_crypto_streams(self):
        """Start Binance WebSocket streams for crypto"""
        try:
            streams = []
            for symbol, binance_symbol in self.binance_symbols.items():
                streams.append(f"{binance_symbol}@ticker")
            
            stream_names = '/'.join(streams)
            ws_url = f"wss://stream.binance.com:9443/ws/{stream_names}"
            
            logger.info(f"Starting Binance WebSocket: {ws_url}")
            
            async def handle_binance():
                try:
                    async with websockets.connect(ws_url) as websocket:
                        self.connections['binance'] = websocket
                        logger.info("✅ Binance WebSocket connected")
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                await self._process_binance_data(data)
                            except Exception as e:
                                logger.error(f"Error processing Binance data: {e}")
                                
                except Exception as e:
                    logger.error(f"Binance WebSocket error: {e}")
                    # Reconnect after delay
                    await asyncio.sleep(5)
                    asyncio.create_task(handle_binance())
            
            asyncio.create_task(handle_binance())
            
        except Exception as e:
            logger.error(f"Error starting crypto streams: {e}")
    
    async def start_traditional_streams(self):
        """Start traditional market streams using multiple sources"""
        
        # Start Finnhub WebSocket
        asyncio.create_task(self._start_finnhub_stream())
        
        # Start IEX Cloud polling (since free tier doesn't have WebSocket)
        asyncio.create_task(self._start_iex_polling())
        
        # Fallback: Alpha Vantage polling
        asyncio.create_task(self._start_alpha_vantage_polling())
    
    async def _start_finnhub_stream(self):
        """Start Finnhub WebSocket for traditional markets"""
        try:
            ws_url = f"wss://ws.finnhub.io?token={self.finnhub_api_key}"
            
            async def handle_finnhub():
                try:
                    async with websockets.connect(ws_url) as websocket:
                        self.connections['finnhub'] = websocket
                        logger.info("✅ Finnhub WebSocket connected")
                        
                        # Subscribe to symbols
                        for symbol, finnhub_symbol in self.finnhub_symbols.items():
                            subscribe_msg = {"type": "subscribe", "symbol": finnhub_symbol}
                            await websocket.send(json.dumps(subscribe_msg))
                            logger.info(f"Subscribed to Finnhub {symbol}")
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                await self._process_finnhub_data(data)
                            except Exception as e:
                                logger.error(f"Error processing Finnhub data: {e}")
                                
                except Exception as e:
                    logger.error(f"Finnhub WebSocket error: {e}")
                    # Reconnect after delay
                    await asyncio.sleep(10)
                    asyncio.create_task(handle_finnhub())
            
            asyncio.create_task(handle_finnhub())
            
        except Exception as e:
            logger.error(f"Error starting Finnhub stream: {e}")
    
    async def _start_iex_polling(self):
        """Poll IEX Cloud for traditional market data (free tier)"""
        try:
            while True:
                async with aiohttp.ClientSession() as session:
                    for symbol, iex_symbol in self.iex_symbols.items():
                        try:
                            url = f"https://cloud.iexapis.com/stable/stock/{iex_symbol}/quote"
                            params = {'token': 'demo'}  # Use demo for now
                            
                            async with session.get(url, params=params) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    await self._process_iex_data(symbol, data)
                                    
                        except Exception as e:
                            logger.error(f"IEX polling error for {symbol}: {e}")
                
                # Poll every 5 seconds for free tier
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error in IEX polling: {e}")
    
    async def _start_alpha_vantage_polling(self):
        """Alpha Vantage polling as fallback"""
        try:
            while True:
                async with aiohttp.ClientSession() as session:
                    for symbol in ['SPX', 'NASDAQ']:
                        try:
                            # Map to Alpha Vantage symbols
                            av_symbol = 'SPY' if symbol == 'SPX' else 'QQQ'
                            
                            url = 'https://www.alphavantage.co/query'
                            params = {
                                'function': 'GLOBAL_QUOTE',
                                'symbol': av_symbol,
                                'apikey': 'demo'
                            }
                            
                            async with session.get(url, params=params) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    await self._process_alpha_vantage_data(symbol, data)
                                    
                        except Exception as e:
                            logger.error(f"Alpha Vantage polling error for {symbol}: {e}")
                
                # Poll every 10 seconds to avoid rate limits
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"Error in Alpha Vantage polling: {e}")
    
    async def _process_binance_data(self, data):
        """Process Binance ticker data"""
        try:
            if 's' in data and 'c' in data:  # symbol and close price
                binance_symbol = data['s'].lower()
                
                # Find our symbol mapping
                symbol = None
                for our_symbol, mapped_symbol in self.binance_symbols.items():
                    if mapped_symbol == binance_symbol:
                        symbol = our_symbol
                        break
                
                if symbol:
                    tick_data = {
                        'symbol': symbol,
                        'price': float(data['c']),
                        'volume': float(data['v']),
                        'high_24h': float(data['h']),
                        'low_24h': float(data['l']),
                        'change_24h': float(data['P']),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'binance',
                        'asset_type': 'crypto'
                    }
                    
                    # Store in database
                    await self._store_tick_data(tick_data)
                    
                    # Broadcast to subscribers
                    await self._broadcast_to_subscribers(tick_data)
                    
                    logger.info(f"📈 {symbol}: ${tick_data['price']:.2f} ({tick_data['change_24h']:.2f}%)")
                    
        except Exception as e:
            logger.error(f"Error processing Binance data: {e}")
    
    async def _process_finnhub_data(self, data):
        """Process Finnhub WebSocket data"""
        try:
            if data.get('type') == 'trade' and 'data' in data:
                for trade in data['data']:
                    finnhub_symbol = trade.get('s')
                    
                    # Find our symbol mapping
                    symbol = None
                    for our_symbol, mapped_symbol in self.finnhub_symbols.items():
                        if mapped_symbol == finnhub_symbol:
                            symbol = our_symbol
                            break
                    
                    if symbol and 'p' in trade:  # price
                        tick_data = {
                            'symbol': symbol,
                            'price': float(trade['p']),
                            'volume': trade.get('v', 0),
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'source': 'finnhub',
                            'asset_type': 'traditional'
                        }
                        
                        await self._store_tick_data(tick_data)
                        await self._broadcast_to_subscribers(tick_data)
                        
                        logger.info(f"📊 {symbol}: ${tick_data['price']:.2f} (Finnhub)")
                        
        except Exception as e:
            logger.error(f"Error processing Finnhub data: {e}")
    
    async def _process_iex_data(self, symbol, data):
        """Process IEX Cloud data"""
        try:
            if 'latestPrice' in data:
                price = float(data['latestPrice'])
                
                # Convert ETF price to index approximation
                if symbol == 'SPX':
                    price = price * 10  # SPY to SPX approximation
                elif symbol == 'NASDAQ':
                    price = price * 40  # QQQ to NASDAQ approximation
                
                tick_data = {
                    'symbol': symbol,
                    'price': price,
                    'volume': data.get('latestVolume', 0),
                    'change': data.get('change', 0),
                    'change_percent': data.get('changePercent', 0) * 100,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': 'iex',
                    'asset_type': 'traditional'
                }
                
                await self._store_tick_data(tick_data)
                await self._broadcast_to_subscribers(tick_data)
                
                logger.info(f"📈 {symbol}: ${tick_data['price']:.2f} (IEX)")
                
        except Exception as e:
            logger.error(f"Error processing IEX data: {e}")
    
    async def _process_alpha_vantage_data(self, symbol, data):
        """Process Alpha Vantage data"""
        try:
            global_quote = data.get('Global Quote', {})
            if '05. price' in global_quote:
                price = float(global_quote['05. price'])
                
                # Convert ETF price to index approximation
                if symbol == 'SPX':
                    price = price * 10
                elif symbol == 'NASDAQ':
                    price = price * 40
                
                tick_data = {
                    'symbol': symbol,
                    'price': price,
                    'change_percent': float(global_quote.get('10. change percent', '0').replace('%', '')),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': 'alpha_vantage',
                    'asset_type': 'traditional'
                }
                
                await self._store_tick_data(tick_data)
                await self._broadcast_to_subscribers(tick_data)
                
                logger.info(f"📊 {symbol}: ${tick_data['price']:.2f} (Alpha Vantage)")
                
        except Exception as e:
            logger.error(f"Error processing Alpha Vantage data: {e}")
    
    async def _store_tick_data(self, tick_data):
        """Store tick data in database"""
        try:
            tick_doc = {
                'symbol': tick_data['symbol'],
                'price': tick_data['price'],
                'volume': tick_data.get('volume', 0),
                'timestamp': tick_data['timestamp'],
                'source': tick_data['source'],
                'asset_type': tick_data['asset_type'],
                'metadata': {
                    'change_24h': tick_data.get('change_24h'),
                    'change_percent': tick_data.get('change_percent'),
                    'high_24h': tick_data.get('high_24h'),
                    'low_24h': tick_data.get('low_24h')
                }
            }
            
            # Store in ticks collection
            await self.db.real_time_ticks.insert_one(tick_doc)
            
            # Keep only recent ticks (last 1 hour)
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            await self.db.real_time_ticks.delete_many({
                'symbol': tick_data['symbol'],
                'timestamp': {'$lt': one_hour_ago.isoformat()}
            })
            
        except Exception as e:
            logger.error(f"Error storing tick data: {e}")
    
    async def _broadcast_to_subscribers(self, tick_data):
        """Broadcast tick data to WebSocket subscribers"""
        try:
            message = {
                'type': 'tick',
                'data': tick_data
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
            logger.error(f"Error broadcasting to subscribers: {e}")
    
    def add_subscriber(self, subscriber_id: str, websocket):
        """Add WebSocket subscriber for real-time updates"""
        self.subscribers[subscriber_id] = websocket
        logger.info(f"Added subscriber: {subscriber_id}")
    
    def remove_subscriber(self, subscriber_id: str):
        """Remove WebSocket subscriber"""
        self.subscribers.pop(subscriber_id, None)
        logger.info(f"Removed subscriber: {subscriber_id}")
    
    async def get_latest_ticks(self, symbols: List[str] = None) -> Dict:
        """Get latest tick data for symbols"""
        try:
            query = {}
            if symbols:
                query['symbol'] = {'$in': symbols}
            
            # Get latest tick for each symbol
            pipeline = [
                {'$match': query},
                {'$sort': {'timestamp': -1}},
                {'$group': {
                    '_id': '$symbol',
                    'latest_tick': {'$first': '$$ROOT'}
                }}
            ]
            
            cursor = self.db.real_time_ticks.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            latest_data = {}
            for result in results:
                symbol = result['_id']
                tick = result['latest_tick']
                # Remove MongoDB _id
                if '_id' in tick:
                    del tick['_id']
                latest_data[symbol] = tick
            
            return latest_data
            
        except Exception as e:
            logger.error(f"Error getting latest ticks: {e}")
            return {}
    
    async def start_all_streams(self):
        """Start all real-time streams"""
        logger.info("🚀 Starting all real-time streams...")
        
        # Start crypto streams
        await self.start_crypto_streams()
        
        # Start traditional market streams
        await self.start_traditional_streams()
        
        logger.info("✅ All real-time streams started")
    
    async def stop_all_streams(self):
        """Stop all streams and close connections"""
        for name, connection in self.connections.items():
            try:
                await connection.close()
                logger.info(f"Closed {name} connection")
            except:
                pass
        
        self.connections.clear()
        self.subscribers.clear()
        logger.info("🛑 All streams stopped")