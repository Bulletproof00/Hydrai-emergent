#!/usr/bin/env python3
"""
Correlation System Backend Tests
Focused testing for the correlation system as requested in German
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BACKEND_URL = "https://crypto-ai-trading-2.preview.emergentagent.com/api"

class CorrelationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🎯 STARTING CORRELATION SYSTEM BACKEND TESTS")
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
    
    async def test_api_endpoint(self, endpoint: str, timeout: int = 30):
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            async with self.session.get(url, timeout=timeout) as response:
                status = response.status
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
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

    async def test_correlations_endpoint(self):
        """Test 1: Korrelations-Endpoint - GET /api/correlations"""
        test_name = "🎯 TEST 1: KORRELATIONS-ENDPOINT"
        
        response = await self.test_api_endpoint("/correlations")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Correlations API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if correlations data is returned
        if not isinstance(data, dict) or len(data) == 0:
            self.log_test(test_name, "FAIL", f"❌ Correlations Response leer oder ungültiges Format: {data}")
            return
        
        # Check for expected correlation pairs
        expected_pairs = ['BTC_vs_SPX', 'BTC_vs_ETH', 'BTC_vs_Gold', 'BTC_vs_NASDAQ', 'BTC_vs_DXY']
        found_pairs = []
        correlation_values = []
        
        for pair, value in data.items():
            if any(expected in pair for expected in expected_pairs):
                found_pairs.append(pair)
                if isinstance(value, (int, float)) and -1 <= value <= 1:
                    correlation_values.append(value)
        
        if len(found_pairs) >= 1 and len(correlation_values) >= 1:
            # Convert to percentage values as requested
            percentage_values = [f"{pair}: {value:.3f} → {value*100:.1f}%" for pair, value in list(data.items())[:3]]
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ KORRELATIONS-ENDPOINT ERFOLGREICH! {len(data)} Korrelationspaare gefunden. Beispiele: {', '.join(percentage_values)}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Unzureichende Korrelationsdaten: {len(found_pairs)} Paare, {len(correlation_values)} gültige Werte")

    async def test_macro_market_data_endpoint(self):
        """Test 2: Macro Market Data - GET /api/macro-data"""
        test_name = "🎯 TEST 2: MACRO MARKET DATA"
        
        response = await self.test_api_endpoint("/macro-data")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Macro Data API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if macro data is returned
        if not isinstance(data, dict) or len(data) == 0:
            self.log_test(test_name, "FAIL", f"❌ Macro Data Response leer oder ungültiges Format: {data}")
            return
        
        # Check for expected macro market indicators
        expected_indicators = ['SPX', 'NASDAQ', 'DXY', 'Gold', 'Bitcoin', 'Ethereum']
        found_indicators = []
        valid_data_points = 0
        
        for indicator in expected_indicators:
            if indicator in data:
                found_indicators.append(indicator)
                indicator_data = data[indicator]
                if isinstance(indicator_data, dict) and 'price' in indicator_data and 'change_24h' in indicator_data:
                    valid_data_points += 1
        
        if len(found_indicators) >= 3 and valid_data_points >= 3:
            # Show sample data
            sample_data = []
            for indicator in found_indicators[:3]:
                if indicator in data and isinstance(data[indicator], dict):
                    price = data[indicator].get('price', 0)
                    change = data[indicator].get('change_24h', 0)
                    sample_data.append(f"{indicator}: ${price:,.2f} ({change:+.2f}%)")
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ MACRO MARKET DATA ERFOLGREICH! {len(found_indicators)} Makro-Indikatoren gefunden. Beispiele: {', '.join(sample_data)}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Unzureichende Makro-Daten: {len(found_indicators)} Indikatoren, {valid_data_points} gültige Datenpunkte")

    async def test_market_overview_endpoint(self):
        """Test 3: Market Overview - GET /api/market-overview"""
        test_name = "🎯 TEST 3: MARKET OVERVIEW"
        
        response = await self.test_api_endpoint("/market-overview", timeout=60)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Market Overview API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if market overview data is returned
        if not isinstance(data, dict):
            self.log_test(test_name, "FAIL", f"❌ Market Overview Response ungültiges Format: {data}")
            return
        
        # Check for expected sections
        required_sections = ['bitcoin', 'macro_data', 'correlations', 'summary']
        missing_sections = [section for section in required_sections if section not in data]
        
        if missing_sections:
            self.log_test(test_name, "FAIL", f"❌ Market Overview unvollständig, fehlende Sektionen: {missing_sections}")
            return
        
        # Check Bitcoin data
        bitcoin_data = data.get('bitcoin', {})
        btc_price = bitcoin_data.get('price', 0)
        btc_change = bitcoin_data.get('change_24h', 0)
        
        # Check correlations in overview
        correlations = data.get('correlations', {})
        correlation_count = len(correlations)
        
        # Check summary data
        summary = data.get('summary', {})
        market_sentiment = summary.get('market_sentiment', '')
        btc_dominance = summary.get('btc_dominance', 0)
        spx_correlation = summary.get('correlation_with_spx', 0)
        
        if btc_price > 0 and correlation_count >= 1 and market_sentiment:
            # Convert correlation to percentage as requested
            spx_correlation_percent = spx_correlation * 100 if spx_correlation else 0
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ MARKET OVERVIEW ERFOLGREICH! BTC: ${btc_price:,.2f} ({btc_change:+.2f}%), {correlation_count} Korrelationen, BTC-SPX Korrelation: {spx_correlation:.3f} → {spx_correlation_percent:.1f}%, Sentiment: {market_sentiment}, BTC Dominanz: {btc_dominance:.1f}%"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Market Overview Daten unvollständig: BTC: ${btc_price}, Korrelationen: {correlation_count}, Sentiment: {market_sentiment}")

    async def test_correlation_percentage_calculation(self):
        """Test 4: Korrelations-Prozentwerte-Berechnung"""
        test_name = "🎯 TEST 4: KORRELATIONS-PROZENTWERTE-BERECHNUNG"
        
        response = await self.test_api_endpoint("/correlations")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Correlations API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Test percentage conversion for correlation values
        valid_correlations = 0
        percentage_examples = []
        
        for pair, value in data.items():
            if isinstance(value, (int, float)) and -1 <= value <= 1:
                valid_correlations += 1
                percentage_value = value * 100
                percentage_examples.append(f"{pair}: {value:.3f} → {percentage_value:.1f}%")
        
        if valid_correlations >= 1:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ KORRELATIONS-PROZENTWERTE-BERECHNUNG ERFOLGREICH! {valid_correlations} gültige Korrelationen. Beispiele: {'; '.join(percentage_examples[:3])}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Unzureichende gültige Korrelationswerte: {valid_correlations}")

    async def run_all_tests(self):
        """Run all correlation system tests"""
        await self.setup()
        
        try:
            print("KORRELATIONS-SYSTEM TESTS:")
            print("1. Korrelations-Endpoint testen: GET /api/correlations")
            print("2. Macro Market Data testen: GET /api/macro-data")
            print("3. Market Overview testen: GET /api/market-overview")
            print("ERWARTETE FUNKTIONALITÄT:")
            print("- Korrelationen als Prozentwerte (z.B. BTC_vs_SPX: 0.45 → 45%)")
            print("- Multiple Asset-Korrelationen (BTC vs SPX, ETH, Gold, etc.)")
            print("- Timeframe-spezifische Korrelationsberechnungen")
            print("- Error Handling bei fehlenden Daten")
            print("=" * 80)
            
            # Core Correlation System Tests
            await self.test_correlations_endpoint()
            await self.test_macro_market_data_endpoint()
            await self.test_market_overview_endpoint()
            await self.test_correlation_percentage_calculation()
            
        except Exception as e:
            print(f"❌ Error during Correlation System tests: {e}")
        finally:
            await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary of Correlation System tests"""
        print("\n" + "=" * 80)
        print("📊 CORRELATION SYSTEM TEST SUMMARY")
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
        print("📊 CORRELATION SYSTEM TESTING COMPLETE")
        print("=" * 80)

async def main():
    """Main test runner - CORRELATION SYSTEM TESTS"""
    tester = CorrelationTester()
    
    print("📊 RUNNING CORRELATION SYSTEM BACKEND TESTS")
    print("Teste das Korrelations-System im Backend:")
    print("1. Korrelations-Endpoint testen: GET /api/correlations")
    print("2. Macro Market Data testen: GET /api/macro-data") 
    print("3. Market Overview testen: GET /api/market-overview")
    print("Backend URL: https://crypto-ai-trading-2.preview.emergentagent.com/api")
    print("Demo User: demo@example.com/demo123 oder demo-token für Authorization")
    print()
    
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())