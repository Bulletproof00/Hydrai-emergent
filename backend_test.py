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
BACKEND_URL = "https://hydra-trade.preview.emergentagent.com/api"
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
        test_symbols = ['BTC%2FUSDT', 'ETH%2FUSDT', 'SOL%2FUSDT', 'XRP%2FUSDT']
        
        for encoded_symbol in test_symbols:
            display_symbol = encoded_symbol.replace('%2F', '/')
            test_name = f"Liquidation Heatmap API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/liquidation-heatmap/{encoded_symbol}")
            
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
        test_symbols = ['BTC%2FUSDT', 'ETH%2FUSDT', 'SOL%2FUSDT', 'XRP%2FUSDT']
        
        for encoded_symbol in test_symbols:
            display_symbol = encoded_symbol.replace('%2F', '/')
            test_name = f"Open Interest API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/open-interest/{encoded_symbol}")
            
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
        test_symbols = ['BTC%2FUSDT', 'ETH%2FUSDT', 'SOL%2FUSDT', 'XRP%2FUSDT']
        
        for encoded_symbol in test_symbols:
            display_symbol = encoded_symbol.replace('%2F', '/')
            test_name = f"Funding Rates API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/smart-money/funding-rates/{encoded_symbol}")
            
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
    
    async def test_tick_simulation(self):
        """Test that price simulation is working between API calls"""
        test_name = "Price Tick Simulation"
        
        # Get initial prices
        response1 = await self.test_api_endpoint("/realtime/latest")
        if not response1['success']:
            self.log_test(test_name, "FAIL", f"Could not get initial prices: {response1.get('error', 'Unknown error')}")
            return
        
        # Wait for simulation to potentially update prices
        await asyncio.sleep(5)
        
        # Get prices again
        response2 = await self.test_api_endpoint("/realtime/latest")
        if not response2['success']:
            self.log_test(test_name, "FAIL", f"Could not get updated prices: {response2.get('error', 'Unknown error')}")
            return
        
        data1 = response1['data'].get('data', {})
        data2 = response2['data'].get('data', {})
        
        # Check if any prices have changed (indicating simulation)
        price_changes = 0
        simulated_ticks = 0
        
        for symbol in data1:
            if symbol in data2 and data1[symbol] and data2[symbol]:
                price1 = data1[symbol].get('price', 0)
                price2 = data2[symbol].get('price', 0)
                
                if abs(price1 - price2) > 0.001:  # Small threshold for floating point comparison
                    price_changes += 1
                
                # Check if tick is marked as simulated
                if data2[symbol].get('simulated'):
                    simulated_ticks += 1
        
        if price_changes > 0 or simulated_ticks > 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Price simulation active: {price_changes} price changes, {simulated_ticks} simulated ticks",
                "Price movements between API calls",
                f"{price_changes} changes, {simulated_ticks} simulated"
            )
        else:
            self.log_test(
                test_name, 
                "WARN", 
                "No price changes detected (simulation may be inactive or very small movements)",
                "Price simulation active",
                "No changes detected"
            )
    
    async def test_multi_asset_support(self):
        """Test support for crypto and traditional markets"""
        test_name = "Multi-Asset Support"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data'].get('data', {})
        
        crypto_assets = []
        traditional_assets = []
        
        for symbol, price_info in data.items():
            if price_info and 'asset_type' in price_info:
                if price_info['asset_type'] == 'crypto':
                    crypto_assets.append(symbol)
                elif price_info['asset_type'] == 'traditional':
                    traditional_assets.append(symbol)
        
        if len(crypto_assets) > 0 and len(traditional_assets) > 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Both asset types supported: {len(crypto_assets)} crypto, {len(traditional_assets)} traditional",
                "Both crypto and traditional assets",
                f"Crypto: {crypto_assets[:3]}, Traditional: {traditional_assets[:3]}"
            )
        elif len(crypto_assets) > 0:
            self.log_test(
                test_name, 
                "WARN", 
                f"Only crypto assets found: {crypto_assets}",
                "Both asset types",
                f"Only crypto: {crypto_assets}"
            )
        elif len(traditional_assets) > 0:
            self.log_test(
                test_name, 
                "WARN", 
                f"Only traditional assets found: {traditional_assets}",
                "Both asset types",
                f"Only traditional: {traditional_assets}"
            )
        else:
            self.log_test(test_name, "FAIL", "No assets with asset_type found")

    async def test_api_performance(self):
        """Test real-time API response times"""
        test_name = "Real-Time API Performance"
        
        start_time = datetime.now()
        response = await self.test_api_endpoint("/realtime/latest")
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        # Real-time API should be very fast (under 1 second)
        if response_time < 1.0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Excellent response time: {response_time:.3f}s",
                "Response time < 1s",
                f"{response_time:.3f}s"
            )
        elif response_time < 3.0:
            self.log_test(
                test_name, 
                "WARN", 
                f"Acceptable response time: {response_time:.3f}s",
                "Response time < 1s",
                f"{response_time:.3f}s"
            )
        else:
            self.log_test(
                test_name, 
                "FAIL", 
                f"Slow response time: {response_time:.3f}s",
                "Response time < 1s",
                f"{response_time:.3f}s"
            )
    
    async def run_all_tests(self):
        """Run all test cases for real-time tick data system"""
        await self.setup()
        
        try:
            # Core real-time functionality tests
            await self.test_realtime_latest_api()
            await self.test_realtime_history_api()
            await self.test_websocket_connection()
            await self.test_data_sources_verification()
            await self.test_database_storage()
            await self.test_tick_simulation()
            await self.test_multi_asset_support()
            await self.test_api_performance()
            
        finally:
            await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
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
    tester = RealTimeTickDataTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())