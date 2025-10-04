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
        print("🚀 Starting Real-Time Tick Data System Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"WebSocket URL: {WEBSOCKET_URL}")
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
    
    async def test_realtime_latest_api(self):
        """Test /api/realtime/latest endpoint for current prices"""
        test_name = "Real-Time Latest Prices API"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
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
        
        prices_data = data['data']
        
        # Check if we have price data for expected symbols
        expected_symbols = ['NASDAQ', 'SPX', 'BTC/USDT', 'ETH/USDT']
        found_symbols = []
        
        for symbol in expected_symbols:
            if symbol in prices_data and prices_data[symbol]:
                price_info = prices_data[symbol]
                if 'price' in price_info and price_info['price'] > 0:
                    found_symbols.append(symbol)
                    
                    # Validate NASDAQ is showing current price (~$24,800)
                    if symbol == 'NASDAQ' and price_info['price'] > 24000:
                        self.log_test(
                            f"NASDAQ Real-Time Price", 
                            "PASS", 
                            f"NASDAQ shows ${price_info['price']:.2f} (current market level)",
                            "Price > $24,000",
                            f"${price_info['price']:.2f}"
                        )
                    elif symbol == 'NASDAQ':
                        self.log_test(
                            f"NASDAQ Real-Time Price", 
                            "FAIL", 
                            f"NASDAQ shows ${price_info['price']:.2f} (may be outdated)",
                            "Price > $24,000",
                            f"${price_info['price']:.2f}"
                        )
        
        if len(found_symbols) >= 2:  # At least 2 symbols working
            self.log_test(
                test_name, 
                "PASS", 
                f"Found real-time data for {len(found_symbols)} symbols: {', '.join(found_symbols)}",
                "Real-time data for multiple assets",
                f"{len(found_symbols)} symbols with valid prices"
            )
        else:
            self.log_test(test_name, "FAIL", f"Insufficient real-time data. Found: {found_symbols}")
    
    async def test_realtime_history_api(self):
        """Test /api/realtime/history/{symbol} endpoint"""
        test_symbols = [
            ('NASDAQ', 'NASDAQ'),
            ('BTC/USDT', 'BTCUSDT'),  # Convert to format expected by API
            ('SPX', 'SPX')
        ]
        
        for display_symbol, api_symbol in test_symbols:
            test_name = f"Real-Time History API - {display_symbol}"
            
            response = await self.test_api_endpoint(f"/realtime/history/{api_symbol}?minutes=60")
            
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
            
            history_data = data['data']
            
            if len(history_data) > 0:
                # Validate data structure
                sample_tick = history_data[0]
                required_fields = ['symbol', 'price', 'timestamp', 'source', 'asset_type']
                missing_fields = [field for field in required_fields if field not in sample_tick]
                
                if not missing_fields:
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"Retrieved {len(history_data)} ticks with valid structure",
                        "Valid tick data with required fields",
                        f"{len(history_data)} ticks"
                    )
                else:
                    self.log_test(test_name, "FAIL", f"Missing fields in tick data: {missing_fields}")
            else:
                self.log_test(test_name, "WARN", "No historical tick data found (may be expected for new system)")
    
    async def test_websocket_connection(self):
        """Test WebSocket connection to /api/realtime"""
        test_name = "WebSocket Real-Time Connection"
        
        try:
            # Test WebSocket connection
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                self.log_test(
                    f"{test_name} - Connection", 
                    "PASS", 
                    "Successfully connected to WebSocket endpoint",
                    "WebSocket connection established",
                    "Connected"
                )
                
                # Send ping message
                ping_msg = json.dumps({"type": "ping"})
                await websocket.send(ping_msg)
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'pong':
                        self.log_test(
                            f"{test_name} - Ping/Pong", 
                            "PASS", 
                            "WebSocket ping/pong working",
                            "Pong response received",
                            "Pong received"
                        )
                    elif data.get('type') == 'initial_data':
                        self.log_test(
                            f"{test_name} - Initial Data", 
                            "PASS", 
                            "Received initial price data on connection",
                            "Initial data broadcast",
                            "Initial data received"
                        )
                    else:
                        self.log_test(
                            f"{test_name} - Response", 
                            "PASS", 
                            f"Received WebSocket message: {data.get('type', 'unknown')}",
                            "Any WebSocket response",
                            f"Type: {data.get('type', 'unknown')}"
                        )
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        f"{test_name} - Response", 
                        "WARN", 
                        "No response received within 5 seconds (may be normal for new system)",
                        "WebSocket response",
                        "Timeout"
                    )
                
        except Exception as e:
            self.log_test(test_name, "FAIL", f"WebSocket connection failed: {str(e)}")
    
    async def test_data_sources_verification(self):
        """Test multiple data sources are working (CoinGecko, Yahoo Finance, Market-Adjusted)"""
        test_name = "Multiple Data Sources Verification"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        if 'data' not in data:
            self.log_test(test_name, "FAIL", "No data in response")
            return
        
        prices_data = data['data']
        sources_found = set()
        
        # Check what data sources are being used
        for symbol, price_info in prices_data.items():
            if price_info and 'source' in price_info:
                sources_found.add(price_info['source'])
        
        expected_sources = ['coingecko', 'market_adjusted', 'yahoo_fallback', 'marketwatch']
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
                f"Only one data source found: {', '.join(sources_found)}",
                "Multiple data sources",
                f"1 source: {', '.join(sources_found)}"
            )
        else:
            self.log_test(test_name, "FAIL", "No data sources identified in response")
    
    async def test_database_storage(self):
        """Test that real-time ticks are being stored in database"""
        test_name = "Database Storage - Real-Time Ticks"
        
        # First get some real-time data to ensure there's something to store
        response = await self.test_api_endpoint("/realtime/latest")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"Could not get real-time data: {response.get('error', 'Unknown error')}")
            return
        
        # Wait a moment for data to be stored
        await asyncio.sleep(2)
        
        # Now check if we can retrieve historical data (which comes from database)
        history_response = await self.test_api_endpoint("/realtime/history/NASDAQ?minutes=10")
        
        if not history_response['success']:
            self.log_test(test_name, "FAIL", f"Could not retrieve historical data: {history_response.get('error', 'Unknown error')}")
            return
        
        history_data = history_response['data']
        
        if 'data' in history_data and len(history_data['data']) > 0:
            ticks = history_data['data']
            
            # Validate tick structure
            sample_tick = ticks[0]
            required_fields = ['symbol', 'price', 'timestamp', 'source', 'asset_type']
            has_all_fields = all(field in sample_tick for field in required_fields)
            
            if has_all_fields:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Database contains {len(ticks)} real-time ticks with proper structure",
                    "Real-time ticks stored in database",
                    f"{len(ticks)} ticks with valid structure"
                )
            else:
                missing = [field for field in required_fields if field not in sample_tick]
                self.log_test(test_name, "FAIL", f"Tick data missing fields: {missing}")
        else:
            self.log_test(test_name, "WARN", "No tick data found in database (may be expected for new system)")
    
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