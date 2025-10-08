#!/usr/bin/env python3
"""
CHART-DATEN REPARATUR TEST: Frontend Chart-Integration nach Binance-Fallback-System
Tests: Chart-Data Endpoints mit 3-stufigem Fallback-System (Binance → AI Data Module → Minimal Fallback)
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"

class ChartDataTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting CHART-DATEN REPARATUR TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        print("🎯 KRITISCHER CHART-DATA FIX: Binance → AI Data Module → Minimal Chart Data Generierung")
        print("=" * 80)
    
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

    def validate_ohlcv_data(self, candle: dict) -> bool:
        """Validate OHLCV candle data structure and logic"""
        # Chart-data API uses 'time' field instead of 'timestamp'
        required_fields = ['time', 'open', 'high', 'low', 'close', 'volume']
        
        # Check all required fields exist
        for field in required_fields:
            if field not in candle:
                return False
        
        try:
            timestamp = candle['time']
            open_price = float(candle['open'])
            high_price = float(candle['high'])
            low_price = float(candle['low'])
            close_price = float(candle['close'])
            volume = float(candle['volume'])
            
            # Validate OHLCV logic
            if high_price < max(open_price, close_price):
                return False  # High should be >= max(Open, Close)
            
            if low_price > min(open_price, close_price):
                return False  # Low should be <= min(Open, Close)
            
            if volume <= 0:
                return False  # Volume should be > 0
            
            if timestamp <= 0:
                return False  # Timestamp should be valid
            
            return True
            
        except (ValueError, TypeError):
            return False

    def is_realistic_price(self, symbol: str, price: float) -> bool:
        """Check if price is realistic for the given symbol"""
        realistic_ranges = {
            'BTC/USDT': (100000, 150000),  # BTC ~$122k as mentioned
            'BTC-USDT': (100000, 150000),
            'ETH/USDT': (3000, 6000),      # ETH ~$4.2k as mentioned  
            'ETH-USDT': (3000, 6000),
            'BNB/USDT': (500, 800),
            'BNB-USDT': (500, 800),
        }
        
        if symbol in realistic_ranges:
            min_price, max_price = realistic_ranges[symbol]
            return min_price <= price <= max_price
        
        return price > 0  # For other symbols, just check positive

    async def test_btc_chart_data_1h_100_candles(self):
        """TEST 1: GET /api/chart-data/BTC-USDT?timeframe=1h&limit=100"""
        test_name = "🎯 TEST 1: BTC CHART-DATA 1H (100 CANDLES)"
        
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1h&limit=100")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Chart-Data API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check response structure
        if 'data' not in data or 'bars_count' not in data:
            self.log_test(test_name, "FAIL", f"❌ Chart-Data Response structure invalid: {list(data.keys())}")
            return
        
        chart_data = data['data']
        bars_count = data['bars_count']
        symbol = data.get('symbol', 'Unknown')
        timeframe = data.get('timeframe', 'Unknown')
        
        # Validate minimum candles (should be at least 50 as per requirements)
        if bars_count < 50:
            self.log_test(test_name, "FAIL", f"❌ Insufficient candles returned: {bars_count} (expected ≥50)")
            return
        
        # Validate OHLCV structure for first few candles
        valid_candles = 0
        realistic_prices = 0
        source_info = "unknown"
        
        for i, candle in enumerate(chart_data[:10]):  # Check first 10 candles
            if self.validate_ohlcv_data(candle):
                valid_candles += 1
                
                # Check realistic BTC prices
                close_price = float(candle['close'])
                if self.is_realistic_price('BTC-USDT', close_price):
                    realistic_prices += 1
        
        # Check source information
        if len(chart_data) > 0 and 'source' in chart_data[0]:
            source_info = chart_data[0]['source']
        elif 'source' in data:
            source_info = data['source']
        
        if valid_candles >= 8 and realistic_prices >= 5:  # At least 80% valid, 50% realistic
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ BTC CHART-DATA 1H ERFOLGREICH! {bars_count} OHLCV-Bars erhalten, {valid_candles}/10 gültige Candles, {realistic_prices}/10 realistische Preise (~$122k), Source: {source_info}",
                "100 OHLCV-Bars mit korrekter timestamp/open/high/low/close/volume Struktur",
                f"{bars_count} bars, {valid_candles}/10 valid, {realistic_prices}/10 realistic, source: {source_info}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Chart-Data Qualität unzureichend: {valid_candles}/10 gültig, {realistic_prices}/10 realistisch")

    async def test_eth_chart_data_4h_200_candles(self):
        """TEST 2: GET /api/chart-data/ETH-USDT?timeframe=4h&limit=200"""
        test_name = "🎯 TEST 2: ETH CHART-DATA 4H (200 CANDLES)"
        
        response = await self.test_api_endpoint("/chart-data/ETH-USDT?timeframe=4h&limit=200")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ ETH Chart-Data API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'data' not in data or 'bars_count' not in data:
            self.log_test(test_name, "FAIL", f"❌ ETH Chart-Data Response structure invalid: {list(data.keys())}")
            return
        
        chart_data = data['data']
        bars_count = data['bars_count']
        symbol = data.get('symbol', 'Unknown')
        timeframe = data.get('timeframe', 'Unknown')
        
        # Validate minimum candles
        if bars_count < 50:
            self.log_test(test_name, "FAIL", f"❌ ETH: Insufficient candles returned: {bars_count} (expected ≥50)")
            return
        
        # Validate OHLCV structure
        valid_candles = 0
        realistic_prices = 0
        source_info = "unknown"
        
        for i, candle in enumerate(chart_data[:10]):
            if self.validate_ohlcv_data(candle):
                valid_candles += 1
                
                # Check realistic ETH prices (~$4.2k)
                close_price = float(candle['close'])
                if self.is_realistic_price('ETH-USDT', close_price):
                    realistic_prices += 1
        
        # Check source information
        if len(chart_data) > 0 and 'source' in chart_data[0]:
            source_info = chart_data[0]['source']
        elif 'source' in data:
            source_info = data['source']
        
        if valid_candles >= 8 and realistic_prices >= 5:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ ETH CHART-DATA 4H ERFOLGREICH! {bars_count} OHLCV-Bars erhalten, {valid_candles}/10 gültige Candles, {realistic_prices}/10 realistische Preise (~$4.2k), Source: {source_info}",
                "200 OHLCV-Bars mit korrekter Struktur für ETH",
                f"{bars_count} bars, {valid_candles}/10 valid, {realistic_prices}/10 realistic, source: {source_info}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ ETH Chart-Data Qualität unzureichend: {valid_candles}/10 gültig, {realistic_prices}/10 realistisch")

    async def test_various_timeframes(self):
        """TEST 3: Verschiedene Timeframes testen (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)"""
        test_name = "🎯 TEST 3: VERSCHIEDENE TIMEFRAMES"
        
        timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']
        successful_timeframes = []
        failed_timeframes = []
        
        for timeframe in timeframes:
            print(f"🔄 Testing timeframe: {timeframe}")
            
            response = await self.test_api_endpoint(f"/chart-data/BTC-USDT?timeframe={timeframe}&limit=50")
            
            if response['success']:
                data = response['data']
                if 'data' in data and 'bars_count' in data:
                    bars_count = data['bars_count']
                    if bars_count >= 10:  # At least 10 candles for each timeframe
                        successful_timeframes.append(f"{timeframe}({bars_count})")
                    else:
                        failed_timeframes.append(f"{timeframe}(only {bars_count})")
                else:
                    failed_timeframes.append(f"{timeframe}(invalid structure)")
            else:
                failed_timeframes.append(f"{timeframe}(API error)")
        
        success_rate = len(successful_timeframes) / len(timeframes) * 100
        
        if success_rate >= 75:  # At least 75% of timeframes should work
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ TIMEFRAMES ERFOLGREICH! {len(successful_timeframes)}/{len(timeframes)} Timeframes funktionieren ({success_rate:.1f}%): {', '.join(successful_timeframes)}",
                "Alle Timeframes (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M) sollten korrekte Daten liefern",
                f"{len(successful_timeframes)}/{len(timeframes)} working: {', '.join(successful_timeframes)}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Timeframes unzureichend: {len(successful_timeframes)}/{len(timeframes)} funktionieren. Fehlgeschlagen: {', '.join(failed_timeframes)}")

    async def test_ohlcv_data_validation(self):
        """TEST 4: OHLCV-Datenvalidierung (High >= max(Open, Close), Low <= min(Open, Close), Volume > 0)"""
        test_name = "🎯 TEST 4: OHLCV-DATENVALIDIERUNG"
        
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1h&limit=100")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Could not get chart data for validation: {response.get('error')}")
            return
        
        data = response['data']
        chart_data = data.get('data', [])
        
        if len(chart_data) < 10:
            self.log_test(test_name, "FAIL", f"❌ Insufficient data for validation: {len(chart_data)} candles")
            return
        
        validation_results = {
            'total_candles': len(chart_data),
            'valid_structure': 0,
            'valid_high_logic': 0,
            'valid_low_logic': 0,
            'valid_volume': 0,
            'valid_timestamp': 0,
            'realistic_prices': 0
        }
        
        for candle in chart_data:
            # Structure validation
            if self.validate_ohlcv_data(candle):
                validation_results['valid_structure'] += 1
                
                try:
                    open_price = float(candle['open'])
                    high_price = float(candle['high'])
                    low_price = float(candle['low'])
                    close_price = float(candle['close'])
                    volume = float(candle['volume'])
                    timestamp = candle['time']
                    
                    # High >= max(Open, Close)
                    if high_price >= max(open_price, close_price):
                        validation_results['valid_high_logic'] += 1
                    
                    # Low <= min(Open, Close)
                    if low_price <= min(open_price, close_price):
                        validation_results['valid_low_logic'] += 1
                    
                    # Volume > 0
                    if volume > 0:
                        validation_results['valid_volume'] += 1
                    
                    # Timestamp should be valid (Unix timestamp, could be seconds or milliseconds)
                    if timestamp > 1000000000:  # Valid Unix timestamp (after year 2001)
                        validation_results['valid_timestamp'] += 1
                    
                    # Realistic BTC prices
                    if self.is_realistic_price('BTC-USDT', close_price):
                        validation_results['realistic_prices'] += 1
                        
                except (ValueError, TypeError):
                    continue
        
        total = validation_results['total_candles']
        structure_rate = validation_results['valid_structure'] / total * 100
        high_rate = validation_results['valid_high_logic'] / total * 100
        low_rate = validation_results['valid_low_logic'] / total * 100
        volume_rate = validation_results['valid_volume'] / total * 100
        timestamp_rate = validation_results['valid_timestamp'] / total * 100
        price_rate = validation_results['realistic_prices'] / total * 100
        
        # Overall validation should be at least 90% for critical fields
        if (structure_rate >= 90 and high_rate >= 90 and low_rate >= 90 and 
            volume_rate >= 90 and timestamp_rate >= 90 and price_rate >= 70):
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ OHLCV-DATENVALIDIERUNG ERFOLGREICH! {total} Candles validiert: Struktur {structure_rate:.1f}%, High-Logic {high_rate:.1f}%, Low-Logic {low_rate:.1f}%, Volume {volume_rate:.1f}%, Timestamp {timestamp_rate:.1f}%, Realistische Preise {price_rate:.1f}%",
                "High >= max(Open, Close), Low <= min(Open, Close), Volume > 0, Timestamp in Millisekunden, Realistische Preise",
                f"Structure: {structure_rate:.1f}%, High: {high_rate:.1f}%, Low: {low_rate:.1f}%, Volume: {volume_rate:.1f}%, Timestamp: {timestamp_rate:.1f}%, Price: {price_rate:.1f}%"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ OHLCV-Validierung fehlgeschlagen: Struktur {structure_rate:.1f}%, High {high_rate:.1f}%, Low {low_rate:.1f}%, Volume {volume_rate:.1f}%, Timestamp {timestamp_rate:.1f}%, Preise {price_rate:.1f}%")

    async def test_fallback_system_verification(self):
        """TEST 5: 3-stufiges Fallback-System Verifikation (Binance → AI Data Module → Minimal Fallback)"""
        test_name = "🎯 TEST 5: FALLBACK-SYSTEM VERIFIKATION"
        
        # Test multiple symbols to see different fallback sources
        test_symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT']
        fallback_sources = {}
        
        for symbol in test_symbols:
            response = await self.test_api_endpoint(f"/chart-data/{symbol}?timeframe=1h&limit=50")
            
            if response['success']:
                data = response['data']
                chart_data = data.get('data', [])
                
                # Check source information
                source = "unknown"
                if len(chart_data) > 0 and 'source' in chart_data[0]:
                    source = chart_data[0]['source']
                elif 'source' in data:
                    source = data['source']
                
                fallback_sources[symbol] = {
                    'source': source,
                    'bars_count': data.get('bars_count', 0),
                    'success': True
                }
            else:
                fallback_sources[symbol] = {
                    'source': 'failed',
                    'bars_count': 0,
                    'success': False
                }
        
        # Analyze fallback system
        successful_symbols = sum(1 for info in fallback_sources.values() if info['success'])
        source_types = set(info['source'] for info in fallback_sources.values() if info['success'])
        
        # Check if we have evidence of fallback system working
        expected_sources = ['binance_spot', 'ai_data_module', 'minimal_fallback']
        fallback_evidence = any(source in expected_sources for source in source_types)
        
        if successful_symbols >= 2 and fallback_evidence:
            source_summary = ', '.join(f"{symbol}({info['source']})" for symbol, info in fallback_sources.items() if info['success'])
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ FALLBACK-SYSTEM FUNKTIONIERT! {successful_symbols}/{len(test_symbols)} Symbole erfolgreich, Quellen erkannt: {', '.join(source_types)}. Details: {source_summary}",
                "3-stufiges Fallback-System (Binance → AI Data Module → Minimal Fallback) sollte funktionieren",
                f"{successful_symbols}/{len(test_symbols)} symbols, sources: {', '.join(source_types)}"
            )
        else:
            failed_symbols = [symbol for symbol, info in fallback_sources.items() if not info['success']]
            self.log_test(test_name, "FAIL", f"❌ Fallback-System unzureichend: {successful_symbols}/{len(test_symbols)} erfolgreich, Quellen: {', '.join(source_types)}, Fehlgeschlagen: {failed_symbols}")

    async def test_response_status_and_structure(self):
        """TEST 6: Response Status und Struktur Validierung"""
        test_name = "🎯 TEST 6: RESPONSE STATUS UND STRUKTUR"
        
        response = await self.test_api_endpoint("/chart-data/BTC-USDT?timeframe=1h&limit=100")
        
        if response['status'] != 200:
            self.log_test(test_name, "FAIL", f"❌ Response Status nicht 200: {response['status']}")
            return
        
        data = response['data']
        
        # Check required response fields
        required_fields = ['symbol', 'timeframe', 'bars_count', 'data']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test(test_name, "FAIL", f"❌ Response Struktur unvollständig, fehlende Felder: {missing_fields}")
            return
        
        # Validate field values
        symbol = data['symbol']
        timeframe = data['timeframe']
        bars_count = data['bars_count']
        chart_data = data['data']
        
        # Check if data matches request
        if symbol != 'BTC/USDT' and symbol != 'BTC-USDT':
            self.log_test(test_name, "FAIL", f"❌ Symbol mismatch: expected BTC/USDT or BTC-USDT, got {symbol}")
            return
        
        if timeframe != '1h':
            self.log_test(test_name, "FAIL", f"❌ Timeframe mismatch: expected 1h, got {timeframe}")
            return
        
        if bars_count != len(chart_data):
            self.log_test(test_name, "FAIL", f"❌ Bars count mismatch: reported {bars_count}, actual {len(chart_data)}")
            return
        
        if bars_count < 50:
            self.log_test(test_name, "FAIL", f"❌ Insufficient bars: {bars_count} (expected ≥50)")
            return
        
        self.log_test(
            test_name, 
            "PASS", 
            f"✅ RESPONSE STATUS UND STRUKTUR KORREKT! Status: 200, Symbol: {symbol}, Timeframe: {timeframe}, Bars: {bars_count}, Datenstruktur vollständig",
            "200 Status, korrekte Felder (symbol, timeframe, bars_count, data), mindestens 50 Candles",
            f"Status: 200, Symbol: {symbol}, Timeframe: {timeframe}, Bars: {bars_count}"
        )

    async def run_all_tests(self):
        """Run all chart-data tests"""
        await self.setup()
        
        try:
            # Core chart-data tests as requested
            await self.test_btc_chart_data_1h_100_candles()
            await self.test_eth_chart_data_4h_200_candles()
            await self.test_various_timeframes()
            await self.test_ohlcv_data_validation()
            await self.test_fallback_system_verification()
            await self.test_response_status_and_structure()
            
            # Print summary
            print("\n" + "=" * 80)
            print("🎯 CHART-DATEN REPARATUR TEST ZUSAMMENFASSUNG")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
            failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
            warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
            
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"📊 GESAMT: {total_tests} Tests")
            print(f"✅ ERFOLGREICH: {passed_tests} Tests ({success_rate:.1f}%)")
            print(f"❌ FEHLGESCHLAGEN: {failed_tests} Tests")
            print(f"⚠️ WARNUNGEN: {warned_tests} Tests")
            print()
            
            if success_rate >= 80:
                print("🎉 CHART-DATEN REPARATUR ERFOLGREICH!")
                print("✅ Frontend Charts sollten jetzt funktionsfähig sein")
                print("✅ 3-stufiges Fallback-System (Binance → AI Data Module → Minimal Fallback) arbeitet")
            elif success_rate >= 60:
                print("⚠️ CHART-DATEN TEILWEISE REPARIERT")
                print("⚠️ Einige Chart-Funktionen könnten noch Probleme haben")
            else:
                print("❌ CHART-DATEN REPARATUR UNZUREICHEND")
                print("❌ Frontend Charts benötigen weitere Reparaturen")
            
            print("\n🔍 DETAILLIERTE ERGEBNISSE:")
            for result in self.test_results:
                status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
                print(f"{status_emoji} {result['test']}: {result['status']}")
                if result['details']:
                    print(f"   {result['details']}")
            
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = ChartDataTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())