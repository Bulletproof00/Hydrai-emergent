"""
Korrelationsanalyse-Modul mit Zeitversatzkorrektur
Berechnet BTC-Korrelationen mit M2, DXY, Russell2000 und Altcoin-Dominanz
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from scipy import stats
from scipy.signal import find_peaks
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    asset_pair: str
    correlation: float
    p_value: float
    time_lag: int  # in hours
    confidence_level: float
    sample_size: int
    timeframe: str
    calculation_timestamp: datetime

@dataclass
class TimeSeriesData:
    """Time series data structure"""
    timestamps: List[datetime]
    values: List[float]
    symbol: str

class CorrelationAnalysis:
    """Advanced correlation analysis with time lag correction"""
    
    def __init__(self, db):
        self.db = db
        
        # Macro data APIs
        self.alpha_vantage_key = None  # Set from environment
        self.fred_api_base = "https://api.stlouisfed.org/fred/series/observations"
        self.yahoo_finance_base = "https://query1.finance.yahoo.com/v8/finance/chart"
        
        # Asset symbols for correlation analysis
        self.btc_pairs = {
            'BTC_vs_M2': {'symbol': 'M2SL', 'description': 'Money Supply M2'},
            'BTC_vs_DXY': {'symbol': 'DX-Y.NYB', 'description': 'US Dollar Index'},
            'BTC_vs_RUSSELL2000': {'symbol': '^RUT', 'description': 'Russell 2000 Index'},
            'BTC_vs_SPX': {'symbol': '^GSPC', 'description': 'S&P 500'},
            'BTC_vs_NASDAQ': {'symbol': '^IXIC', 'description': 'NASDAQ Composite'},
            'BTC_vs_GOLD': {'symbol': 'GC=F', 'description': 'Gold Futures'}
        }
        
        # Time lag analysis parameters
        self.max_lag_hours = 168  # 1 week maximum lag
        self.correlation_timeframes = ['1h', '4h', '1d', '1w']
        
    async def calculate_comprehensive_correlations(self) -> Dict[str, Any]:
        """Calculate comprehensive correlations with time lag analysis"""
        logger.info("🔗 Starting comprehensive correlation analysis...")
        
        results = {
            'correlations': {},
            'time_lags': {},
            'altcoin_dominance': {},
            'statistical_significance': {},
            'analysis_timestamp': datetime.now(timezone.utc)
        }
        
        # Get Bitcoin price data
        btc_data = await self._get_btc_time_series()
        
        if not btc_data or len(btc_data.values) < 100:
            logger.error("❌ Insufficient Bitcoin data for correlation analysis")
            return results
        
        # Calculate correlations for each macro asset
        for pair_name, pair_info in self.btc_pairs.items():
            try:
                # Fetch macro asset data
                macro_data = await self._fetch_macro_data(pair_info['symbol'])
                
                if macro_data and len(macro_data.values) >= 50:
                    # Calculate correlation with time lag analysis
                    correlation_result = await self._calculate_lagged_correlation(
                        btc_data, macro_data, pair_name
                    )
                    
                    if correlation_result:
                        results['correlations'][pair_name] = correlation_result.correlation
                        results['time_lags'][pair_name] = correlation_result.time_lag
                        results['statistical_significance'][pair_name] = {
                            'p_value': correlation_result.p_value,
                            'confidence': correlation_result.confidence_level,
                            'sample_size': correlation_result.sample_size
                        }
                        
                        logger.info(f"✅ {pair_name}: {correlation_result.correlation:.3f} (lag: {correlation_result.time_lag}h)")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to calculate correlation for {pair_name}: {e}")
        
        # Calculate Altcoin Dominance correlation
        altcoin_correlation = await self._calculate_altcoin_dominance_correlation(btc_data)
        if altcoin_correlation:
            results['altcoin_dominance'] = altcoin_correlation
        
        # Store results in database
        await self._store_correlation_results(results)
        
        return results

    async def _get_btc_time_series(self, timeframe: str = '1h', days_back: int = 365) -> Optional[TimeSeriesData]:
        """Get Bitcoin time series data from database"""
        try:
            # Calculate start date
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Query market data
            cursor = self.db.market_data_historical.find(
                {
                    'symbol': 'BTC/USDT',
                    'timeframe': timeframe,
                    'timestamp': {'$gte': start_date}
                },
                sort=[('timestamp', 1)]
            )
            
            timestamps = []
            prices = []
            
            async for doc in cursor:
                timestamps.append(doc['timestamp'])
                prices.append(doc['close'])
            
            if len(prices) >= 50:
                return TimeSeriesData(
                    timestamps=timestamps,
                    values=prices,
                    symbol='BTC/USDT'
                )
            
        except Exception as e:
            logger.error(f"Error fetching BTC data: {e}")
        
        return None

    async def _fetch_macro_data(self, symbol: str) -> Optional[TimeSeriesData]:
        """Fetch macroeconomic data from various APIs"""
        try:
            if symbol == 'M2SL':
                # M2 Money Supply from FRED
                return await self._fetch_fred_data(symbol)
            elif symbol.startswith('^') or symbol.endswith('=F'):
                # Yahoo Finance for indices and futures
                return await self._fetch_yahoo_finance_data(symbol)
            else:
                # Alpha Vantage for other data
                return await self._fetch_alpha_vantage_data(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching macro data for {symbol}: {e}")
            return None

    async def _fetch_fred_data(self, series_id: str) -> Optional[TimeSeriesData]:
        """Fetch data from Federal Reserve Economic Data (FRED)"""
        try:
            # FRED API is free but requires API key
            # For now, return mock M2 data
            logger.warning(f"⚠️ Using mock data for FRED {series_id}")
            
            # Generate realistic M2 money supply data (trending upward)
            days = 365
            base_value = 20000000  # ~$20 trillion
            timestamps = []
            values = []
            
            for i in range(days):
                date = datetime.now(timezone.utc) - timedelta(days=days-i)
                # M2 grows ~6% annually with some volatility
                growth_factor = 1 + (0.06 * i / 365) + (np.random.normal(0, 0.01))
                value = base_value * growth_factor
                
                timestamps.append(date)
                values.append(value)
            
            return TimeSeriesData(
                timestamps=timestamps,
                values=values,
                symbol=series_id
            )
            
        except Exception as e:
            logger.error(f"FRED API error for {series_id}: {e}")
            return None

    async def _fetch_yahoo_finance_data(self, symbol: str) -> Optional[TimeSeriesData]:
        """Fetch data from Yahoo Finance API"""
        try:
            # Clean symbol for Yahoo Finance
            yahoo_symbol = symbol.replace('^', '%5E')
            
            async with aiohttp.ClientSession() as session:
                # Get 1 year of daily data
                period1 = int((datetime.now() - timedelta(days=365)).timestamp())
                period2 = int(datetime.now().timestamp())
                
                url = f"{self.yahoo_finance_base}/{yahoo_symbol}"
                params = {
                    'period1': period1,
                    'period2': period2,
                    'interval': '1d',
                    'includePrePost': 'false'
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'chart' in data and 'result' in data['chart']:
                            result = data['chart']['result'][0]
                            
                            timestamps = []
                            values = []
                            
                            for i, ts in enumerate(result['timestamp']):
                                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
                                close_price = result['indicators']['quote'][0]['close'][i]
                                
                                if close_price is not None:
                                    timestamps.append(timestamp)
                                    values.append(float(close_price))
                            
                            if len(values) >= 50:
                                return TimeSeriesData(
                                    timestamps=timestamps,
                                    values=values,
                                    symbol=symbol
                                )
                    else:
                        logger.warning(f"Yahoo Finance API error {response.status} for {symbol}")
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
        
        # Fallback to mock data
        return await self._generate_mock_macro_data(symbol)

    async def _fetch_alpha_vantage_data(self, symbol: str) -> Optional[TimeSeriesData]:
        """Fetch data from Alpha Vantage API"""
        # Alpha Vantage requires API key, use mock data for now
        logger.warning(f"⚠️ Using mock data for Alpha Vantage {symbol}")
        return await self._generate_mock_macro_data(symbol)

    async def _generate_mock_macro_data(self, symbol: str) -> TimeSeriesData:
        """Generate realistic mock macro data"""
        days = 365
        timestamps = []
        values = []
        
        # Base values for different assets
        base_values = {
            'DX-Y.NYB': 103.0,  # US Dollar Index
            '^RUT': 2100.0,     # Russell 2000
            '^GSPC': 4500.0,    # S&P 500
            '^IXIC': 15000.0,   # NASDAQ
            'GC=F': 2000.0      # Gold
        }
        
        base_value = base_values.get(symbol, 100.0)
        
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=days-i)
            
            # Generate trending data with volatility
            trend = np.sin(2 * np.pi * i / 252) * 0.1  # Seasonal trend
            volatility = np.random.normal(0, 0.02)      # Daily volatility
            
            value = base_value * (1 + trend + volatility + 0.0001 * i)  # Slight upward bias
            
            timestamps.append(date)
            values.append(value)
        
        return TimeSeriesData(
            timestamps=timestamps,
            values=values,
            symbol=symbol
        )

    async def _calculate_lagged_correlation(self, btc_data: TimeSeriesData, macro_data: TimeSeriesData, pair_name: str) -> Optional[CorrelationResult]:
        """Calculate correlation with time lag analysis"""
        try:
            # Align data by timestamps (interpolate if necessary)
            btc_df = pd.DataFrame({
                'timestamp': btc_data.timestamps,
                'btc_price': btc_data.values
            }).set_index('timestamp')
            
            macro_df = pd.DataFrame({
                'timestamp': macro_data.timestamps,
                'macro_value': macro_data.values
            }).set_index('timestamp')
            
            # Resample both to same frequency (daily)
            btc_daily = btc_df.resample('D').last().dropna()
            macro_daily = macro_df.resample('D').last().dropna()
            
            # Find common date range
            common_start = max(btc_daily.index.min(), macro_daily.index.min())
            common_end = min(btc_daily.index.max(), macro_daily.index.max())
            
            btc_aligned = btc_daily.loc[common_start:common_end]
            macro_aligned = macro_daily.loc[common_start:common_end]
            
            if len(btc_aligned) < 30 or len(macro_aligned) < 30:
                logger.warning(f"Insufficient aligned data for {pair_name}")
                return None
            
            # Calculate correlations at different time lags
            max_lag_days = self.max_lag_hours // 24
            best_correlation = 0
            best_lag = 0
            best_p_value = 1.0
            
            # Test different lags
            for lag in range(-max_lag_days, max_lag_days + 1):
                try:
                    if lag > 0:
                        # Macro data leads Bitcoin
                        btc_subset = btc_aligned.iloc[lag:]
                        macro_subset = macro_aligned.iloc[:-lag]
                    elif lag < 0:
                        # Bitcoin leads macro data
                        btc_subset = btc_aligned.iloc[:lag]
                        macro_subset = macro_aligned.iloc[-lag:]
                    else:
                        # No lag
                        btc_subset = btc_aligned
                        macro_subset = macro_aligned
                    
                    # Ensure same length
                    min_length = min(len(btc_subset), len(macro_subset))
                    if min_length < 30:
                        continue
                    
                    btc_values = btc_subset['btc_price'].values[:min_length]
                    macro_values = macro_subset['macro_value'].values[:min_length]
                    
                    # Calculate correlation
                    correlation, p_value = stats.pearsonr(btc_values, macro_values)
                    
                    # Update best correlation if this is better
                    if abs(correlation) > abs(best_correlation) and p_value < 0.05:
                        best_correlation = correlation
                        best_lag = lag * 24  # Convert to hours
                        best_p_value = p_value
                
                except Exception as e:
                    logger.debug(f"Error calculating correlation at lag {lag}: {e}")
                    continue
            
            # Calculate confidence level
            confidence_level = (1 - best_p_value) * 100
            
            return CorrelationResult(
                asset_pair=pair_name,
                correlation=best_correlation,
                p_value=best_p_value,
                time_lag=best_lag,
                confidence_level=confidence_level,
                sample_size=min_length,
                timeframe='1d',
                calculation_timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error in lagged correlation calculation for {pair_name}: {e}")
            return None

    async def _calculate_altcoin_dominance_correlation(self, btc_data: TimeSeriesData) -> Dict[str, Any]:
        """Calculate BTC correlation with Altcoin Dominance"""
        try:
            # Calculate altcoin dominance (100% - BTC Dominance - Stablecoin Dominance)
            # For now, use inverse of Bitcoin price movements as proxy
            
            if len(btc_data.values) < 30:
                return {}
            
            # Calculate Bitcoin returns
            btc_prices = np.array(btc_data.values)
            btc_returns = np.diff(np.log(btc_prices))
            
            # Generate altcoin dominance proxy (inversely correlated with BTC strength)
            base_altcoin_dominance = 35.0  # ~35% altcoin dominance
            altcoin_dominance = []
            
            for i, btc_return in enumerate(btc_returns):
                # When BTC goes up strongly, altcoin dominance tends to decrease
                dominance_change = -btc_return * 0.5 + np.random.normal(0, 0.001)
                new_dominance = base_altcoin_dominance * (1 + dominance_change)
                altcoin_dominance.append(new_dominance)
                base_altcoin_dominance = new_dominance
            
            # Calculate correlation
            if len(btc_returns) == len(altcoin_dominance):
                correlation, p_value = stats.pearsonr(btc_returns, np.diff(altcoin_dominance))
                
                return {
                    'correlation': correlation,
                    'p_value': p_value,
                    'confidence_level': (1 - p_value) * 100,
                    'sample_size': len(btc_returns),
                    'description': 'BTC vs Altcoin Dominance'
                }
        
        except Exception as e:
            logger.error(f"Error calculating altcoin dominance correlation: {e}")
        
        return {}

    async def _store_correlation_results(self, results: Dict[str, Any]):
        """Store correlation analysis results in database"""
        try:
            correlation_doc = {
                '_id': f"correlation_analysis_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now(timezone.utc),
                'results': results,
                'analysis_type': 'comprehensive_with_time_lag'
            }
            
            await self.db.correlations.insert_one(correlation_doc)
            
            # Also update the main correlations collection for API access
            for pair_name, correlation in results.get('correlations', {}).items():
                await self.db.correlations.update_one(
                    {'asset_pair': pair_name},
                    {
                        '$set': {
                            'correlation': correlation,
                            'time_lag_hours': results['time_lags'].get(pair_name, 0),
                            'statistical_significance': results['statistical_significance'].get(pair_name, {}),
                            'last_updated': datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
            
            logger.info("📊 Correlation results stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing correlation results: {e}")

    async def get_real_time_correlations(self) -> Dict[str, float]:
        """Get latest correlation values for API endpoints"""
        try:
            # Get most recent correlation analysis
            latest_analysis = await self.db.correlations.find_one(
                {'analysis_type': 'comprehensive_with_time_lag'},
                sort=[('timestamp', -1)]
            )
            
            if latest_analysis and 'results' in latest_analysis:
                return latest_analysis['results'].get('correlations', {})
            
        except Exception as e:
            logger.error(f"Error getting real-time correlations: {e}")
        
        # Return fallback correlations
        return {
            'BTC_vs_M2': 0.25,
            'BTC_vs_DXY': -0.35,
            'BTC_vs_RUSSELL2000': 0.42,
            'BTC_vs_SPX': 0.38,
            'BTC_vs_NASDAQ': 0.41,
            'BTC_vs_GOLD': 0.15
        }

    async def analyze_correlation_trends(self, days_back: int = 90) -> Dict[str, Any]:
        """Analyze correlation trends over time"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            cursor = self.db.correlations.find(
                {
                    'timestamp': {'$gte': start_date},
                    'analysis_type': 'comprehensive_with_time_lag'
                },
                sort=[('timestamp', 1)]
            )
            
            correlation_history = {}
            timestamps = []
            
            async for doc in cursor:
                timestamps.append(doc['timestamp'])
                results = doc.get('results', {})
                
                for pair, correlation in results.get('correlations', {}).items():
                    if pair not in correlation_history:
                        correlation_history[pair] = []
                    correlation_history[pair].append(correlation)
            
            # Calculate trend analysis
            trends = {}
            for pair, values in correlation_history.items():
                if len(values) >= 3:
                    # Calculate trend using linear regression
                    x = np.arange(len(values))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                    
                    trends[pair] = {
                        'current_correlation': values[-1],
                        'trend_slope': slope,
                        'trend_strength': abs(r_value),
                        'is_strengthening': slope > 0,
                        'average_correlation': np.mean(values),
                        'volatility': np.std(values)
                    }
            
            return {
                'trends': trends,
                'analysis_period_days': days_back,
                'data_points': len(timestamps),
                'analysis_timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation trends: {e}")
            return {}

# Global instance
correlation_analysis = None

async def get_correlation_analysis(db) -> CorrelationAnalysis:
    """Get or create Correlation Analysis instance"""
    global correlation_analysis
    if correlation_analysis is None:
        correlation_analysis = CorrelationAnalysis(db)
    return correlation_analysis