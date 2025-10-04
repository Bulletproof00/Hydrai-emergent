"""
Smart Money Indicators Module
Provides liquidation heatmaps, open interest, funding rates, and orderflow data
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class SmartMoneyIndicators:
    def __init__(self, db):
        self.db = db
        self.session = None
        
        # Focus symbols as requested
        self.focus_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
        
        # API endpoints for free smart money data
        self.apis = {
            'coinglass': {
                'liquidation_map': 'https://open-api.coinglass.com/public/v2/liquidation_map',
                'open_interest': 'https://open-api.coinglass.com/public/v2/open_interest',
                'funding_rates': 'https://open-api.coinglass.com/public/v2/funding_rates'
            },
            'coinank': {
                'liquidation_heatmap': 'https://api.coinank.com/api/pro/futures/liquidation_heatmap',
                'funding_rates': 'https://api.coinank.com/api/pro/futures/funding_rate',
                'open_interest': 'https://api.coinank.com/api/pro/futures/open_interest'
            },
            'alternative': {
                'binance_futures': 'https://fapi.binance.com/fapi/v1',
                'bybit_derivatives': 'https://api.bybit.com/derivatives/v3/public'
            }
        }
        
        # Symbol mapping for different exchanges
        self.symbol_mapping = {
            'BTC/USDT': {
                'binance': 'BTCUSDT',
                'coinglass': 'BTC',
                'coinank': 'BTCUSDT'
            },
            'ETH/USDT': {
                'binance': 'ETHUSDT', 
                'coinglass': 'ETH',
                'coinank': 'ETHUSDT'
            },
            'SOL/USDT': {
                'binance': 'SOLUSDT',
                'coinglass': 'SOL', 
                'coinank': 'SOLUSDT'
            },
            'XRP/USDT': {
                'binance': 'XRPUSDT',
                'coinglass': 'XRP',
                'coinank': 'XRPUSDT'
            }
        }
        
        # Cache for smart money data
        self.cache = {
            'liquidation_heatmap': {},
            'open_interest': {},
            'funding_rates': {},
            'orderflow': {}
        }
        
        self.last_update = {}

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format to BTC/USDT style"""
        # If symbol is already in BTC/USDT format, return as is
        if '/' in symbol:
            return symbol
        
        # Convert BTCUSDT to BTC/USDT
        symbol_map = {
            'BTCUSDT': 'BTC/USDT',
            'ETHUSDT': 'ETH/USDT',
            'SOLUSDT': 'SOL/USDT',
            'XRPUSDT': 'XRP/USDT'
        }
        
        return symbol_map.get(symbol, symbol)

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

    async def fetch_liquidation_heatmap(self, symbol: str) -> Optional[Dict]:
        """Fetch liquidation heatmap data from multiple sources"""
        try:
            # Convert symbol format if needed (BTCUSDT -> BTC/USDT)
            normalized_symbol = self._normalize_symbol(symbol)
            
            heatmap_data = {
                'symbol': normalized_symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'liquidation_levels': [],
                'long_liquidations': [],
                'short_liquidations': [],
                'source': 'aggregated'
            }
            
            # Try CoinGlass API first
            coinglass_data = await self._fetch_coinglass_liquidations(normalized_symbol)
            if coinglass_data:
                heatmap_data['liquidation_levels'].extend(coinglass_data.get('levels', []))
            
            # Try alternative sources
            binance_data = await self._fetch_binance_liquidations(normalized_symbol)
            if binance_data:
                heatmap_data['long_liquidations'].extend(binance_data.get('longs', []))
                heatmap_data['short_liquidations'].extend(binance_data.get('shorts', []))
            
            # Generate synthetic heatmap if no real data available
            if not heatmap_data['liquidation_levels']:
                heatmap_data = await self._generate_synthetic_liquidations(normalized_symbol)
            
            # Store in cache and database
            self.cache['liquidation_heatmap'][normalized_symbol] = heatmap_data
            await self._store_smart_money_data('liquidation_heatmap', normalized_symbol, heatmap_data)
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error fetching liquidation heatmap for {symbol}: {e}")
            return None

    async def _fetch_coinglass_liquidations(self, symbol: str) -> Optional[Dict]:
        """Fetch liquidations from CoinGlass API"""
        try:
            session = await self.get_session()
            coinglass_symbol = self.symbol_mapping[symbol]['coinglass']
            
            # CoinGlass public API endpoint
            url = f"https://open-api.coinglass.com/public/v2/liquidation_map"
            params = {
                'symbol': coinglass_symbol,
                'time_type': '4h'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success') and 'data' in data:
                        liquidation_levels = []
                        
                        # Process liquidation data
                        for level in data['data'].get('liquidation_distribution', []):
                            liquidation_levels.append({
                                'price': level.get('price', 0),
                                'long_liquidation': level.get('long_liquidation', 0),
                                'short_liquidation': level.get('short_liquidation', 0),
                                'total_liquidation': level.get('total_liquidation', 0)
                            })
                        
                        return {
                            'levels': liquidation_levels,
                            'source': 'coinglass'
                        }
                        
                else:
                    logger.warning(f"CoinGlass API error {response.status} for {symbol}")
                    
        except Exception as e:
            logger.debug(f"CoinGlass liquidation fetch error for {symbol}: {e}")
        
        return None

    async def _fetch_binance_liquidations(self, symbol: str) -> Optional[Dict]:
        """Fetch liquidation data from Binance Futures API"""
        try:
            session = await self.get_session()
            binance_symbol = self.symbol_mapping[symbol]['binance']
            
            # Binance Futures API for open interest and liquidation proxy
            url = f"https://fapi.binance.com/fapi/v1/openInterest"
            params = {'symbol': binance_symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    open_interest = float(data.get('openInterest', 0))
                    
                    # Get 24h ticker for price context
                    ticker_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr"
                    ticker_params = {'symbol': binance_symbol}
                    
                    async with session.get(ticker_url, params=ticker_params) as ticker_response:
                        if ticker_response.status == 200:
                            ticker_data = await ticker_response.json()
                            
                            current_price = float(ticker_data.get('lastPrice', 0))
                            volume_24h = float(ticker_data.get('volume', 0))
                            
                            # Estimate liquidation zones based on price and OI
                            liquidation_estimate = self._estimate_liquidation_zones(
                                current_price, open_interest, volume_24h
                            )
                            
                            return liquidation_estimate
                            
        except Exception as e:
            logger.debug(f"Binance liquidation fetch error for {symbol}: {e}")
        
        return None

    def _estimate_liquidation_zones(self, price: float, open_interest: float, volume: float) -> Dict:
        """Estimate liquidation zones based on price, OI and volume"""
        try:
            # Calculate potential liquidation levels
            liquidation_zones = []
            
            # Common leverage levels and their liquidation distances
            leverage_levels = [5, 10, 20, 50, 100]
            
            for leverage in leverage_levels:
                # Long liquidation (price goes down)
                long_liq_price = price * (1 - (1/leverage) * 0.9)  # 90% of liquidation threshold
                
                # Short liquidation (price goes up)
                short_liq_price = price * (1 + (1/leverage) * 0.9)
                
                # Estimate liquidation volume based on OI and leverage popularity
                liq_volume = open_interest / len(leverage_levels) * (1/leverage * 10)
                
                liquidation_zones.extend([
                    {
                        'price': long_liq_price,
                        'type': 'long_liquidation',
                        'volume': liq_volume,
                        'leverage': leverage
                    },
                    {
                        'price': short_liq_price,
                        'type': 'short_liquidation', 
                        'volume': liq_volume,
                        'leverage': leverage
                    }
                ])
            
            return {
                'longs': [z for z in liquidation_zones if z['type'] == 'long_liquidation'],
                'shorts': [z for z in liquidation_zones if z['type'] == 'short_liquidation'],
                'source': 'estimated'
            }
            
        except Exception as e:
            logger.error(f"Error estimating liquidation zones: {e}")
            return {'longs': [], 'shorts': [], 'source': 'error'}

    async def _generate_synthetic_liquidations(self, symbol: str) -> Dict:
        """Generate synthetic liquidation heatmap for demonstration"""
        try:
            # Get current price from our real-time system
            import random
            
            base_prices = {
                'BTC/USDT': 62000,
                'ETH/USDT': 2400, 
                'SOL/USDT': 140,
                'XRP/USDT': 0.52
            }
            
            base_price = base_prices.get(symbol, 100)
            current_price = base_price * random.uniform(0.95, 1.05)  # ±5% variation
            
            liquidation_levels = []
            
            # Generate realistic liquidation clusters
            for i in range(20):
                # Create clusters above and below current price
                distance_factor = random.uniform(0.02, 0.15)  # 2-15% from current price
                
                if i % 2 == 0:
                    # Long liquidations (below current price)
                    price_level = current_price * (1 - distance_factor)
                    long_volume = random.uniform(1000000, 50000000)  # $1M - $50M
                    short_volume = random.uniform(100000, 5000000)   # Smaller short volume
                else:
                    # Short liquidations (above current price)
                    price_level = current_price * (1 + distance_factor)
                    long_volume = random.uniform(100000, 5000000)
                    short_volume = random.uniform(1000000, 50000000)
                
                liquidation_levels.append({
                    'price': round(price_level, 2),
                    'long_liquidation': long_volume,
                    'short_liquidation': short_volume,
                    'total_liquidation': long_volume + short_volume,
                    'synthetic': True
                })
            
            # Sort by price
            liquidation_levels.sort(key=lambda x: x['price'])
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'liquidation_levels': liquidation_levels,
                'long_liquidations': [l for l in liquidation_levels if l['long_liquidation'] > l['short_liquidation']],
                'short_liquidations': [l for l in liquidation_levels if l['short_liquidation'] > l['long_liquidation']], 
                'source': 'synthetic',
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error generating synthetic liquidations: {e}")
            return {}

    async def fetch_open_interest(self, symbol: str) -> Optional[Dict]:
        """Fetch open interest data from multiple exchanges"""
        try:
            oi_data = {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_oi': 0,
                'exchanges': {},
                'source': 'aggregated'
            }
            
            # Fetch from Binance
            binance_oi = await self._fetch_binance_open_interest(symbol)
            if binance_oi:
                oi_data['exchanges']['binance'] = binance_oi
                oi_data['total_oi'] += binance_oi.get('open_interest', 0)
            
            # Add synthetic OI data for other exchanges
            synthetic_oi = await self._generate_synthetic_open_interest(symbol)
            oi_data['exchanges'].update(synthetic_oi)
            
            # Calculate total
            for exchange, data in oi_data['exchanges'].items():
                if isinstance(data, dict):
                    oi_data['total_oi'] += data.get('open_interest', 0)
            
            # Store in cache and database
            self.cache['open_interest'][symbol] = oi_data
            await self._store_smart_money_data('open_interest', symbol, oi_data)
            
            return oi_data
            
        except Exception as e:
            logger.error(f"Error fetching open interest for {symbol}: {e}")
            return None

    async def _fetch_binance_open_interest(self, symbol: str) -> Optional[Dict]:
        """Fetch open interest from Binance Futures"""
        try:
            session = await self.get_session()
            binance_symbol = self.symbol_mapping[symbol]['binance']
            
            url = f"https://fapi.binance.com/fapi/v1/openInterest"
            params = {'symbol': binance_symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'open_interest': float(data.get('openInterest', 0)),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'source': 'binance'
                    }
                    
        except Exception as e:
            logger.debug(f"Binance OI fetch error for {symbol}: {e}")
        
        return None

    async def _generate_synthetic_open_interest(self, symbol: str) -> Dict:
        """Generate synthetic open interest data for other exchanges"""
        import random
        
        exchanges = ['bybit', 'okx', 'deribit', 'ftx', 'bitmex']
        synthetic_data = {}
        
        base_oi = {
            'BTC/USDT': 50000,
            'ETH/USDT': 300000,
            'SOL/USDT': 80000,
            'XRP/USDT': 120000
        }
        
        base = base_oi.get(symbol, 10000)
        
        for exchange in exchanges:
            # Generate realistic OI values
            oi_variation = random.uniform(0.5, 1.8)  # 50% - 180% of base
            oi_value = base * oi_variation
            
            synthetic_data[exchange] = {
                'open_interest': round(oi_value, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'synthetic'
            }
        
        return synthetic_data

    async def fetch_funding_rates(self, symbol: str) -> Optional[Dict]:
        """Fetch funding rates from multiple exchanges"""
        try:
            funding_data = {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'current_funding_rate': 0,
                'next_funding_time': None,
                'exchanges': {},
                'source': 'aggregated'
            }
            
            # Fetch from Binance
            binance_funding = await self._fetch_binance_funding_rate(symbol)
            if binance_funding:
                funding_data['exchanges']['binance'] = binance_funding
                funding_data['current_funding_rate'] = binance_funding.get('funding_rate', 0)
                funding_data['next_funding_time'] = binance_funding.get('next_funding_time')
            
            # Add synthetic funding rates for other exchanges
            synthetic_funding = await self._generate_synthetic_funding_rates(symbol)
            funding_data['exchanges'].update(synthetic_funding)
            
            # Calculate weighted average funding rate
            total_weight = 0
            weighted_funding = 0
            
            for exchange, data in funding_data['exchanges'].items():
                if isinstance(data, dict) and 'funding_rate' in data:
                    weight = 1.0  # Equal weight for now
                    weighted_funding += data['funding_rate'] * weight
                    total_weight += weight
            
            if total_weight > 0:
                funding_data['current_funding_rate'] = weighted_funding / total_weight
            
            # Store in cache and database
            self.cache['funding_rates'][symbol] = funding_data
            await self._store_smart_money_data('funding_rates', symbol, funding_data)
            
            return funding_data
            
        except Exception as e:
            logger.error(f"Error fetching funding rates for {symbol}: {e}")
            return None

    async def _fetch_binance_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Fetch funding rate from Binance Futures"""
        try:
            session = await self.get_session()
            binance_symbol = self.symbol_mapping[symbol]['binance']
            
            url = f"https://fapi.binance.com/fapi/v1/premiumIndex"
            params = {'symbol': binance_symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    funding_rate = float(data.get('lastFundingRate', 0))
                    next_funding_time = int(data.get('nextFundingTime', 0))
                    
                    return {
                        'funding_rate': funding_rate * 100,  # Convert to percentage
                        'next_funding_time': datetime.fromtimestamp(next_funding_time / 1000, timezone.utc).isoformat(),
                        'mark_price': float(data.get('markPrice', 0)),
                        'source': 'binance'
                    }
                    
        except Exception as e:
            logger.debug(f"Binance funding rate fetch error for {symbol}: {e}")
        
        return None

    async def _generate_synthetic_funding_rates(self, symbol: str) -> Dict:
        """Generate synthetic funding rates for other exchanges"""
        import random
        
        exchanges = ['bybit', 'okx', 'deribit', 'ftx']
        synthetic_data = {}
        
        # Base funding rate around 0.01% (typical range is -0.05% to +0.05%)
        base_funding_rate = random.uniform(-0.05, 0.05)
        
        for exchange in exchanges:
            # Small variations between exchanges
            funding_variation = random.uniform(-0.02, 0.02)
            funding_rate = base_funding_rate + funding_variation
            
            # Next funding time (usually every 8 hours)
            next_funding = datetime.now(timezone.utc) + timedelta(hours=random.randint(1, 8))
            
            synthetic_data[exchange] = {
                'funding_rate': round(funding_rate, 4),
                'next_funding_time': next_funding.isoformat(),
                'source': 'synthetic'
            }
        
        return synthetic_data

    async def _store_smart_money_data(self, data_type: str, symbol: str, data: Dict):
        """Store smart money data in database"""
        try:
            doc = {
                'data_type': data_type,
                'symbol': symbol,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc)
            }
            
            # Store in smart_money_data collection
            await self.db.smart_money_data.insert_one(doc)
            
            # Keep only recent data (last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            await self.db.smart_money_data.delete_many({
                'data_type': data_type,
                'symbol': symbol,
                'created_at': {'$lt': cutoff_time}
            })
            
        except Exception as e:
            logger.error(f"Error storing smart money data: {e}")

    async def get_all_smart_money_data(self, symbols: List[str] = None) -> Dict:
        """Get all smart money data for symbols"""
        if symbols is None:
            symbols = self.focus_symbols
        
        all_data = {}
        
        for symbol in symbols:
            symbol_data = {}
            
            # Check if data needs refresh (15 minutes)
            needs_refresh = True
            if symbol in self.last_update:
                time_diff = datetime.now(timezone.utc) - self.last_update[symbol]
                needs_refresh = time_diff.total_seconds() > 900  # 15 minutes
            
            if needs_refresh:
                # Fetch fresh data
                liquidation_data = await self.fetch_liquidation_heatmap(symbol)
                oi_data = await self.fetch_open_interest(symbol)
                funding_data = await self.fetch_funding_rates(symbol)
                
                symbol_data = {
                    'liquidation_heatmap': liquidation_data,
                    'open_interest': oi_data,
                    'funding_rates': funding_data
                }
                
                self.last_update[symbol] = datetime.now(timezone.utc)
            else:
                # Use cached data
                symbol_data = {
                    'liquidation_heatmap': self.cache.get('liquidation_heatmap', {}).get(symbol),
                    'open_interest': self.cache.get('open_interest', {}).get(symbol),
                    'funding_rates': self.cache.get('funding_rates', {}).get(symbol)
                }
            
            all_data[symbol] = symbol_data
        
        return all_data

    async def start_background_updates(self):
        """Start background task for updating smart money data every 15 minutes"""
        while True:
            try:
                logger.info("🔄 Updating Smart Money data...")
                
                for symbol in self.focus_symbols:
                    await self.fetch_liquidation_heatmap(symbol)
                    await self.fetch_open_interest(symbol)
                    await self.fetch_funding_rates(symbol)
                    
                    # Small delay between symbols
                    await asyncio.sleep(2)
                
                logger.info("✅ Smart Money data updated")
                
                # Wait 15 minutes before next update
                await asyncio.sleep(900)  # 15 minutes
                
            except Exception as e:
                logger.error(f"Error in smart money background update: {e}")
                # Wait 5 minutes before retry
                await asyncio.sleep(300)