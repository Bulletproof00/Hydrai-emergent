"""
Enhanced Smart Money Indicators - Coinglass Style Implementation
Provides detailed liquidation heatmaps, open interest aggregation, and exchange-level data
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
import numpy as np
from .live_smart_money import LiveSmartMoneyDataFetcher

logger = logging.getLogger(__name__)

class EnhancedSmartMoneyIndicators:
    def __init__(self, db):
        self.db = db
        self.session = None
        self.live_fetcher = LiveSmartMoneyDataFetcher(db)
        
        # All supported symbols (expanded from focus symbols)
        self.supported_symbols = {
            'BTC/USDT': {
                'binance': 'BTCUSDT',
                'coinglass': 'BTC', 
                'display_name': 'Bitcoin',
                'price_precision': 2,
                'base_price': 62000
            },
            'ETH/USDT': {
                'binance': 'ETHUSDT',
                'coinglass': 'ETH',
                'display_name': 'Ethereum', 
                'price_precision': 2,
                'base_price': 2400
            },
            'SOL/USDT': {
                'binance': 'SOLUSDT',
                'coinglass': 'SOL',
                'display_name': 'Solana',
                'price_precision': 2,
                'base_price': 140
            },
            'XRP/USDT': {
                'binance': 'XRPUSDT',
                'coinglass': 'XRP',
                'display_name': 'Ripple',
                'price_precision': 4,
                'base_price': 0.52
            },
            'BNB/USDT': {
                'binance': 'BNBUSDT',
                'coinglass': 'BNB',
                'display_name': 'BNB',
                'price_precision': 2,
                'base_price': 580
            },
            'ADA/USDT': {
                'binance': 'ADAUSDT',
                'coinglass': 'ADA',
                'display_name': 'Cardano',
                'price_precision': 4,
                'base_price': 0.35
            }
        }
        
        # Exchange configurations
        self.exchanges = {
            'binance': {'name': 'Binance', 'weight': 0.35, 'api_working': True},
            'bybit': {'name': 'Bybit', 'weight': 0.25, 'api_working': False},
            'okx': {'name': 'OKX', 'weight': 0.20, 'api_working': False},
            'deribit': {'name': 'Deribit', 'weight': 0.10, 'api_working': False},
            'bitmex': {'name': 'BitMEX', 'weight': 0.05, 'api_working': False},
            'ftx': {'name': 'FTX', 'weight': 0.05, 'api_working': False}
        }
        
        # Cache for enhanced data
        self.cache = {
            'liquidation_heatmap_2d': {},
            'open_interest_detailed': {},
            'funding_rates_multi_exchange': {},
            'current_prices': {}
        }
        
        self.last_update = {}

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
        
        if self.live_fetcher:
            await self.live_fetcher.close_session()

    async def fetch_enhanced_liquidation_heatmap(self, symbol: str) -> Optional[Dict]:
        """Fetch enhanced 2D liquidation heatmap data with LIVE data like Coinglass"""
        try:
            if symbol not in self.supported_symbols:
                logger.warning(f"Symbol {symbol} not supported")
                return None
            
            symbol_info = self.supported_symbols[symbol]
            
            # Fetch LIVE liquidation data
            live_liquidation_data = await self.live_fetcher.fetch_live_liquidation_data(symbol)
            
            if not live_liquidation_data:
                logger.warning(f"Could not fetch live liquidation data for {symbol}")
                return None
            
            current_price = live_liquidation_data['current_price']
            liquidation_levels = live_liquidation_data['liquidation_levels']
            summary = live_liquidation_data['summary']
            
            logger.info(f"Fetched LIVE liquidation data for {symbol}: ${current_price}, {len(liquidation_levels)} levels")
            
            # Enhanced heatmap data with LIVE information
            heatmap_data = {
                'symbol': symbol,
                'display_name': symbol_info['display_name'],
                'current_price': current_price,
                'timestamp': live_liquidation_data['timestamp'],
                'timeframe': '24h',
                'price_range': self._calculate_price_range(current_price, symbol_info),
                'liquidation_levels': liquidation_levels,
                'summary': summary,
                'total_liquidations_24h': live_liquidation_data.get('total_liquidations_24h', 0),
                'data_sources': live_liquidation_data.get('data_sources', {}),
                'source': 'live_aggregated',
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in cache and database
            self.cache['liquidation_heatmap_2d'][symbol] = heatmap_data
            await self._store_enhanced_smart_money_data('liquidation_heatmap_2d', symbol, heatmap_data)
            
            logger.info(f"Enhanced liquidation heatmap ready for {symbol}: {len(liquidation_levels)} levels, ${current_price} current price")
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error fetching enhanced liquidation heatmap for {symbol}: {e}")
            return None

    async def fetch_enhanced_open_interest(self, symbol: str) -> Optional[Dict]:
        """Fetch enhanced open interest with detailed exchange breakdown using LIVE data like Coinglass"""
        try:
            if symbol not in self.supported_symbols:
                return None
            
            symbol_info = self.supported_symbols[symbol]
            
            # Fetch LIVE open interest data
            live_oi_data = await self.live_fetcher.fetch_live_open_interest_data(symbol)
            
            if not live_oi_data:
                logger.warning(f"Could not fetch live open interest data for {symbol}")
                return None
            
            current_price = live_oi_data['current_price']
            
            logger.info(f"Fetched LIVE open interest data for {symbol}: ${current_price}, Total OI: {live_oi_data['total_open_interest']}")
            
            # Enhanced OI data with LIVE information
            oi_data = {
                'symbol': symbol,
                'display_name': symbol_info['display_name'],
                'current_price': current_price,
                'timestamp': live_oi_data['timestamp'],
                'total_open_interest': live_oi_data['total_open_interest'],
                'total_volume_24h': live_oi_data['total_volume_24h'],
                'oi_change_24h': live_oi_data['market_metrics'].get('oi_change_24h', 0),
                'exchanges_detail': live_oi_data['exchanges_detail'],
                'market_metrics': live_oi_data['market_metrics'],
                'data_sources': live_oi_data.get('data_sources', {}),
                'source': 'live_aggregated',
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in cache and database
            self.cache['open_interest_detailed'][symbol] = oi_data
            await self._store_enhanced_smart_money_data('open_interest_detailed', symbol, oi_data)
            
            logger.info(f"Enhanced open interest ready for {symbol}: {len(oi_data['exchanges_detail'])} exchanges, Total OI: ${oi_data['total_open_interest']/1000000:.1f}M")
            
            return oi_data
            
        except Exception as e:
            logger.error(f"Error fetching enhanced open interest for {symbol}: {e}")
            return None

    async def _get_current_price(self, symbol: str) -> float:
        """Get current price from real-time system or fetch fresh"""
        try:
            # Try to get from real-time cache first
            if symbol in self.cache['current_prices']:
                cached_price = self.cache['current_prices'][symbol]
                if cached_price['timestamp'] > datetime.now(timezone.utc) - timedelta(minutes=5):
                    return cached_price['price']
            
            # Fetch fresh price from Binance
            binance_symbol = self.supported_symbols[symbol]['binance']
            session = await self.get_session()
            
            url = f"https://fapi.binance.com/fapi/v1/ticker/price"
            params = {'symbol': binance_symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data.get('price', 0))
                    
                    # Cache the price
                    self.cache['current_prices'][symbol] = {
                        'price': price,
                        'timestamp': datetime.now(timezone.utc)
                    }
                    
                    return price
            
            # Fallback to base price with variation
            import random
            base_price = self.supported_symbols[symbol]['base_price']
            return base_price * random.uniform(0.95, 1.05)
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return self.supported_symbols[symbol]['base_price']

    def _calculate_price_range(self, current_price: float, symbol_info: Dict) -> Dict:
        """Calculate price range for heatmap (±20% from current price)"""
        try:
            range_percent = 0.20  # ±20% range
            
            min_price = current_price * (1 - range_percent)
            max_price = current_price * (1 + range_percent)
            
            # Create 40 price levels
            price_levels = np.linspace(min_price, max_price, 40)
            
            return {
                'min_price': min_price,
                'max_price': max_price,
                'current_price': current_price,
                'price_levels': price_levels.tolist(),
                'range_percent': range_percent * 100
            }
        except Exception as e:
            logger.error(f"Error calculating price range: {e}")
            return {}

    async def _fetch_binance_liquidation_detailed(self, symbol: str) -> Optional[Dict]:
        """Fetch detailed liquidation data from Binance"""
        try:
            session = await self.get_session()
            binance_symbol = self.supported_symbols[symbol]['binance']
            
            # Get open interest
            oi_url = f"https://fapi.binance.com/fapi/v1/openInterest"
            oi_params = {'symbol': binance_symbol}
            
            async with session.get(oi_url, params=oi_params) as response:
                if response.status == 200:
                    oi_data = await response.json()
                    open_interest = float(oi_data.get('openInterest', 0))
                    
                    # Get 24h stats
                    stats_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr"
                    stats_params = {'symbol': binance_symbol}
                    
                    async with session.get(stats_url, params=stats_params) as stats_response:
                        if stats_response.status == 200:
                            stats_data = await stats_response.json()
                            
                            return {
                                'exchange': 'binance',
                                'open_interest': open_interest,
                                'volume_24h': float(stats_data.get('volume', 0)),
                                'price_change_24h': float(stats_data.get('priceChangePercent', 0)),
                                'high_24h': float(stats_data.get('highPrice', 0)),
                                'low_24h': float(stats_data.get('lowPrice', 0)),
                                'liquidation_estimate': self._estimate_liquidation_levels_binance(
                                    open_interest, float(stats_data.get('lastPrice', 0))
                                ),
                                'source': 'binance_api'
                            }
                            
        except Exception as e:
            logger.debug(f"Binance liquidation fetch error for {symbol}: {e}")
        
        return None

    def _estimate_liquidation_levels_binance(self, open_interest: float, current_price: float) -> List[Dict]:
        """Estimate liquidation levels based on OI and price"""
        try:
            liquidation_levels = []
            
            # Common leverage levels in futures trading
            leverage_levels = [5, 10, 20, 50, 100]
            
            for leverage in leverage_levels:
                # Calculate liquidation prices for both long and short positions
                # Simplified calculation (actual margin requirements are more complex)
                
                # Long liquidation (price goes down)
                long_liq_price = current_price * (1 - (1/leverage) * 0.9)
                long_volume = (open_interest / len(leverage_levels)) * (1/leverage * 20)
                
                # Short liquidation (price goes up)  
                short_liq_price = current_price * (1 + (1/leverage) * 0.9)
                short_volume = (open_interest / len(leverage_levels)) * (1/leverage * 15)
                
                liquidation_levels.extend([
                    {
                        'price': long_liq_price,
                        'volume': long_volume,
                        'type': 'long_liquidation',
                        'leverage': leverage,
                        'distance_percent': ((current_price - long_liq_price) / current_price) * 100
                    },
                    {
                        'price': short_liq_price,
                        'volume': short_volume,
                        'type': 'short_liquidation',
                        'leverage': leverage,
                        'distance_percent': ((short_liq_price - current_price) / current_price) * 100
                    }
                ])
            
            return sorted(liquidation_levels, key=lambda x: x['price'])
            
        except Exception as e:
            logger.error(f"Error estimating liquidation levels: {e}")
            return []

    async def _generate_synthetic_exchange_liquidations(self, symbol: str, exchange: str, current_price: float) -> Dict:
        """Generate realistic synthetic liquidation data for exchanges"""
        import random
        
        try:
            exchange_info = self.exchanges.get(exchange, {})
            weight = exchange_info.get('weight', 0.1)
            
            # Base volume scaled by exchange weight
            base_volume = current_price * 1000000 * weight  # $1M base per exchange weight
            
            liquidation_levels = []
            
            # Generate liquidation clusters
            for i in range(15):  # 15 levels per exchange
                # Price distance from current (1% to 15% away)
                distance = random.uniform(0.01, 0.15)
                
                if random.choice([True, False]):
                    # Above current price (short liquidations)
                    price = current_price * (1 + distance)
                    liq_type = 'short_liquidation'
                else:
                    # Below current price (long liquidations)
                    price = current_price * (1 - distance)
                    liq_type = 'long_liquidation'
                
                volume = base_volume * random.uniform(0.1, 2.0)  # Vary volume
                
                liquidation_levels.append({
                    'price': price,
                    'volume': volume,
                    'type': liq_type,
                    'distance_percent': distance * 100,
                    'leverage': random.choice([5, 10, 20, 50, 100])
                })
            
            return {
                'exchange': exchange,
                'liquidation_levels': liquidation_levels,
                'total_liquidation_volume': sum(l['volume'] for l in liquidation_levels),
                'source': 'synthetic'
            }
            
        except Exception as e:
            logger.error(f"Error generating synthetic liquidations for {exchange}: {e}")
            return {}

    def _create_liquidation_matrix(self, exchanges_data: Dict, price_range: Dict, current_price: float) -> Dict:
        """Create 2D liquidation matrix like Coinglass heatmap"""
        try:
            price_levels = price_range.get('price_levels', [])
            if not price_levels:
                return {'matrix': [], 'levels': [], 'summary': {}}
            
            # Time points (last 24 hours in 1-hour intervals)
            time_points = []
            for i in range(24):
                time_point = datetime.now(timezone.utc) - timedelta(hours=23-i)
                time_points.append(time_point.isoformat())
            
            # Initialize matrix
            matrix = []
            aggregated_levels = {}
            
            for time_idx, time_point in enumerate(time_points):
                time_row = []
                
                for price_idx, price_level in enumerate(price_levels):
                    # Aggregate liquidation density at this price level across all exchanges
                    total_density = 0
                    
                    for exchange, data in exchanges_data.items():
                        if 'liquidation_levels' in data:
                            for level in data['liquidation_levels']:
                                level_price = level['price']
                                # Check if this liquidation level is close to current price level
                                if abs(level_price - price_level) <= (current_price * 0.005):  # Within 0.5%
                                    # Add time-based variation
                                    time_factor = 1 + np.sin(time_idx * 0.3) * 0.3
                                    total_density += level['volume'] * time_factor
                    
                    time_row.append({
                        'time': time_point,
                        'price': price_level,
                        'density': total_density,
                        'normalized_density': 0  # Will be calculated later
                    })
                    
                    # Aggregate for levels summary
                    if price_level not in aggregated_levels:
                        aggregated_levels[price_level] = {
                            'price': price_level,
                            'total_volume': 0,
                            'long_volume': 0,
                            'short_volume': 0,
                            'above_current': price_level > current_price
                        }
                    
                    aggregated_levels[price_level]['total_volume'] += total_density
                
                matrix.append(time_row)
            
            # Normalize densities for color mapping (0-100)
            all_densities = [cell['density'] for row in matrix for cell in row if cell['density'] > 0]
            if all_densities:
                max_density = max(all_densities)
                min_density = min(all_densities)
                density_range = max_density - min_density if max_density > min_density else 1
                
                for row in matrix:
                    for cell in row:
                        if cell['density'] > 0:
                            cell['normalized_density'] = ((cell['density'] - min_density) / density_range) * 100
            
            # Create levels summary
            levels_list = list(aggregated_levels.values())
            levels_list.sort(key=lambda x: x['price'], reverse=True)
            
            # Calculate summary statistics
            levels_above = [l for l in levels_list if l['above_current']]
            levels_below = [l for l in levels_list if not l['above_current']]
            
            total_above = sum(l['total_volume'] for l in levels_above)
            total_below = sum(l['total_volume'] for l in levels_below)
            
            strongest_above = max(levels_above, key=lambda x: x['total_volume']) if levels_above else None
            strongest_below = max(levels_below, key=lambda x: x['total_volume']) if levels_below else None
            
            # Calculate risk score (0-100, higher = more risky)
            risk_score = 50
            if total_above + total_below > 0:
                above_ratio = total_above / (total_above + total_below)
                # Risk increases if liquidations are heavily skewed
                risk_score = 50 + abs(above_ratio - 0.5) * 100
            
            summary = {
                'total_liquidations_above': total_above,
                'total_liquidations_below': total_below,
                'strongest_level_above': strongest_above,
                'strongest_level_below': strongest_below,
                'risk_score': min(100, max(0, risk_score)),
                'levels_count_above': len(levels_above),
                'levels_count_below': len(levels_below)
            }
            
            return {
                'matrix': matrix,
                'levels': levels_list[:20],  # Top 20 levels
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error creating liquidation matrix: {e}")
            return {'matrix': [], 'levels': [], 'summary': {}}

    async def _fetch_binance_open_interest_detailed(self, symbol: str) -> Optional[Dict]:
        """Fetch detailed open interest data from Binance"""
        try:
            session = await self.get_session()
            binance_symbol = self.supported_symbols[symbol]['binance']
            
            # Get open interest
            oi_url = f"https://fapi.binance.com/fapi/v1/openInterest"
            async with session.get(oi_url, params={'symbol': binance_symbol}) as response:
                if response.status == 200:
                    oi_data = await response.json()
                    
                    # Get 24h ticker
                    ticker_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr"
                    async with session.get(ticker_url, params={'symbol': binance_symbol}) as ticker_response:
                        if ticker_response.status == 200:
                            ticker_data = await ticker_response.json()
                            
                            # Get funding rate
                            funding_url = f"https://fapi.binance.com/fapi/v1/premiumIndex"
                            async with session.get(funding_url, params={'symbol': binance_symbol}) as funding_response:
                                funding_data = {}
                                if funding_response.status == 200:
                                    funding_data = await funding_response.json()
                                
                                return {
                                    'exchange': 'binance',
                                    'open_interest': float(oi_data.get('openInterest', 0)),
                                    'volume_24h': float(ticker_data.get('volume', 0)),
                                    'quote_volume_24h': float(ticker_data.get('quoteVolume', 0)),
                                    'price_change_24h': float(ticker_data.get('priceChangePercent', 0)),
                                    'funding_rate': float(funding_data.get('lastFundingRate', 0)) * 100,
                                    'mark_price': float(funding_data.get('markPrice', 0)),
                                    'trades_count_24h': int(ticker_data.get('count', 0)),
                                    'source': 'binance_api'
                                }
                                
        except Exception as e:
            logger.debug(f"Binance OI detailed fetch error for {symbol}: {e}")
        
        return None

    def _generate_synthetic_exchange_oi(self, symbol: str, exchange: str, exchange_info: Dict, current_price: float) -> Dict:
        """Generate detailed synthetic OI data for exchange"""
        import random
        
        try:
            weight = exchange_info.get('weight', 0.1)
            
            # Base OI calculation
            base_oi = current_price * 10000 * weight  # Realistic OI scaling
            oi_variation = random.uniform(0.5, 1.8)
            open_interest = base_oi * oi_variation
            
            # Volume calculation (usually higher than OI)
            volume_multiplier = random.uniform(2, 8)
            volume_24h = open_interest * volume_multiplier
            
            return {
                'exchange': exchange,
                'open_interest': round(open_interest, 2),
                'volume_24h': round(volume_24h, 2),
                'quote_volume_24h': round(volume_24h * current_price, 2),
                'price_change_24h': random.uniform(-8, 8),
                'funding_rate': random.uniform(-0.1, 0.1),
                'mark_price': current_price * random.uniform(0.999, 1.001),
                'trades_count_24h': random.randint(50000, 500000),
                'oi_share': 0,  # Will be calculated later
                'source': 'synthetic'
            }
            
        except Exception as e:
            logger.error(f"Error generating synthetic OI for {exchange}: {e}")
            return {}

    def _calculate_market_metrics(self, oi_data: Dict) -> Dict:
        """Calculate derived market metrics"""
        try:
            total_oi = oi_data.get('total_open_interest', 0)
            total_volume = oi_data.get('total_volume_24h', 0)
            
            # Calculate OI shares for each exchange
            for exchange, details in oi_data['exchanges_detail'].items():
                if total_oi > 0:
                    details['oi_share'] = (details['open_interest'] / total_oi) * 100
                else:
                    details['oi_share'] = 0
            
            # Calculate aggregate metrics
            funding_rates = [
                details.get('funding_rate', 0) 
                for details in oi_data['exchanges_detail'].values()
            ]
            avg_funding_rate = sum(funding_rates) / len(funding_rates) if funding_rates else 0
            
            # Estimate liquidations (synthetic)
            import random
            liquidations_24h = total_oi * random.uniform(0.01, 0.05)  # 1-5% of OI
            
            return {
                'oi_volume_ratio': (total_oi / total_volume) if total_volume > 0 else 0,
                'oi_dominance': 0,  # Would need market-wide data
                'avg_funding_rate': avg_funding_rate,
                'liquidations_24h': liquidations_24h
            }
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
            return {}

    async def _store_enhanced_smart_money_data(self, data_type: str, symbol: str, data: Dict):
        """Store enhanced smart money data in database"""
        try:
            doc = {
                'data_type': data_type,
                'symbol': symbol,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc)
            }
            
            # Store in enhanced_smart_money_data collection
            await self.db.enhanced_smart_money_data.insert_one(doc)
            
            # Keep only recent data (last 48 hours for enhanced data)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=48)
            await self.db.enhanced_smart_money_data.delete_many({
                'data_type': data_type,
                'symbol': symbol,
                'created_at': {'$lt': cutoff_time}
            })
            
        except Exception as e:
            logger.error(f"Error storing enhanced smart money data: {e}")

    async def get_supported_symbols(self) -> List[Dict]:
        """Get list of supported symbols with display information"""
        return [
            {
                'symbol': symbol,
                'display_name': info['display_name'],
                'price_precision': info['price_precision']
            }
            for symbol, info in self.supported_symbols.items()
        ]

    async def get_enhanced_smart_money_data(self, symbol: str) -> Dict:
        """Get all enhanced smart money data for a symbol"""
        try:
            if symbol not in self.supported_symbols:
                return {
                    'error': f'Symbol {symbol} not supported',
                    'supported_symbols': await self.get_supported_symbols()
                }
            
            # Check if data needs refresh (15 minutes)
            needs_refresh = True
            if symbol in self.last_update:
                time_diff = datetime.now(timezone.utc) - self.last_update[symbol]
                needs_refresh = time_diff.total_seconds() > 900  # 15 minutes
            
            if needs_refresh:
                # Fetch fresh enhanced data
                liquidation_data = await self.fetch_enhanced_liquidation_heatmap(symbol)
                oi_data = await self.fetch_enhanced_open_interest(symbol)
                
                self.last_update[symbol] = datetime.now(timezone.utc)
            else:
                # Use cached data
                liquidation_data = self.cache.get('liquidation_heatmap_2d', {}).get(symbol)
                oi_data = self.cache.get('open_interest_detailed', {}).get(symbol)
            
            return {
                'symbol': symbol,
                'liquidation_heatmap_2d': liquidation_data,
                'open_interest_detailed': oi_data,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced smart money data for {symbol}: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }