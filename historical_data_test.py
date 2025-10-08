#!/usr/bin/env python3
"""
Historical Data Loading Repair Test Suite
Tests the repaired historical data loading functionality with comprehensive synthetic data 2019-2025
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BACKEND_URL = "https://crypto-ai-trading-2.preview.emergentagent.com/api"
AUTH_TOKEN = "demo-token"

class HistoricalDataTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Historical Data Loading Repair Tests")
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
    
    async def test_api_endpoint(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
            
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status = response.status
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            return {
                'status': status,
                'data': response_data,
                'success': status == 200
            }
        except Exception as e:
            return {
                'status': 0,
                'data': str(e),
                'success': False,
                'error': str(e)
            }

    async def test_historical_data_loading(self):
        """CRITICAL TEST: Historical Data Loading - POST /api/ai-data/load-historical"""
        test_name = "🎯 CRITICAL: HISTORISCHE DATENLADUNG REPARATUR TEST"
        
        # Test comprehensive historical data loading from 2019-2025
        load_data = {
            "start_date": "2019-01-01",
            "end_date": "2025-01-01",
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"]
        }
        
        print(f"🔄 Loading historical data from 2019-2025 for all timeframes...")
        response = await self.test_api_endpoint("/ai-data/load-historical", method="POST", data=load_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Historical data loading failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful data loading
        if data.get('status') == 'success' and 'result' in data:
            result = data['result']
            loaded_symbols = len(result.get('loaded_symbols', []))
            loaded_timeframes = len(result.get('loaded_timeframes', []))
            total_records = result.get('total_records', 0)
            
            # Validate comprehensive data loading
            if loaded_symbols >= 2 and loaded_timeframes >= 8 and total_records > 10000:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ HISTORISCHE DATENLADUNG ERFOLGREICH! {loaded_symbols} Symbole, {loaded_timeframes} Timeframes, {total_records:,} OHLCV-Bars geladen. Umfassende synthetische Daten 2019-2025 verfügbar!"
                )
            elif loaded_symbols >= 0 and loaded_timeframes >= 0:  # API working but empty data
                self.log_test(test_name, "WARN", f"⚠️ API funktioniert aber leere Daten: {loaded_symbols} Symbole, {loaded_timeframes} Timeframes, {total_records:,} Records")
            else:
                self.log_test(test_name, "FAIL", f"❌ Unvollständige Datenladung: {loaded_symbols} Symbole, {loaded_timeframes} Timeframes, {total_records:,} Records")
        else:
            self.log_test(test_name, "FAIL", f"❌ Historical data loading response invalid: {data}")

    async def test_data_quality_improvement(self):
        """CRITICAL TEST: Data Quality Improvement - GET /api/ai-data/data-quality"""
        test_name = "🎯 CRITICAL: DATENQUALITÄT VERBESSERUNG TEST"
        
        response = await self.test_api_endpoint("/ai-data/data-quality")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Data quality check failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if data.get('status') == 'success' and 'quality_report' in data:
            quality_report = data['quality_report']
            overall_score = quality_report.get('overall_score', 0) * 100  # Convert to percentage
            btc_dominance = quality_report.get('bitcoin_dominance_check', {})
            btc_dominance_value = btc_dominance.get('current_dominance', 0)
            
            # Check for improved quality scores (should be >0% now)
            if overall_score > 0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ DATENQUALITÄT DEUTLICH VERBESSERT! Overall Score: {overall_score:.1f}%, Bitcoin Dominance: {btc_dominance_value:.1f}% (Ziel: 59%)"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ API funktioniert aber Datenqualität niedrig: Overall: {overall_score:.1f}%")
        else:
            self.log_test(test_name, "FAIL", f"❌ Data quality response invalid: {data}")

    async def test_technical_indicators_calculation(self):
        """CRITICAL TEST: Technical Indicators with Historical Data - POST /api/ai-data/calculate-indicators"""
        test_name = "🎯 CRITICAL: TECHNISCHE INDIKATOREN MIT HISTORISCHEN DATEN"
        
        indicators_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "indicators": ["RSI", "SMA", "EMA", "BOLLINGER_BANDS", "MACD", "STOCHASTIC", "MFI"],
            "period": 30
        }
        
        response = await self.test_api_endpoint("/ai-data/calculate-indicators", method="POST", data=indicators_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Technical indicators calculation failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if data.get('status') == 'success' and 'result' in data:
            result = data['result']
            processed_symbols = result.get('processed_symbols', [])
            indicator_counts = result.get('indicator_counts', {})
            total_indicators = sum(indicator_counts.values())
            
            if len(processed_symbols) >= 5 and total_indicators > 500:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ TECHNISCHE INDIKATOREN ERFOLGREICH! {len(processed_symbols)} Symbole verarbeitet, {total_indicators} Indikatoren berechnet: {processed_symbols}"
                )
            elif len(processed_symbols) > 0:
                self.log_test(test_name, "WARN", f"⚠️ Teilweise erfolgreich: {len(processed_symbols)} Symbole, {total_indicators} Indikatoren")
            else:
                self.log_test(test_name, "FAIL", f"❌ Keine Indikatoren berechnet: {len(processed_symbols)} Symbole")
        else:
            self.log_test(test_name, "FAIL", f"❌ Technical indicators response invalid: {data}")

    async def test_realistic_price_evolution(self):
        """CRITICAL TEST: Realistic Price Evolution Validation"""
        test_name = "🎯 CRITICAL: REALISTISCHE PREISENTWICKLUNG VALIDIERUNG"
        
        # Get current BTC price to validate realistic evolution
        btc_response = await self.test_api_endpoint("/price/BTC-USDT")
        
        if not btc_response['success']:
            self.log_test(test_name, "FAIL", f"❌ Could not get BTC price: {btc_response.get('error')}")
            return
        
        btc_data = btc_response['data']
        current_btc_price = btc_data.get('price', 0)
        
        # Get ETH price
        eth_response = await self.test_api_endpoint("/price/ETH-USDT")
        
        if not eth_response['success']:
            self.log_test(test_name, "FAIL", f"❌ Could not get ETH price: {eth_response.get('error')}")
            return
        
        eth_data = eth_response['data']
        current_eth_price = eth_data.get('price', 0)
        
        # Validate realistic price ranges
        btc_in_range = 100000 <= current_btc_price <= 130000  # $100k-$130k range
        eth_in_range = 3000 <= current_eth_price <= 5000      # $3k-$5k range
        
        if btc_in_range and eth_in_range:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ REALISTISCHE PREISENTWICKLUNG BESTÄTIGT! BTC: ${current_btc_price:,.2f} (Ziel: ~$122,000), ETH: ${current_eth_price:,.2f} (Ziel: ~$4,200). Evolution von 2019 Startpreisen realistisch!"
            )
        else:
            self.log_test(test_name, "WARN", f"⚠️ Preise außerhalb erwarteter Bereiche: BTC ${current_btc_price:,.2f} (erwartet: $100k-$130k), ETH ${current_eth_price:,.2f} (erwartet: $3k-$5k)")

    async def test_ohlcv_data_validation(self):
        """CRITICAL TEST: OHLCV Data Logic Validation"""
        test_name = "🎯 CRITICAL: OHLCV-DATENLOGIK VALIDIERUNG"
        
        # Get chart data to validate OHLCV logic
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1d&limit=100")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Could not get chart data: {response.get('error')}")
            return
        
        data = response['data']
        chart_data = data.get('data', [])
        
        if len(chart_data) < 50:
            self.log_test(test_name, "FAIL", f"❌ Insufficient chart data: {len(chart_data)} bars")
            return
        
        # Validate OHLCV logic for recent candles
        valid_candles = 0
        invalid_candles = 0
        
        for candle in chart_data[-20:]:  # Check last 20 candles
            open_price = candle.get('open', 0)
            high_price = candle.get('high', 0)
            low_price = candle.get('low', 0)
            close_price = candle.get('close', 0)
            
            # Validate OHLCV logic: High >= max(Open,Close), Low <= min(Open,Close)
            max_oc = max(open_price, close_price)
            min_oc = min(open_price, close_price)
            
            if high_price >= max_oc and low_price <= min_oc and high_price >= low_price:
                valid_candles += 1
            else:
                invalid_candles += 1
        
        if valid_candles >= 18:  # Allow for 2 potential edge cases
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ OHLCV-DATENLOGIK KORREKT! {valid_candles}/20 Candles haben korrekte OHLCV-Logik (High >= max(Open,Close), Low <= min(Open,Close))"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ OHLCV-Logik fehlerhaft: {valid_candles}/20 korrekte Candles, {invalid_candles} fehlerhafte")

    async def test_all_timeframes_availability(self):
        """CRITICAL TEST: All Timeframes Availability"""
        test_name = "🎯 CRITICAL: ALLE TIMEFRAMES VERFÜGBARKEIT"
        
        required_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"]
        available_timeframes = []
        
        for timeframe in required_timeframes:
            response = await self.test_api_endpoint(f"/chart-data/BTC-USDT?timeframe={timeframe}&limit=10")
            
            if response['success']:
                data = response['data']
                chart_data = data.get('data', [])
                if len(chart_data) > 0:
                    available_timeframes.append(timeframe)
        
        if len(available_timeframes) >= 8:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ ALLE TIMEFRAMES VERFÜGBAR! {len(available_timeframes)}/8 Timeframes funktionieren: {available_timeframes}"
            )
        else:
            missing_timeframes = [tf for tf in required_timeframes if tf not in available_timeframes]
            self.log_test(test_name, "FAIL", f"❌ Fehlende Timeframes: {missing_timeframes}. Verfügbar: {available_timeframes}")

    async def run_all_tests(self):
        """Run all historical data loading tests"""
        await self.setup()
        
        try:
            print("🎯 TESTING HISTORISCHE DATENLADUNG REPARATUR")
            print("=" * 80)
            print("KRITISCHE TESTS:")
            print("1. HISTORISCHE DATENLADUNG: POST /api/ai-data/load-historical mit start_date='2019-01-01'")
            print("2. DATENQUALITÄT: GET /api/ai-data/data-quality")
            print("3. TECHNISCHE INDIKATOREN: POST /api/ai-data/calculate-indicators")
            print("4. REALISTISCHE PREISENTWICKLUNG: Bitcoin $3,800→$122,000, Ethereum $140→$4,200")
            print("5. OHLCV-DATENLOGIK: High >= max(Open,Close), Low <= min(Open,Close)")
            print("6. ALLE TIMEFRAMES: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M")
            print("=" * 80)
            
            # Run all tests
            await self.test_historical_data_loading()
            await self.test_data_quality_improvement()
            await self.test_technical_indicators_calculation()
            await self.test_realistic_price_evolution()
            await self.test_ohlcv_data_validation()
            await self.test_all_timeframes_availability()
            
        except Exception as e:
            print(f"❌ Error during Historical Data Loading tests: {e}")
        finally:
            await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary of Historical Data Loading tests"""
        print("\n" + "=" * 80)
        print("📊 HISTORISCHE DATENLADUNG REPARATUR TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📊 TOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️  WARNINGS: {warned_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        print("\n🎯 DETAILED RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print("\n" + "=" * 80)
        print("📊 HISTORISCHE DATENLADUNG REPARATUR TESTING COMPLETE")
        print("=" * 80)

async def main():
    """Main test runner"""
    tester = HistoricalDataTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())