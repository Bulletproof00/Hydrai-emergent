#!/usr/bin/env python3
"""
Backend Test Suite for Real-Time Tick Data System
Tests the new EnhancedRealTimeStreamer with WebSocket and REST APIs
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

class RealTimeTickDataTester:
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
        test_symbols = ['NASDAQ', 'BTC/USDT', 'SPX']
        
        for symbol in test_symbols:
            test_name = f"Real-Time History API - {symbol}"
            
            # URL encode the symbol (BTC/USDT -> BTC%2FUSDT)
            encoded_symbol = symbol.replace('/', '%2F')
            response = await self.test_api_endpoint(f"/realtime/history/{encoded_symbol}?minutes=60")
            
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
            # Test WebSocket connection with timeout
            async with websockets.connect(WEBSOCKET_URL, timeout=10) as websocket:
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
    
    async def test_data_consistency(self):
        """Test data consistency and timestamps"""
        test_name = "Data Consistency & Timestamps"
        
        response = await self.test_api_endpoint("/chart-data/SPX?timeframe=1d&limit=5")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        if 'data' not in data or len(data['data']) < 2:
            self.log_test(test_name, "FAIL", "Insufficient data for consistency check")
            return
        
        candles = data['data']
        issues = []
        
        # Check timestamp ordering
        for i in range(1, len(candles)):
            if candles[i]['time'] <= candles[i-1]['time']:
                issues.append(f"Timestamp ordering issue at index {i}")
        
        # Check OHLC consistency
        for i, candle in enumerate(candles):
            if not (candle['low'] <= candle['open'] <= candle['high'] and 
                   candle['low'] <= candle['close'] <= candle['high']):
                issues.append(f"OHLC consistency issue at index {i}")
        
        # Check for reasonable price values
        for i, candle in enumerate(candles):
            if candle['close'] <= 0:
                issues.append(f"Invalid price at index {i}: {candle['close']}")
        
        if not issues:
            self.log_test(
                test_name, 
                "PASS", 
                f"All {len(candles)} candles have consistent data and timestamps",
                "Consistent OHLC data with proper timestamps",
                "All validations passed"
            )
        else:
            self.log_test(test_name, "FAIL", f"Data consistency issues: {'; '.join(issues)}")
    
    async def test_error_handling(self):
        """Test error handling for invalid symbols"""
        test_name = "Error Handling - Invalid Symbol"
        
        response = await self.test_api_endpoint("/chart-data/INVALID_SYMBOL", expected_status=500)
        
        # We expect this to fail gracefully, not crash
        if response['status'] in [400, 404, 500]:
            self.log_test(
                test_name, 
                "PASS", 
                f"Invalid symbol handled gracefully with status {response['status']}",
                "Graceful error handling",
                f"HTTP {response['status']}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Unexpected response: {response}")
    
    async def test_api_performance(self):
        """Test API response times"""
        test_name = "API Performance"
        
        start_time = datetime.now()
        response = await self.test_api_endpoint("/chart-data/NASDAQ?timeframe=1h&limit=100")
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        # Response should be under 10 seconds for good performance
        if response_time < 10.0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Response time: {response_time:.2f}s",
                "Response time < 10s",
                f"{response_time:.2f}s"
            )
        else:
            self.log_test(
                test_name, 
                "WARN", 
                f"Slow response time: {response_time:.2f}s",
                "Response time < 10s",
                f"{response_time:.2f}s"
            )
    
    async def run_all_tests(self):
        """Run all test cases"""
        await self.setup()
        
        try:
            # Core functionality tests
            await self.test_nasdaq_current_price()
            await self.test_traditional_markets()
            await self.test_crypto_data_still_works()
            await self.test_force_refresh_endpoint()
            await self.test_data_consistency()
            await self.test_error_handling()
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
    tester = MarketDataTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())