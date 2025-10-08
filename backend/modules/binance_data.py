"""
Binance Data Provider - Real-time and Historical OHLCV data
Provides both Spot and Futures data using Binance API and WebSocket
"""
import asyncio
import json
import logging
import ccxt
import websockets
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
import aiohttp

logger = logging.getLogger(__name__)

class BinanceDataProvider:
    def __init__(self):
        """Initialize Binance data provider with CCXT and WebSocket support"""
        
        # CCXT Exchange instances
        self.spot_exchange = ccxt.binance({
            'apiKey': '',  # No API key needed for public data
            'secret': '',
            'sandbox': False,  # Use live market data
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}  # Default to spot
        })
        
        self.futures_exchange = ccxt.binance({
            'apiKey': '',
            'secret': '', 
            'sandbox': False,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}  # Futures market
        })
        
        # WebSocket URLs
        self.spot_ws_url = "wss://stream.binance.com:9443/ws/"
        self.futures_ws_url = "wss://fstream.binance.com/ws/"
        
        # Current price cache
        self.current_prices = {}
        
        # Supported trading pairs
        self.supported_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT',
            'SOL/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT',
            'SHIB/USDT', 'LTC/USDT', 'UNI/USDT', 'ATOM/USDT', 'LINK/USDT',
            'BCH/USDT', 'XLM/USDT', 'ICP/USDT', 'VET/USDT', 'ETC/USDT'
        ]
        
        logger.info("🟡 Binance Data Provider initialized with CCXT")

    async def get_current_price(self, symbol: str, market_type: str = 'spot') -> Optional[float]:
        """Get current price for a symbol from Binance"""
        try:
            # Format symbol for Binance (BTC/USDT format)
            if '/' not in symbol and 'USDT' in symbol:
                # Convert BTCUSDT to BTC/USDT
                base = symbol.replace('USDT', '')
                symbol = f"{base}/USDT"
            
            exchange = self.futures_exchange if market_type == 'futures' else self.spot_exchange
            
            # Get ticker data
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ticker, symbol
            )
            
            if ticker and 'last' in ticker:
                price = float(ticker['last'])
                logger.info(f"📊 Binance {market_type.upper()} price for {symbol}: ${price:,.2f}")
                return price
                
        except Exception as e:
            logger.error(f"❌ Error fetching Binance price for {symbol} ({market_type}): {e}")
            
        return None

    async def get_ohlcv_data(self, symbol: str, timeframe: str = '1m', limit: int = 100, 
                            market_type: str = 'spot') -> Optional[List[List]]:
        """Get OHLCV data from Binance"""
        try:
            # Format symbol
            if '/' not in symbol and 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                symbol = f"{base}/USDT"
            
            exchange = self.futures_exchange if market_type == 'futures' else self.spot_exchange
            
            # Get OHLCV data
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ohlcv, symbol, timeframe, None, limit
            )
            
            if ohlcv:
                logger.info(f"📈 Fetched {len(ohlcv)} OHLCV candles for {symbol} ({timeframe}, {market_type})")
                return ohlcv
                
        except Exception as e:
            logger.error(f"❌ Error fetching OHLCV for {symbol}: {e}")
            
        return None

    async def get_24h_stats(self, symbol: str, market_type: str = 'spot') -> Optional[Dict]:
        """Get 24h ticker statistics from Binance"""
        try:
            if '/' not in symbol and 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                symbol = f"{base}/USDT"
            
            exchange = self.futures_exchange if market_type == 'futures' else self.spot_exchange
            
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ticker, symbol
            )
            
            if ticker:
                stats = {
                    'symbol': symbol,
                    'price': float(ticker['last']) if ticker['last'] else 0,
                    'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                    'volume_24h': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                    'high_24h': float(ticker['high']) if ticker['high'] else 0,
                    'low_24h': float(ticker['low']) if ticker['low'] else 0,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'market_type': market_type
                }
                
                logger.info(f"📊 24h stats for {symbol} ({market_type}): ${stats['price']:,.2f} ({stats['change_24h']:+.2f}%)")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error fetching 24h stats for {symbol}: {e}")
            
        return None

    async def get_order_book(self, symbol: str, limit: int = 20, market_type: str = 'spot') -> Optional[Dict]:
        """Get order book data from Binance"""
        try:
            if '/' not in symbol and 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                symbol = f"{base}/USDT"
            
            exchange = self.futures_exchange if market_type == 'futures' else self.spot_exchange
            
            order_book = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_order_book, symbol, limit
            )
            
            if order_book:
                formatted_book = {
                    'symbol': symbol,
                    'bids': order_book['bids'][:limit],  # [price, quantity]
                    'asks': order_book['asks'][:limit],
                    'timestamp': order_book['timestamp'],
                    'market_type': market_type
                }
                
                logger.info(f"📚 Order book for {symbol} ({market_type}): {len(formatted_book['bids'])} bids, {len(formatted_book['asks'])} asks")
                return formatted_book
                
        except Exception as e:
            logger.error(f"❌ Error fetching order book for {symbol}: {e}")
            
        return None

    async def start_websocket_stream(self, symbols: List[str], market_type: str = 'spot'):
        """Start WebSocket stream for real-time price updates"""
        try:
            # Format symbols for Binance WebSocket
            formatted_symbols = []
            for symbol in symbols:
                if '/' in symbol:
                    base, quote = symbol.split('/')
                    formatted_symbols.append(f"{base.lower()}{quote.lower()}")
                else:
                    formatted_symbols.append(symbol.lower())
            
            # Create stream names for mini ticker
            streams = [f"{symbol}@miniTicker" for symbol in formatted_symbols]
            stream_url = f"{'wss://fstream.binance.com/stream' if market_type == 'futures' else 'wss://stream.binance.com:9443/stream'}?streams={'/'.join(streams)}"
            
            logger.info(f"🔄 Starting Binance {market_type} WebSocket stream for {len(symbols)} symbols")
            
            async with websockets.connect(stream_url) as websocket:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if 'stream' in data and 'data' in data:
                            stream_data = data['data']
                            symbol = stream_data['s']  # BTCUSDT format
                            
                            # Convert to standard format
                            if symbol.endswith('USDT'):
                                base = symbol.replace('USDT', '')
                                formatted_symbol = f"{base}/USDT"
                            else:
                                formatted_symbol = symbol
                            
                            price_data = {
                                'price': float(stream_data['c']),  # Close price
                                'change_24h': float(stream_data['P']),  # 24h change %
                                'volume': float(stream_data['v']),  # 24h volume
                                'high_24h': float(stream_data['h']),
                                'low_24h': float(stream_data['l']),
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'market_type': market_type
                            }
                            
                            # Update cache
                            self.current_prices[formatted_symbol] = price_data
                            
                            # logger.debug(f"💹 {formatted_symbol} ({market_type}): ${price_data['price']:,.2f} ({price_data['change_24h']:+.2f}%)")
                        
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning(f"🔄 Binance {market_type} WebSocket connection closed, reconnecting...")
                        break
                    except Exception as e:
                        logger.error(f"❌ WebSocket error for {market_type}: {e}")
                        await asyncio.sleep(5)
                        
        except Exception as e:
            logger.error(f"❌ Failed to start {market_type} WebSocket stream: {e}")

    def get_cached_price(self, symbol: str) -> Optional[Dict]:
        """Get cached price data from WebSocket stream"""
        return self.current_prices.get(symbol)

    async def get_supported_symbols(self, market_type: str = 'spot') -> List[str]:
        """Get list of supported trading pairs"""
        try:
            exchange = self.futures_exchange if market_type == 'futures' else self.spot_exchange
            
            markets = await asyncio.get_event_loop().run_in_executor(
                None, exchange.load_markets
            )
            
            # Filter USDT pairs
            usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
            
            logger.info(f"📋 Found {len(usdt_pairs)} USDT pairs on Binance {market_type}")
            return usdt_pairs[:50]  # Return top 50 pairs
            
        except Exception as e:
            logger.error(f"❌ Error loading Binance markets: {e}")
            return self.supported_pairs

# Global Binance data provider instance
binance_provider = BinanceDataProvider()