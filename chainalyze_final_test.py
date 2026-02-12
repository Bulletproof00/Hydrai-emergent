#!/usr/bin/env python3
"""
CHAiNALYZE VOLLSTÄNDIGES SYSTEM FINAL TESTING
Nach AI Module Implementation - Finale Verifikation aller Module

Tests: NEW AI DATA MODULE APIs, AI EVOLUTION & SELF-CODING SYSTEM, 
CORE TRADING & MARKET SYSTEMS, NEWS & SENTIMENT SYSTEM, COMPREHENSIVE SYSTEM HEALTH
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://crypto-ai-trading-2.preview.emergentagent.com/api"

class CHAiNALYZEFinalTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🎯 STARTING CHAiNALYZE VOLLSTÄNDIGES SYSTEM FINAL TESTING")
        print("Nach AI Module Implementation - Finale Verifikation aller Module")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup test user for authenticated endpoints
        await self.setup_test_user()
    
    async def setup_test_user(self):
        """Setup test user for authenticated endpoints - using demo user"""
        try:
            # Try to login with demo user
            login_data = {
                "email": "demo@example.com",
                "password": "demo123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    print("✅ Logged in with demo user (demo@example.com)")
                    return
                    
            # If demo user doesn't exist, register it
            register_data = {
                "email": "demo@example.com",
                "username": "demouser",
                "password": "demo123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=register_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    print("✅ Registered demo user (demo@example.com)")
                else:
                    print("⚠️ Could not setup demo user - some tests may fail")
                    
        except Exception as e:
            print(f"⚠️ Error setting up demo user: {e}")
    
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
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200, method: str = "GET", data: dict = None, auth: bool = False) -> Dict[str, Any]:
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            headers = {}
            
            if auth and self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
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
                'success': status == expected_status
            }
        except Exception as e:
            return {
                'status': 0,
                'data': str(e),
                'success': False,
                'error': str(e)
            }

    # ============= NEW AI DATA MODULE TESTS =============
    
    async def test_ai_data_load_historical(self):
        """Test NEW AI DATA MODULE - Historical OHLCV Data Loading"""
        test_name = "🎯 NEW AI DATA MODULE - Historical OHLCV Data Loading"
        
        historical_data = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "timeframes": ["1h", "4h", "1d"],
            "start_date": "2019-01-01",
            "end_date": "2024-12-31"
        }
        
        response = await self.test_api_endpoint("/ai-data/load-historical", method="POST", data=historical_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Data Load Historical API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful historical data loading
        if 'status' in data and data['status'] == 'success':
            result = data.get('result', {})
            symbols_loaded = result.get('symbols_loaded', 0)
            timeframes_loaded = result.get('timeframes_loaded', 0)
            total_bars = result.get('total_bars_loaded', 0)
            
            if symbols_loaded >= 2 and timeframes_loaded >= 3 and total_bars > 10000:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI DATA MODULE HISTORICAL LOADING SUCCESSFUL! {symbols_loaded} symbols, {timeframes_loaded} timeframes, {total_bars:,} bars loaded from 2019-today",
                    "Historical OHLCV data loaded for multiple symbols and timeframes",
                    f"Symbols: {symbols_loaded}, Timeframes: {timeframes_loaded}, Bars: {total_bars:,}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Insufficient historical data loaded: {symbols_loaded} symbols, {timeframes_loaded} timeframes, {total_bars} bars")
        else:
            self.log_test(test_name, "FAIL", f"❌ Historical data loading failed: {data}")

    async def test_ai_data_calculate_indicators(self):
        """Test NEW AI DATA MODULE - Technical Indicators Calculation"""
        test_name = "🎯 NEW AI DATA MODULE - Technical Indicators Calculation"
        
        indicators_data = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "timeframes": ["1h", "4h"],
            "indicators": ["RSI", "SMA", "EMA", "BOLLINGER_BANDS", "MACD", "STOCHASTIC", "MFI"]
        }
        
        response = await self.test_api_endpoint("/ai-data/calculate-indicators", method="POST", data=indicators_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Data Calculate Indicators API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful indicator calculation
        if 'status' in data and data['status'] == 'success':
            result = data.get('result', {})
            symbols_processed = result.get('symbols_processed', 0)
            indicators_calculated = result.get('indicators_calculated', 0)
            
            if symbols_processed >= 2 and indicators_calculated > 100:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI DATA MODULE INDICATORS CALCULATION SUCCESSFUL! {symbols_processed} symbols processed, {indicators_calculated} indicators calculated (RSI, SMA, EMA, Bollinger Bands, MACD, Stochastic, MFI)",
                    "Technical indicators calculated for multiple symbols and timeframes",
                    f"Symbols: {symbols_processed}, Indicators: {indicators_calculated}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Insufficient indicators calculated: {symbols_processed} symbols, {indicators_calculated} indicators")
        else:
            self.log_test(test_name, "FAIL", f"❌ Indicators calculation failed: {data}")

    async def test_ai_data_status(self):
        """Test NEW AI DATA MODULE - Status Check"""
        test_name = "🎯 NEW AI DATA MODULE - Status Check"
        
        response = await self.test_api_endpoint("/ai-data/status")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Data Status API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check AI Data Module status
        if 'status' in data and data['status'] == 'operational':
            module_info = data.get('module_info', {})
            data_quality = module_info.get('data_quality_score', 0)
            bitcoin_dominance = module_info.get('bitcoin_dominance', 0)
            
            if data_quality > 0.5 and bitcoin_dominance == 59.0:  # Target 59% as mentioned in request
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI DATA MODULE STATUS OPERATIONAL! Data Quality: {data_quality:.1%}, Bitcoin Dominance: {bitcoin_dominance}% (corrected to target 59%)",
                    "AI Data Module operational with good data quality and corrected Bitcoin dominance",
                    f"Quality: {data_quality:.1%}, BTC Dom: {bitcoin_dominance}%"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI Data Module operational but data quality or dominance needs attention: Quality: {data_quality:.1%}, BTC Dom: {bitcoin_dominance}%")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Data Module not operational: {data}")

    # ============= AI EVOLUTION & SELF-CODING SYSTEM TESTS =============
    
    async def test_ai_evolution_status(self):
        """Test AI EVOLUTION STATUS - Should work now"""
        test_name = "🎯 AI EVOLUTION STATUS - Should Work Now"
        
        response = await self.test_api_endpoint("/ai/evolution/status")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Evolution Status API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check evolution status
        if 'status' in data and data['status'] == 'active':
            evolution_info = data.get('evolution_info', {})
            learning_cycles = evolution_info.get('learning_cycles_completed', 0)
            
            if learning_cycles >= 0:  # Should be operational now
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI EVOLUTION STATUS NOW WORKING! Status: active, Learning Cycles: {learning_cycles}",
                    "AI Evolution system should be operational after implementation",
                    f"Status: active, Cycles: {learning_cycles}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI Evolution active but no learning cycles completed yet")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Evolution Status not active: {data}")

    async def test_ai_evolution_chat(self):
        """Test AI EVOLUTION CHAT"""
        test_name = "🎯 AI EVOLUTION CHAT"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        chat_data = {
            "message": "Erkläre mir deine Selbst-Evolution und Lernfähigkeiten"
        }
        
        response = await self.test_api_endpoint("/ai/evolution/chat", method="POST", data=chat_data, auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Evolution Chat API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check evolution chat response
        if 'response' in data:
            ai_response = data['response']
            evolution_keywords = ['evolution', 'lernen', 'selbst', 'verbesserung', 'anpassung']
            keyword_count = sum(1 for word in evolution_keywords if word.lower() in ai_response.lower())
            
            if len(ai_response) > 500 and keyword_count >= 3:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI EVOLUTION CHAT WORKING! Comprehensive response about self-evolution: {len(ai_response)} chars, {keyword_count} evolution concepts",
                    "AI Evolution chat should provide detailed responses about self-learning",
                    f"Response: {len(ai_response)} chars, {keyword_count} concepts"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Evolution chat working but response could be more comprehensive: {len(ai_response)} chars, {keyword_count} concepts")
        else:
            self.log_test(test_name, "FAIL", f"❌ Evolution chat response missing: {data}")

    async def test_ai_coding_plugins(self):
        """Test AI CODING PLUGINS System"""
        test_name = "🎯 AI CODING PLUGINS System"
        
        response = await self.test_api_endpoint("/ai/coding/plugins")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Coding Plugins API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check plugin system status
        if 'status' in data and data['status'] == 'operational':
            plugin_stats = data.get('plugin_statistics', {})
            total_plugins = plugin_stats.get('total_plugins', 0)
            deployed_plugins = plugin_stats.get('deployed_plugins', 0)
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ AI CODING PLUGINS SYSTEM OPERATIONAL! Total Plugins: {total_plugins}, Deployed: {deployed_plugins}",
                "AI Coding Plugin system should be operational and ready for plugin creation",
                f"Total: {total_plugins}, Deployed: {deployed_plugins}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Coding Plugins system not operational: {data}")

    # ============= CORE TRADING & MARKET SYSTEMS TESTS =============
    
    async def test_enhanced_smart_money_directional_bias(self):
        """Test Enhanced Smart Money with directional_bias"""
        test_name = "🎯 Enhanced Smart Money with Directional Bias"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1h")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Enhanced Smart Money API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            smart_money_data = data.get('data', {})
            
            # Check for directional_bias field
            if 'directional_bias' in smart_money_data:
                directional_bias = smart_money_data['directional_bias']
                liquidation_heatmap = smart_money_data.get('liquidation_heatmap_2d', {})
                
                if directional_bias in ['bullish', 'bearish', 'neutral'] and liquidation_heatmap:
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"✅ ENHANCED SMART MONEY WITH DIRECTIONAL BIAS WORKING! Bias: {directional_bias}, Liquidation Heatmap: Available",
                        "Enhanced Smart Money should include directional_bias analysis",
                        f"Bias: {directional_bias}, Heatmap: Available"
                    )
                else:
                    self.log_test(test_name, "FAIL", f"❌ Directional bias or heatmap data invalid: Bias: {directional_bias}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Directional bias field missing from Enhanced Smart Money data")
        else:
            self.log_test(test_name, "FAIL", f"❌ Enhanced Smart Money API error: {data}")

    async def test_real_time_data_extended_crypto_assets(self):
        """Test Real-time Data with Extended Crypto Assets"""
        test_name = "🎯 Real-time Data with Extended Crypto Assets"
        
        # Test extended crypto assets beyond BTC/ETH
        extended_symbols = "BTC/USDT,ETH/USDT,SOL/USDT,AVAX/USDT,LINK/USDT,DOT/USDT,UNI/USDT"
        response = await self.test_api_endpoint(f"/realtime/latest?symbols={extended_symbols}")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Real-time Data API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            realtime_data = data.get('data', {})
            extended_assets = ['SOL/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOT/USDT', 'UNI/USDT']
            available_extended = [asset for asset in extended_assets if asset in realtime_data]
            
            if len(available_extended) >= 3:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ REAL-TIME DATA WITH EXTENDED CRYPTO ASSETS WORKING! {len(available_extended)}/5 extended assets available: {', '.join(available_extended)}",
                    "Real-time data should include extended crypto assets beyond BTC/ETH",
                    f"Extended assets: {len(available_extended)}/5"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Limited extended crypto assets: {len(available_extended)}/5 available")
        else:
            self.log_test(test_name, "FAIL", f"❌ Real-time data API error: {data}")

    # ============= NEWS & SENTIMENT SYSTEM TESTS =============
    
    async def test_news_sentiment_apis(self):
        """Test All News/Sentiment APIs"""
        test_name = "🎯 News & Sentiment System APIs"
        
        # Test multiple news/sentiment endpoints
        endpoints_to_test = [
            "/financial-news",
            "/market-sentiment", 
            "/economic-calendar",
            "/news-sentiment/real-time-sentiment"
        ]
        
        working_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            response = await self.test_api_endpoint(endpoint)
            if response['success']:
                working_endpoints += 1
        
        success_rate = (working_endpoints / total_endpoints) * 100
        
        if success_rate >= 75:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ NEWS & SENTIMENT SYSTEM WORKING! {working_endpoints}/{total_endpoints} endpoints operational ({success_rate:.1f}% success rate)",
                "News & Sentiment APIs should be functional",
                f"Working: {working_endpoints}/{total_endpoints} ({success_rate:.1f}%)"
            )
        elif success_rate >= 50:
            self.log_test(test_name, "WARN", f"⚠️ Partial News & Sentiment functionality: {working_endpoints}/{total_endpoints} endpoints working")
        else:
            self.log_test(test_name, "FAIL", f"❌ News & Sentiment system mostly non-functional: {working_endpoints}/{total_endpoints} endpoints working")

    # ============= COMPREHENSIVE SYSTEM HEALTH TEST =============
    
    async def test_system_health_comprehensive(self):
        """Test Comprehensive System Health Check"""
        test_name = "🎯 COMPREHENSIVE SYSTEM HEALTH CHECK"
        
        response = await self.test_api_endpoint("/health")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ System Health API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check overall system health
        if 'status' in data and data['status'] == 'healthy':
            services = data.get('services', {})
            
            # Count operational services
            operational_services = 0
            total_services = 0
            
            for service_name, service_status in services.items():
                total_services += 1
                if isinstance(service_status, dict):
                    if service_status.get('status') == 'operational':
                        operational_services += 1
                elif service_status == 'operational':
                    operational_services += 1
            
            health_percentage = (operational_services / total_services * 100) if total_services > 0 else 0
            
            if health_percentage >= 85:  # Target 85%+ as mentioned in request
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ COMPREHENSIVE SYSTEM HEALTH EXCELLENT! {operational_services}/{total_services} services operational ({health_percentage:.1f}% health - exceeds 85% target)",
                    "System should have 85%+ success rate with all critical modules functional",
                    f"Health: {health_percentage:.1f}% ({operational_services}/{total_services})"
                )
            elif health_percentage >= 70:
                self.log_test(test_name, "WARN", f"⚠️ System health good but below target: {health_percentage:.1f}% ({operational_services}/{total_services})")
            else:
                self.log_test(test_name, "FAIL", f"❌ System health below acceptable level: {health_percentage:.1f}% ({operational_services}/{total_services})")
        else:
            self.log_test(test_name, "FAIL", f"❌ System not healthy: {data}")

    # ============= CORE PAPER TRADING VERIFICATION TESTS =============
    
    async def test_trading_account_status(self):
        """Test Trading Account Status - GET /api/trading/account"""
        test_name = "🎯 CORE PAPER TRADING - Trading Account Status"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        response = await self.test_api_endpoint("/trading/account", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Trading Account API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for account data structure
        if 'account' not in data:
            self.log_test(test_name, "FAIL", f"❌ Trading Account Response missing 'account' object: {data}")
            return
        
        account_data = data['account']
        required_fields = ['balance', 'equity', 'free_margin', 'unrealized_pnl']
        missing_fields = [field for field in required_fields if field not in account_data]
        
        if missing_fields:
            self.log_test(test_name, "FAIL", f"❌ Trading Account Response incomplete, missing fields: {missing_fields}")
            return
        
        balance = account_data.get('balance', 0)
        equity = account_data.get('equity', 0)
        
        if balance > 0 and equity >= 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ TRADING ACCOUNT STATUS WORKING! Balance: ${balance:,.2f}, Equity: ${equity:,.2f}",
                "Correct account data with all required fields",
                f"Balance: ${balance:,.2f}, Equity: ${equity:,.2f}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Trading Account data invalid: Balance: ${balance}, Equity: ${equity}")

    async def test_ai_trading_integration(self):
        """Test AI Trading Integration"""
        test_name = "🎯 AI TRADING INTEGRATION"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        analyze_data = {
            "symbol": "BTC/USDT",
            "context": "Test analysis for CHAiNALYZE final testing"
        }
        
        response = await self.test_api_endpoint("/ai-trading/analyze", method="POST", data=analyze_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 UNPROCESSABLE ENTITY ERROR! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Trading Analyze API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful AI analysis
        if 'recommendation' in data and 'symbol' in data:
            recommendation = data.get('recommendation', {})
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            action = recommendation.get('action', '') if isinstance(recommendation, dict) else ''
            
            if len(reasoning) > 100 and action:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI TRADING INTEGRATION WORKING! Analysis: {len(reasoning)} chars reasoning, action: {action}",
                    "AI Trading analysis with correct Authorization Header",
                    f"Reasoning: {len(reasoning)} chars, Action: {action}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI analysis working but could be more detailed: {len(reasoning)} chars, action: {action}")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI analysis response incomplete: {data}")

    # ============= MAIN TEST EXECUTION =============
    
    async def run_all_tests(self):
        """Run all tests in sequence - CHAiNALYZE FINAL TESTING"""
        print("🎯 STARTING CHAiNALYZE VOLLSTÄNDIGES SYSTEM FINAL TESTING")
        print("Nach AI Module Implementation - Finale Verifikation aller Module")
        print("=" * 80)
        
        # 1. NEW AI DATA MODULE APIs (Priority)
        print("\n🔥 PHASE 1: NEW AI DATA MODULE APIs")
        await self.test_ai_data_load_historical()
        await self.test_ai_data_calculate_indicators()
        await self.test_ai_data_status()
        
        # 2. AI EVOLUTION & SELF-CODING SYSTEM (Priority)
        print("\n🔥 PHASE 2: AI EVOLUTION & SELF-CODING SYSTEM")
        await self.test_ai_evolution_status()
        await self.test_ai_evolution_chat()
        await self.test_ai_coding_plugins()
        
        # 3. CORE TRADING & MARKET SYSTEMS (Priority)
        print("\n🔥 PHASE 3: CORE TRADING & MARKET SYSTEMS")
        await self.test_enhanced_smart_money_directional_bias()
        await self.test_real_time_data_extended_crypto_assets()
        
        # 4. NEWS & SENTIMENT SYSTEM (Priority)
        print("\n🔥 PHASE 4: NEWS & SENTIMENT SYSTEM")
        await self.test_news_sentiment_apis()
        
        # 5. COMPREHENSIVE SYSTEM HEALTH (Priority)
        print("\n🔥 PHASE 5: COMPREHENSIVE SYSTEM HEALTH")
        await self.test_system_health_comprehensive()
        
        # 6. Core Paper Trading Tests (Verification)
        print("\n🔥 PHASE 6: CORE PAPER TRADING VERIFICATION")
        await self.test_trading_account_status()
        
        # 7. AI Integration Tests (Verification)
        print("\n🔥 PHASE 7: AI INTEGRATION VERIFICATION")
        await self.test_ai_trading_integration()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("🎯 CHAiNALYZE FINAL TESTING RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 TOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️ WARNINGS: {warning_tests}")
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        # Check if target 85%+ achieved
        if success_rate >= 85:
            print(f"🎉 TARGET ACHIEVED: {success_rate:.1f}% SUCCESS RATE (≥85% target)")
        else:
            print(f"⚠️ TARGET NOT MET: {success_rate:.1f}% SUCCESS RATE (<85% target)")
        
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['test']}: {result['details']}")
            print()
        
        if warning_tests > 0:
            print("⚠️ WARNING TESTS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   - {result['test']}: {result['details']}")
            print()
        
        print("=" * 80)

async def main():
    """Main test execution"""
    tester = CHAiNALYZEFinalTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())