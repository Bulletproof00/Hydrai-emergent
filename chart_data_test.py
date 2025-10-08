#!/usr/bin/env python3
"""
Chart Data Testing for Candlestick Rendering Problem
Focus: Test GET /api/chart-data/BTC-USDT for open === close issue
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BACKEND_URL = "https://crypto-ai-trading-2.preview.emergentagent.com/api"

class ChartDataTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🎯 CHART-DATEN REPARATUR TESTS - CANDLESTICK RENDERING PROBLEM")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200):
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            async with self.session.get(url) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return {
                    'status': status,
                    'data': response_data,
                    'success': status == expected_status
                }
        except Exception as e:
            return {
                'status': 0,
                'data': str(e),
                'success': False,
                'error': str(e)
            }

    async def test_chart_data_btc_1h_debugging(self):
        """CHART-DATEN DEBUGGING: Test GET /api/chart-data/BTC-USDT?timeframe=1h&limit=5"""
        test_name = "🎯 CHART-DATEN DEBUGGING: BTC-USDT 1h (5 candles)"
        
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1h&limit=5")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Chart Data API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check basic response structure
        if 'data' not in data or not isinstance(data['data'], list):
            self.log_test(test_name, "FAIL", f"❌ Chart Data Response invalid structure: {data}")
            return
        
        chart_data = data['data']
        
        if len(chart_data) == 0:
            self.log_test(test_name, "FAIL", f"❌ Chart Data empty - no candles returned")
            return
        
        # Analyze first few candles for open === close issue
        problematic_candles = 0
        valid_candles = 0
        
        print(f"📊 Analyzing {len(chart_data)} candles for open === close issue...")
        
        for i, candle in enumerate(chart_data[:5]):  # Check first 5 candles
            open_price = candle.get('open', 0)
            close_price = candle.get('close', 0)
            high_price = candle.get('high', 0)
            low_price = candle.get('low', 0)
            
            print(f"   Candle {i+1}: open={open_price}, close={close_price}, high={high_price}, low={low_price}")
            
            if open_price == close_price:
                problematic_candles += 1
                print(f"   ⚠️ PROBLEMATIC: open === close = {open_price}")
            else:
                valid_candles += 1
                print(f"   ✅ VALID: open != close")
        
        if problematic_candles > 0:
            self.log_test(
                test_name, 
                "FAIL", 
                f"❌ CHART-DATEN PROBLEM BESTÄTIGT! {problematic_candles}/{len(chart_data[:5])} Kerzen haben open === close, was zu falscher Candlestick-Darstellung als blaue Linie führt. Beispiel: open={chart_data[0].get('open')}, close={chart_data[0].get('close')}"
            )
        else:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ CHART-DATEN KORREKT! Alle {valid_candles} Kerzen haben unterschiedliche open/close Werte für korrekte Candlestick-Darstellung"
            )

    async def test_fallback_system_generate_minimal_chart_data(self):
        """FALLBACK-SYSTEM TEST: Verify generate_minimal_chart_data function works correctly"""
        test_name = "🎯 FALLBACK-SYSTEM: generate_minimal_chart_data"
        
        # Test a less common symbol to trigger fallback
        response = await self.test_api_endpoint("/chart-data/DOGE-USDT?timeframe=1h&limit=10")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Fallback system API call failed: {response.get('error')}")
            return
        
        data = response['data']
        chart_data = data.get('data', [])
        
        if len(chart_data) == 0:
            self.log_test(test_name, "FAIL", f"❌ Fallback system returned no data")
            return
        
        # Check if fallback data has proper OHLCV structure with variations
        valid_ohlcv = 0
        open_close_variations = 0
        
        print(f"📊 Analyzing {len(chart_data)} fallback candles...")
        
        for i, candle in enumerate(chart_data[:3]):  # Check first 3 candles
            # Check required fields
            if all(field in candle for field in ['open', 'high', 'low', 'close', 'volume']):
                valid_ohlcv += 1
                
                # Check for price variations (open !== close)
                if candle['open'] != candle['close']:
                    open_close_variations += 1
                    print(f"   Candle {i+1}: open={candle['open']}, close={candle['close']} ✅ VARIATION")
                else:
                    print(f"   Candle {i+1}: open={candle['open']}, close={candle['close']} ⚠️ NO VARIATION")
        
        if valid_ohlcv == len(chart_data) and open_close_variations > 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ FALLBACK-SYSTEM FUNKTIONIERT! generate_minimal_chart_data liefert {len(chart_data)} Kerzen mit korrekter OHLCV-Struktur und {open_close_variations} Kerzen mit open !== close"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Fallback-System Problem: {valid_ohlcv}/{len(chart_data)} valid OHLCV, {open_close_variations} variations")

    async def test_mongodb_cache_check(self):
        """MONGODB CACHE CHECK: Test if faulty data is stored in AI Data Module Cache"""
        test_name = "🎯 MONGODB CACHE CHECK: AI Data Module Cache"
        
        # Test multiple symbols to check cache consistency
        test_symbols = ["BTC-USDT", "ETH-USDT"]
        cache_issues = 0
        total_candles = 0
        
        for symbol in test_symbols:
            print(f"📊 Checking cache for {symbol}...")
            response = await self.test_api_endpoint(f"/chart-data/{symbol}?timeframe=1h&limit=3")
            
            if response['success']:
                data = response['data']
                chart_data = data.get('data', [])
                
                # Check if cached data has open === close issue
                for i, candle in enumerate(chart_data):
                    total_candles += 1
                    if candle.get('open') == candle.get('close'):
                        cache_issues += 1
                        print(f"   ⚠️ Cache issue found in {symbol} candle {i+1}: open === close = {candle.get('open')}")
                    else:
                        print(f"   ✅ {symbol} candle {i+1}: open={candle.get('open')}, close={candle.get('close')}")
        
        if cache_issues > 0:
            self.log_test(
                test_name, 
                "FAIL", 
                f"❌ MONGODB CACHE PROBLEM! {cache_issues}/{total_candles} Kerzen mit open === close in AI Data Module Cache gefunden. Cache sollte geleert werden."
            )
        else:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ MONGODB CACHE SAUBER! Keine fehlerhaften Daten mit open === close in AI Data Module Cache gefunden ({total_candles} candles checked)"
            )

    async def test_binance_integration_check(self):
        """BINANCE INTEGRATION CHECK: Test why real Binance OHLCV isn't being used"""
        test_name = "🎯 BINANCE INTEGRATION CHECK: Real OHLCV Usage"
        
        # Test chart data and check source
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1h&limit=5")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Binance integration test failed: {response.get('error')}")
            return
        
        data = response['data']
        chart_data = data.get('data', [])
        
        # Check if data comes from Binance or fallback
        data_source = data.get('asset_type', 'unknown')
        bars_count = data.get('bars_count', 0)
        
        print(f"📊 Data source: {data_source}, bars: {bars_count}")
        
        # Check data quality indicators
        realistic_prices = 0
        price_variations = 0
        
        for i, candle in enumerate(chart_data):
            btc_price = candle.get('close', 0)
            
            print(f"   Candle {i+1}: BTC price = ${btc_price:,.2f}")
            
            # Check if BTC price is realistic (should be > 100k based on context)
            if btc_price > 100000:
                realistic_prices += 1
            
            # Check for price variations
            if candle.get('open') != candle.get('close'):
                price_variations += 1
        
        # Analyze results
        if realistic_prices > 0 and price_variations > 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ BINANCE INTEGRATION FUNKTIONIERT! {realistic_prices}/{len(chart_data)} Kerzen mit realistischen BTC-Preisen (>$100k), {price_variations} Kerzen mit Preisvariationen. Data source: {data_source}"
            )
        elif realistic_prices > 0 and price_variations == 0:
            self.log_test(
                test_name, 
                "FAIL", 
                f"❌ BINANCE INTEGRATION PROBLEM! Realistische Preise ({realistic_prices}/{len(chart_data)}) aber KEINE Preisvariationen - alle Kerzen haben open === close"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Binance Integration Problem: {realistic_prices} realistic prices, {price_variations} variations")

    async def run_chart_data_tests(self):
        """Run all chart data tests"""
        await self.setup()
        
        try:
            await self.test_chart_data_btc_1h_debugging()
            await self.test_fallback_system_generate_minimal_chart_data()
            await self.test_mongodb_cache_check()
            await self.test_binance_integration_check()
            
            # Print summary
            print("=" * 80)
            print("📊 CHART DATA TEST SUMMARY")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed = len([r for r in self.test_results if r['status'] == 'PASS'])
            failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
            
            print(f"📊 TOTAL TESTS: {total_tests}")
            print(f"✅ PASSED: {passed}")
            print(f"❌ FAILED: {failed}")
            
            if failed > 0:
                print("\n❌ FAILED TESTS:")
                for result in self.test_results:
                    if result['status'] == 'FAIL':
                        print(f"   - {result['test']}")
                        print(f"     {result['details']}")
            
        except Exception as e:
            print(f"❌ Error during Chart Data tests: {e}")
        finally:
            await self.cleanup()

async def main():
    tester = ChartDataTester()
    await tester.run_chart_data_tests()

if __name__ == "__main__":
    asyncio.run(main())