#!/usr/bin/env python3
"""
Backend Test Suite for Smart Money Indicators System
Tests the new Smart Money APIs: liquidation heatmaps, open interest, funding rates
"""

import asyncio
import aiohttp
import json
import sys
import os
import websockets
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://liquidation-oracle.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://hydra-trade.preview.emergentagent.com/api/realtime"

class SmartMoneyTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Smart Money Indicators System Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", expected: str = "", actual: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'expected': expected,
            'actual': actual,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            async with self.session.get(url) as response:
                status = response.status
                data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return {
                    'status': status,
                    'data': data,
                    'success': status == expected_status
                }
        except Exception as e:
            return {
                'status': 0,
                'data': str(e),
                'success': False,
                'error': str(e)
            }
    
    async def test_smart_money_all_api(self):
        """Test /api/smart-money/all endpoint for all smart money data"""
        test_name = "Smart Money All Data API"
        
        # Test with focus symbols
        symbols = "BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT"
        response = await self.test_api_endpoint(f"/smart-money/all?symbols={symbols}")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check response structure
        if 'status' not in data or 'data' not in data:
            self.log_test(test_name, "FAIL", "Invalid response structure")
            return
        
        if data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error status: {data}")
            return
        
        smart_money_data = data['data']
        
        # Check if we have data for all 4 focus symbols
        expected_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
        found_symbols = []
        
        for symbol in expected_symbols:
            if symbol in smart_money_data and smart_money_data[symbol]:
                symbol_data = smart_money_data[symbol]
                
                # Check if all three data types are present
                required_types = ['liquidation_heatmap', 'open_interest', 'funding_rates']
                has_all_types = all(data_type in symbol_data and symbol_data[data_type] for data_type in required_types)
                
                if has_all_types:
                    found_symbols.append(symbol)
        
        if len(found_symbols) == 4:  # All 4 symbols working
            self.log_test(
                test_name, 
                "PASS", 
                f"All 4 focus symbols have complete smart money data: {', '.join(found_symbols)}",
                "Complete data for BTC, ETH, SOL, XRP",
                f"4/4 symbols with liquidation, OI, and funding data"
            )
        elif len(found_symbols) >= 2:
            self.log_test(
                test_name, 
                "WARN", 
                f"Partial smart money data for {len(found_symbols)} symbols: {', '.join(found_symbols)}",
                "Complete data for all 4 symbols",
                f"{len(found_symbols)}/4 symbols working"
            )
        else:
            self.log_test(test_name, "FAIL", f"Insufficient smart money data. Found: {found_symbols}")
    
    async def test_liquidation_heatmap_api(self):
        """Test /api/smart-money/liquidation-heatmap/{symbol} endpoint"""
        test_symbols = [
            ('BTC/USDT', 'BTCUSDT'),
            ('ETH/USDT', 'ETHUSDT'), 
            ('SOL/USDT', 'SOLUSDT'),
            ('XRP/USDT', 'XRPUSDT')
        ]
        
        for display_symbol, api_symbol in test_symbols:
            test_name = f"Liquidation Heatmap API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/liquidation-heatmap/{api_symbol}")
            
            if not response['success']:
                self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                continue
            
            data = response['data']
            
            # Check response structure
            if 'status' not in data or 'data' not in data:
                self.log_test(test_name, "FAIL", "Invalid response structure")
                continue
            
            if data['status'] != 'success':
                self.log_test(test_name, "FAIL", f"API returned error: {data}")
                continue
            
            heatmap_data = data['data']
            
            # Validate liquidation heatmap structure
            required_fields = ['symbol', 'timestamp', 'liquidation_levels', 'source']
            missing_fields = [field for field in required_fields if field not in heatmap_data]
            
            if missing_fields:
                self.log_test(test_name, "FAIL", f"Missing fields in heatmap data: {missing_fields}")
                continue
            
            liquidation_levels = heatmap_data.get('liquidation_levels', [])
            
            if len(liquidation_levels) > 0:
                # Check if liquidation levels have realistic price ranges
                sample_level = liquidation_levels[0]
                level_fields = ['price', 'long_liquidation', 'short_liquidation', 'total_liquidation']
                has_level_fields = all(field in sample_level for field in level_fields)
                
                if has_level_fields and sample_level['price'] > 0:
                    # Validate price ranges are realistic for the symbol
                    prices = [level['price'] for level in liquidation_levels]
                    price_range = max(prices) - min(prices)
                    
                    expected_ranges = {
                        'BTC/USDT': (50000, 70000),
                        'ETH/USDT': (2000, 3000), 
                        'SOL/USDT': (100, 200),
                        'XRP/USDT': (0.3, 0.8)
                    }
                    
                    expected_min, expected_max = expected_ranges.get(display_symbol, (0, 999999))
                    
                    if expected_min <= min(prices) and max(prices) <= expected_max * 1.2:  # Allow 20% buffer
                        self.log_test(
                            test_name, 
                            "PASS", 
                            f"Valid liquidation heatmap: {len(liquidation_levels)} levels, price range ${min(prices):.2f}-${max(prices):.2f}",
                            "Realistic price levels with liquidation volumes",
                            f"{len(liquidation_levels)} levels in expected range"
                        )
                    else:
                        self.log_test(
                            test_name, 
                            "WARN", 
                            f"Price range may be unrealistic: ${min(prices):.2f}-${max(prices):.2f}",
                            f"Price range roughly ${expected_min}-${expected_max}",
                            f"${min(prices):.2f}-${max(prices):.2f}"
                        )
                else:
                    self.log_test(test_name, "FAIL", f"Invalid liquidation level structure: {sample_level}")
            else:
                self.log_test(test_name, "FAIL", "No liquidation levels found in heatmap data")
    
    async def test_open_interest_api(self):
        """Test /api/smart-money/open-interest/{symbol} endpoint"""
        test_symbols = [
            ('BTC/USDT', 'BTCUSDT'),
            ('ETH/USDT', 'ETHUSDT'), 
            ('SOL/USDT', 'SOLUSDT'),
            ('XRP/USDT', 'XRPUSDT')
        ]
        
        for display_symbol, api_symbol in test_symbols:
            test_name = f"Open Interest API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/open-interest/{api_symbol}")
            
            if not response['success']:
                self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                continue
            
            data = response['data']
            
            # Check response structure
            if 'status' not in data or 'data' not in data:
                self.log_test(test_name, "FAIL", "Invalid response structure")
                continue
            
            if data['status'] != 'success':
                self.log_test(test_name, "FAIL", f"API returned error: {data}")
                continue
            
            oi_data = data['data']
            
            # Validate open interest structure
            required_fields = ['symbol', 'timestamp', 'total_oi', 'exchanges', 'source']
            missing_fields = [field for field in required_fields if field not in oi_data]
            
            if missing_fields:
                self.log_test(test_name, "FAIL", f"Missing fields in OI data: {missing_fields}")
                continue
            
            exchanges = oi_data.get('exchanges', {})
            total_oi = oi_data.get('total_oi', 0)
            
            if len(exchanges) >= 3 and total_oi > 0:  # Should have multiple exchanges
                # Check if exchanges have proper structure
                exchange_names = list(exchanges.keys())
                sample_exchange = exchanges[exchange_names[0]]
                
                if isinstance(sample_exchange, dict) and 'open_interest' in sample_exchange:
                    # Calculate percentage breakdown
                    exchange_breakdown = []
                    for exchange, data in exchanges.items():
                        if isinstance(data, dict) and 'open_interest' in data:
                            oi_value = data['open_interest']
                            percentage = (oi_value / total_oi) * 100 if total_oi > 0 else 0
                            exchange_breakdown.append(f"{exchange}: {percentage:.1f}%")
                    
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"Multi-exchange OI data: Total ${total_oi:,.0f}, {len(exchanges)} exchanges",
                        "Multiple exchanges with OI breakdown",
                        f"Exchanges: {', '.join(exchange_breakdown[:3])}"
                    )
                else:
                    self.log_test(test_name, "FAIL", f"Invalid exchange data structure: {sample_exchange}")
            else:
                self.log_test(test_name, "FAIL", f"Insufficient OI data: {len(exchanges)} exchanges, total OI: {total_oi}")
    
    async def test_funding_rates_api(self):
        """Test /api/smart-money/funding-rates/{symbol} endpoint"""
        test_symbols = [
            ('BTC/USDT', 'BTCUSDT'),
            ('ETH/USDT', 'ETHUSDT'), 
            ('SOL/USDT', 'SOLUSDT'),
            ('XRP/USDT', 'XRPUSDT')
        ]
        
        for display_symbol, api_symbol in test_symbols:
            test_name = f"Funding Rates API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/funding-rates/{api_symbol}")
            
            if not response['success']:
                self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                continue
            
            data = response['data']
            
            # Check response structure
            if 'status' not in data or 'data' not in data:
                self.log_test(test_name, "FAIL", "Invalid response structure")
                continue
            
            if data['status'] != 'success':
                self.log_test(test_name, "FAIL", f"API returned error: {data}")
                continue
            
            funding_data = data['data']
            
            # Validate funding rates structure
            required_fields = ['symbol', 'timestamp', 'current_funding_rate', 'exchanges', 'source']
            missing_fields = [field for field in required_fields if field not in funding_data]
            
            if missing_fields:
                self.log_test(test_name, "FAIL", f"Missing fields in funding data: {missing_fields}")
                continue
            
            exchanges = funding_data.get('exchanges', {})
            current_rate = funding_data.get('current_funding_rate', 0)
            next_funding_time = funding_data.get('next_funding_time')
            
            # Validate funding rate is in reasonable range (-5% to +5%)
            if -5.0 <= current_rate <= 5.0:
                rate_status = "reasonable"
            else:
                rate_status = "extreme"
            
            if len(exchanges) >= 3 and rate_status == "reasonable":
                # Check if exchanges have proper funding rate structure
                exchange_rates = []
                for exchange, data in exchanges.items():
                    if isinstance(data, dict) and 'funding_rate' in data:
                        rate = data['funding_rate']
                        exchange_rates.append(f"{exchange}: {rate:.4f}%")
                
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Multi-exchange funding rates: Avg {current_rate:.4f}%, {len(exchanges)} exchanges",
                    "Reasonable funding rates (-5% to +5%) from multiple exchanges",
                    f"Rate: {current_rate:.4f}%, Exchanges: {', '.join(exchange_rates[:3])}"
                )
            elif rate_status != "reasonable":
                self.log_test(
                    test_name, 
                    "WARN", 
                    f"Extreme funding rate: {current_rate:.4f}% (may indicate market stress)",
                    "Funding rate between -5% and +5%",
                    f"{current_rate:.4f}%"
                )
            else:
                self.log_test(test_name, "FAIL", f"Insufficient funding data: {len(exchanges)} exchanges")
    
    async def test_focus_symbols_api(self):
        """Test /api/smart-money/focus-symbols endpoint"""
        test_name = "Focus Symbols API"
        
        response = await self.test_api_endpoint("/smart-money/focus-symbols")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check response structure
        if 'status' not in data or 'symbols' not in data:
            self.log_test(test_name, "FAIL", "Invalid response structure")
            return
        
        if data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error status: {data}")
            return
        
        symbols = data['symbols']
        expected_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
        
        if symbols == expected_symbols:
            self.log_test(
                test_name, 
                "PASS", 
                f"Focus symbols correctly configured: {', '.join(symbols)}",
                "BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT",
                f"{', '.join(symbols)}"
            )
        else:
            self.log_test(
                test_name, 
                "WARN", 
                f"Focus symbols differ from expected: {', '.join(symbols)}",
                "BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT",
                f"{', '.join(symbols)}"
            )
    
    async def test_data_quality_validation(self):
        """Test data quality across all smart money indicators"""
        test_name = "Smart Money Data Quality"
        
        # Get all smart money data
        response = await self.test_api_endpoint("/smart-money/all?symbols=BTC/USDT,ETH/USDT")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        if 'data' not in data:
            self.log_test(test_name, "FAIL", "No data in response")
            return
        
        smart_money_data = data['data']
        quality_issues = []
        quality_passes = []
        
        for symbol, symbol_data in smart_money_data.items():
            if not symbol_data:
                continue
                
            # Check liquidation heatmap quality
            if 'liquidation_heatmap' in symbol_data and symbol_data['liquidation_heatmap']:
                heatmap = symbol_data['liquidation_heatmap']
                levels = heatmap.get('liquidation_levels', [])
                
                if len(levels) >= 10:  # Should have reasonable number of levels
                    prices = [level.get('price', 0) for level in levels if level.get('price', 0) > 0]
                    if len(prices) >= 10:
                        price_range = max(prices) - min(prices)
                        avg_price = sum(prices) / len(prices)
                        
                        # Price range should be reasonable (not too narrow or too wide)
                        range_ratio = price_range / avg_price
                        if 0.05 <= range_ratio <= 0.5:  # 5% to 50% range
                            quality_passes.append(f"{symbol} liquidation levels have realistic price spread")
                        else:
                            quality_issues.append(f"{symbol} liquidation price range may be unrealistic: {range_ratio:.2%}")
                    else:
                        quality_issues.append(f"{symbol} liquidation levels missing valid prices")
                else:
                    quality_issues.append(f"{symbol} insufficient liquidation levels: {len(levels)}")
            
            # Check open interest quality
            if 'open_interest' in symbol_data and symbol_data['open_interest']:
                oi = symbol_data['open_interest']
                exchanges = oi.get('exchanges', {})
                total_oi = oi.get('total_oi', 0)
                
                if len(exchanges) >= 3 and total_oi > 0:
                    # Check if exchange distribution is reasonable (no single exchange > 80%)
                    max_exchange_share = 0
                    for exchange, exchange_data in exchanges.items():
                        if isinstance(exchange_data, dict) and 'open_interest' in exchange_data:
                            share = exchange_data['open_interest'] / total_oi
                            max_exchange_share = max(max_exchange_share, share)
                    
                    if max_exchange_share <= 0.8:
                        quality_passes.append(f"{symbol} OI well distributed across exchanges")
                    else:
                        quality_issues.append(f"{symbol} OI too concentrated in one exchange: {max_exchange_share:.1%}")
                else:
                    quality_issues.append(f"{symbol} insufficient OI data: {len(exchanges)} exchanges")
            
            # Check funding rates quality
            if 'funding_rates' in symbol_data and symbol_data['funding_rates']:
                funding = symbol_data['funding_rates']
                current_rate = funding.get('current_funding_rate', 0)
                exchanges = funding.get('exchanges', {})
                
                if -2.0 <= current_rate <= 2.0:  # Reasonable funding rate range
                    quality_passes.append(f"{symbol} funding rate within normal range: {current_rate:.4f}%")
                else:
                    quality_issues.append(f"{symbol} extreme funding rate: {current_rate:.4f}%")
        
        # Evaluate overall quality
        total_checks = len(quality_passes) + len(quality_issues)
        if total_checks == 0:
            self.log_test(test_name, "FAIL", "No data quality checks could be performed")
        elif len(quality_issues) == 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"All {len(quality_passes)} data quality checks passed",
                "High quality smart money data",
                f"{len(quality_passes)} quality checks passed"
            )
        elif len(quality_passes) > len(quality_issues):
            self.log_test(
                test_name, 
                "WARN", 
                f"Most quality checks passed: {len(quality_passes)} passed, {len(quality_issues)} issues",
                "All quality checks passing",
                f"Issues: {'; '.join(quality_issues[:2])}"
            )
        else:
            self.log_test(
                test_name, 
                "FAIL", 
                f"Multiple quality issues: {len(quality_issues)} issues, {len(quality_passes)} passed",
                "High quality data",
                f"Issues: {'; '.join(quality_issues[:3])}"
            )
    
    async def test_data_sources_verification(self):
        """Test multiple data sources are working (Binance, synthetic, aggregated)"""
        test_name = "Smart Money Data Sources"
        
        response = await self.test_api_endpoint("/smart-money/all?symbols=BTC/USDT,ETH/USDT")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        if 'data' not in data:
            self.log_test(test_name, "FAIL", "No data in response")
            return
        
        smart_money_data = data['data']
        sources_found = set()
        
        # Check what data sources are being used
        for symbol, symbol_data in smart_money_data.items():
            if not symbol_data:
                continue
                
            for data_type, type_data in symbol_data.items():
                if type_data and 'source' in type_data:
                    sources_found.add(type_data['source'])
        
        expected_sources = ['binance', 'synthetic', 'aggregated', 'coinglass']
        found_expected = [source for source in expected_sources if source in sources_found]
        
        if len(found_expected) >= 2:
            self.log_test(
                test_name, 
                "PASS", 
                f"Multiple data sources active: {', '.join(sources_found)}",
                "At least 2 different data sources",
                f"{len(sources_found)} sources: {', '.join(sources_found)}"
            )
        elif len(sources_found) > 0:
            self.log_test(
                test_name, 
                "WARN", 
                f"Limited data sources: {', '.join(sources_found)}",
                "Multiple data sources",
                f"1 source: {', '.join(sources_found)}"
            )
        else:
            self.log_test(test_name, "FAIL", "No data sources identified in response")

    async def test_api_performance(self):
        """Test Smart Money API response times"""
        test_name = "Smart Money API Performance"
        
        # Test performance of the main endpoint
        start_time = datetime.now()
        response = await self.test_api_endpoint("/smart-money/all?symbols=BTC/USDT,ETH/USDT")
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        # Smart Money API should respond within 2 seconds
        if response_time < 2.0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Excellent response time: {response_time:.3f}s",
                "Response time < 2s",
                f"{response_time:.3f}s"
            )
        elif response_time < 5.0:
            self.log_test(
                test_name, 
                "WARN", 
                f"Acceptable response time: {response_time:.3f}s",
                "Response time < 2s",
                f"{response_time:.3f}s"
            )
        else:
            self.log_test(
                test_name, 
                "FAIL", 
                f"Slow response time: {response_time:.3f}s",
                "Response time < 2s",
                f"{response_time:.3f}s"
            )
    
    async def test_enhanced_smart_money_supported_symbols(self):
        """Test /api/enhanced-smart-money/supported-symbols endpoint"""
        test_name = "Enhanced Smart Money Supported Symbols API"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/supported-symbols")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check response structure
        if 'status' not in data or 'symbols' not in data:
            self.log_test(test_name, "FAIL", "Invalid response structure")
            return
        
        if data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error status: {data}")
            return
        
        symbols = data['symbols']
        expected_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
        
        # Check if all expected symbols are present
        found_symbols = [s['symbol'] for s in symbols if isinstance(s, dict) and 'symbol' in s]
        missing_symbols = [s for s in expected_symbols if s not in found_symbols]
        
        if not missing_symbols:
            self.log_test(
                test_name, 
                "PASS", 
                f"All expected symbols supported: {', '.join(found_symbols)}",
                "BTC, ETH, SOL, XRP supported",
                f"{len(found_symbols)} symbols: {', '.join(found_symbols)}"
            )
        else:
            self.log_test(
                test_name, 
                "WARN", 
                f"Missing symbols: {', '.join(missing_symbols)}. Found: {', '.join(found_symbols)}",
                "All expected symbols present",
                f"Missing: {', '.join(missing_symbols)}"
            )

    async def test_enhanced_smart_money_data_with_timeframes(self):
        """Test /api/enhanced-smart-money/data endpoint with different timeframes"""
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
        test_timeframes = ['1day', '3day', '1week']
        
        for symbol in test_symbols:
            for timeframe in test_timeframes:
                test_name = f"Enhanced Smart Money Data - {symbol} ({timeframe})"
                
                response = await self.test_api_endpoint(f"/enhanced-smart-money/data?symbol={symbol}&timeframe={timeframe}")
                
                if not response['success']:
                    self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                    continue
                
                data = response['data']
                
                # Check response structure
                if 'status' not in data:
                    self.log_test(test_name, "FAIL", "Invalid response structure - missing status")
                    continue
                
                if data['status'] != 'success':
                    self.log_test(test_name, "FAIL", f"API returned error: {data}")
                    continue
                
                # Check for required fields in the nested data structure
                if 'data' not in data:
                    self.log_test(test_name, "FAIL", "Missing 'data' field in response")
                    continue
                
                nested_data = data['data']
                required_fields = ['symbol', 'timeframe', 'liquidation_heatmap_2d']
                missing_fields = [field for field in required_fields if field not in nested_data]
                
                if missing_fields:
                    self.log_test(test_name, "FAIL", f"Missing required fields: {missing_fields}")
                    continue
                
                # Validate timeframe matches request
                if nested_data.get('timeframe') != timeframe:
                    self.log_test(test_name, "FAIL", f"Timeframe mismatch: expected {timeframe}, got {nested_data.get('timeframe')}")
                    continue
                
                # Check liquidation heatmap 2D data
                heatmap_2d = nested_data.get('liquidation_heatmap_2d')
                if heatmap_2d and isinstance(heatmap_2d, dict):
                    # Check for directional bias
                    if 'directional_bias' in heatmap_2d:
                        bias = heatmap_2d['directional_bias']
                        if isinstance(bias, dict) and 'bias' in bias and 'strength' in bias:
                            self.log_test(
                                test_name, 
                                "PASS", 
                                f"Enhanced data with timeframe: {timeframe}, bias: {bias.get('bias', 'unknown')} (strength: {bias.get('strength', 0):.2f})",
                                f"Valid enhanced data with {timeframe} timeframe",
                                f"Bias: {bias.get('bias', 'unknown')}, Strength: {bias.get('strength', 0):.2f}"
                            )
                        else:
                            self.log_test(test_name, "WARN", f"Directional bias data incomplete for {timeframe}")
                    else:
                        self.log_test(test_name, "WARN", f"Missing directional bias for {timeframe}")
                else:
                    self.log_test(test_name, "FAIL", f"Invalid or missing liquidation heatmap 2D data for {timeframe}")

    async def test_enhanced_liquidation_heatmap_2d_timeframes(self):
        """Test /api/enhanced-smart-money/liquidation-heatmap-2d endpoint with timeframes"""
        test_symbols = ['BTC/USDT', 'ETH/USDT']
        test_timeframes = ['1day', '3day', '1week']
        
        for symbol in test_symbols:
            for timeframe in test_timeframes:
                test_name = f"Enhanced Liquidation Heatmap 2D - {symbol} ({timeframe})"
                
                response = await self.test_api_endpoint(f"/enhanced-smart-money/liquidation-heatmap-2d?symbol={symbol}&timeframe={timeframe}")
                
                if not response['success']:
                    self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                    continue
                
                data = response['data']
                
                # Check response structure
                if 'status' not in data:
                    self.log_test(test_name, "FAIL", "Invalid response structure")
                    continue
                
                if data['status'] != 'success':
                    self.log_test(test_name, "FAIL", f"API returned error: {data}")
                    continue
                
                # Check for liquidation levels with cluster strength and timeframe impact
                # The data might be nested under 'data' field
                levels_data = data.get('data', data)  # Try nested first, fallback to root
                if 'liquidation_levels' in levels_data:
                    levels = levels_data['liquidation_levels']
                    if isinstance(levels, list) and len(levels) > 0:
                        # Check if levels have timeframe-specific fields
                        sample_level = levels[0]
                        timeframe_fields = ['cluster_strength', 'timeframe_impact']
                        has_timeframe_fields = all(field in sample_level for field in timeframe_fields)
                        
                        if has_timeframe_fields:
                            # Check if timeframe_impact matches requested timeframe
                            if sample_level.get('timeframe_impact') == timeframe:
                                self.log_test(
                                    test_name, 
                                    "PASS", 
                                    f"Liquidation heatmap 2D with {timeframe} timeframe: {len(levels)} levels, cluster strength: {sample_level.get('cluster_strength')}",
                                    f"Valid 2D heatmap with {timeframe} timeframe features",
                                    f"{len(levels)} levels with timeframe impact"
                                )
                            else:
                                self.log_test(test_name, "WARN", f"Timeframe impact mismatch: expected {timeframe}, got {sample_level.get('timeframe_impact')}")
                        else:
                            self.log_test(test_name, "WARN", f"Missing timeframe-specific fields: {timeframe_fields}")
                    else:
                        self.log_test(test_name, "FAIL", f"No liquidation levels found for {timeframe}")
                else:
                    self.log_test(test_name, "FAIL", f"Missing liquidation_levels in response for {timeframe}")

    async def test_directional_bias_calculations(self):
        """Test directional bias calculations with different timeframes"""
        test_name = "Directional Bias Calculations"
        
        # Test with BTC/USDT for different timeframes
        symbol = "BTC/USDT"
        timeframes = ['1day', '3day', '1week']
        bias_results = []
        
        for timeframe in timeframes:
            response = await self.test_api_endpoint(f"/enhanced-smart-money/data?symbol={symbol}&timeframe={timeframe}")
            
            if response['success'] and response['data'].get('status') == 'success':
                data = response['data']
                # Handle nested data structure
                nested_data = data.get('data', {})
                heatmap_2d = nested_data.get('liquidation_heatmap_2d', {})
                
                if 'directional_bias' in heatmap_2d:
                    bias = heatmap_2d['directional_bias']
                    bias_results.append({
                        'timeframe': timeframe,
                        'bias': bias.get('bias', 'unknown'),
                        'strength': bias.get('strength', 0),
                        'above_ratio': bias.get('above_ratio', 0),
                        'below_ratio': bias.get('below_ratio', 0)
                    })
        
        if len(bias_results) >= 2:
            # Check if different timeframes return different data (they should)
            different_data = False
            for i in range(1, len(bias_results)):
                if (bias_results[i]['strength'] != bias_results[0]['strength'] or 
                    bias_results[i]['above_ratio'] != bias_results[0]['above_ratio']):
                    different_data = True
                    break
            
            if different_data:
                bias_summary = ', '.join([f"{r['timeframe']}: {r['bias']} ({r['strength']:.2f})" for r in bias_results])
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Directional bias varies by timeframe: {bias_summary}",
                    "Different bias calculations for different timeframes",
                    f"{len(bias_results)} timeframes with varying bias data"
                )
            else:
                self.log_test(
                    test_name, 
                    "WARN", 
                    f"Directional bias appears identical across timeframes",
                    "Different bias for different timeframes",
                    "Same bias values across timeframes"
                )
        else:
            self.log_test(test_name, "FAIL", f"Insufficient bias data collected: {len(bias_results)} timeframes")

    async def test_timeframe_validation(self):
        """Test timeframe parameter validation"""
        test_name = "Timeframe Parameter Validation"
        
        symbol = "BTC/USDT"
        valid_timeframes = ['1day', '3day', '1week']
        invalid_timeframes = ['1hour', '5min', 'invalid']
        
        valid_count = 0
        invalid_handled = 0
        
        # Test valid timeframes
        for timeframe in valid_timeframes:
            response = await self.test_api_endpoint(f"/enhanced-smart-money/data?symbol={symbol}&timeframe={timeframe}")
            if response['success'] and response['data'].get('status') == 'success':
                valid_count += 1
        
        # Test invalid timeframes (should return error or default)
        for timeframe in invalid_timeframes:
            response = await self.test_api_endpoint(f"/enhanced-smart-money/data?symbol={symbol}&timeframe={timeframe}")
            if not response['success'] or response['data'].get('status') != 'success':
                invalid_handled += 1
        
        if valid_count == len(valid_timeframes) and invalid_handled == len(invalid_timeframes):
            self.log_test(
                test_name, 
                "PASS", 
                f"Timeframe validation working: {valid_count} valid accepted, {invalid_handled} invalid rejected",
                "Valid timeframes accepted, invalid rejected",
                f"{valid_count}/{len(valid_timeframes)} valid, {invalid_handled}/{len(invalid_timeframes)} invalid handled"
            )
        elif valid_count == len(valid_timeframes):
            self.log_test(
                test_name, 
                "WARN", 
                f"Valid timeframes work but invalid handling unclear: {invalid_handled}/{len(invalid_timeframes)} invalid handled",
                "All timeframes properly validated",
                f"Valid: {valid_count}/{len(valid_timeframes)}, Invalid handled: {invalid_handled}/{len(invalid_timeframes)}"
            )
        else:
            self.log_test(
                test_name, 
                "FAIL", 
                f"Timeframe validation issues: {valid_count}/{len(valid_timeframes)} valid work, {invalid_handled}/{len(invalid_timeframes)} invalid handled",
                "All valid timeframes should work",
                f"Only {valid_count} valid timeframes working"
            )

    async def run_all_tests(self):
        """Run all test cases for Smart Money Indicators system"""
        await self.setup()
        
        try:
            # Core Smart Money functionality tests
            await self.test_smart_money_all_api()
            await self.test_liquidation_heatmap_api()
            await self.test_open_interest_api()
            await self.test_funding_rates_api()
            await self.test_focus_symbols_api()
            await self.test_data_quality_validation()
            await self.test_data_sources_verification()
            await self.test_api_performance()
            
            # Enhanced Smart Money functionality tests (NEW)
            await self.test_enhanced_smart_money_supported_symbols()
            await self.test_enhanced_smart_money_data_with_timeframes()
            await self.test_enhanced_liquidation_heatmap_2d_timeframes()
            await self.test_directional_bias_calculations()
            await self.test_timeframe_validation()
            
        finally:
            await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 SMART MONEY INDICATORS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Show warnings
        if warned_tests > 0:
            print("⚠️  WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        print("=" * 60)

async def main():
    """Main test runner"""
    tester = SmartMoneyTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())