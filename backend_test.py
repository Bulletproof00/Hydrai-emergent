#!/usr/bin/env python3
"""
Backend Test Suite for MarketData Real-Time Fix
Tests the enhanced MarketData functionality with real-time traditional market data
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://hydra-trade.preview.emergentagent.com/api"

class MarketDataTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting MarketData Real-Time Fix Tests")
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
    
    async def test_nasdaq_current_price(self):
        """Test NASDAQ current price - should show ~$24,127 not $22,775"""
        test_name = "NASDAQ Current Price Fix"
        
        response = await self.test_api_endpoint("/chart-data/NASDAQ?timeframe=1d&limit=1")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        if 'data' not in data or not data['data']:
            self.log_test(test_name, "FAIL", "No chart data returned")
            return
        
        latest_candle = data['data'][-1]
        current_price = latest_candle['close']
        
        # Check if price is in expected range (should be around $24,127, not $22,775)
        if current_price > 23000:  # Should be above 23k
            self.log_test(
                test_name, 
                "PASS", 
                f"NASDAQ price is ${current_price:.2f} - appears to be current/real-time",
                "Price > $23,000 (current market)",
                f"${current_price:.2f}"
            )
        else:
            self.log_test(
                test_name, 
                "FAIL", 
                f"NASDAQ price ${current_price:.2f} appears outdated",
                "Price > $23,000 (current market)", 
                f"${current_price:.2f}"
            )
    
    async def test_traditional_markets(self):
        """Test all traditional market symbols"""
        symbols = ['SPX', 'NASDAQ', 'DXY', 'GOLD']
        
        for symbol in symbols:
            test_name = f"{symbol} Market Data"
            
            response = await self.test_api_endpoint(f"/chart-data/{symbol}?timeframe=1d&limit=10")
            
            if not response['success']:
                self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                continue
            
            data = response['data']
            if 'data' not in data or not data['data']:
                self.log_test(test_name, "FAIL", "No chart data returned")
                continue
            
            latest_candle = data['data'][-1]
            current_price = latest_candle['close']
            
            # Basic validation - price should be reasonable
            if current_price > 0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"{symbol} price: ${current_price:.2f}, {len(data['data'])} candles",
                    "Valid price data",
                    f"${current_price:.2f}"
                )
            else:
                self.log_test(test_name, "FAIL", f"Invalid price: ${current_price:.2f}")
    
    async def test_crypto_data_still_works(self):
        """Test that crypto data still works after traditional market fixes"""
        crypto_symbols = ['BTC/USDT', 'ETH/USDT']
        
        for symbol in crypto_symbols:
            test_name = f"{symbol} Crypto Data"
            
            # Convert symbol for URL (BTC/USDT -> BTC-USDT)
            url_symbol = symbol.replace('/', '-')
            response = await self.test_api_endpoint(f"/chart-data/{url_symbol}?timeframe=1h&limit=10")
            
            if not response['success']:
                self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
                continue
            
            data = response['data']
            if 'data' not in data or not data['data']:
                self.log_test(test_name, "FAIL", "No chart data returned")
                continue
            
            latest_candle = data['data'][-1]
            current_price = latest_candle['close']
            
            # Validate crypto prices are reasonable
            expected_ranges = {
                'BTC/USDT': (20000, 200000),  # BTC should be between $20k-$200k
                'ETH/USDT': (1000, 20000)     # ETH should be between $1k-$20k
            }
            
            min_price, max_price = expected_ranges[symbol]
            if min_price <= current_price <= max_price:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"{symbol} price: ${current_price:.2f}, {len(data['data'])} candles",
                    f"Price between ${min_price}-${max_price}",
                    f"${current_price:.2f}"
                )
            else:
                self.log_test(
                    test_name, 
                    "FAIL", 
                    f"Price ${current_price:.2f} outside expected range",
                    f"Price between ${min_price}-${max_price}",
                    f"${current_price:.2f}"
                )
    
    async def test_force_refresh_endpoint(self):
        """Test the new force-refresh endpoint"""
        test_name = "Force Refresh Endpoint"
        
        try:
            url = f"{BACKEND_URL}/data/force-refresh/NASDAQ?timeframe=1d"
            async with self.session.post(url) as response:
                status = response.status
                data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                if status != 200:
                    self.log_test(test_name, "FAIL", f"HTTP {status}: {data}")
                    return
                
                response = {'status': status, 'data': data, 'success': True}
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Request failed: {str(e)}")
            return
        
        data = response['data']
        
        # Check response structure
        required_fields = ['status', 'symbol', 'timeframe', 'bars_refreshed', 'latest_price', 'asset_type']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
            return
        
        if data['status'] == 'success' and data['latest_price'] > 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"Refreshed {data['bars_refreshed']} bars, latest price: ${data['latest_price']:.2f}",
                "Successful refresh with valid price",
                f"Status: {data['status']}, Price: ${data['latest_price']:.2f}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Refresh failed or invalid price: {data}")
    
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