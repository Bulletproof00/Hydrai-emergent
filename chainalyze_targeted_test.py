#!/usr/bin/env python3
"""
CHAiNALYZE TARGETED SYSTEM TESTING
Testing available endpoints based on actual implementation
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

class CHAiNALYZETargetedTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🎯 CHAiNALYZE TARGETED SYSTEM TESTING")
        print("Testing Available Endpoints Based on Actual Implementation")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup test user for authenticated endpoints
        await self.setup_test_user()
    
    async def setup_test_user(self):
        """Setup test user for authenticated endpoints"""
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
                    
        except Exception as e:
            print(f"⚠️ Error setting up demo user: {e}")
    
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

    # ============= SYSTEM HEALTH TEST =============
    
    async def test_system_health(self):
        """Test System Health"""
        test_name = "🎯 SYSTEM HEALTH CHECK"
        
        response = await self.test_api_endpoint("/health")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ System Health API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'healthy':
            services = data.get('services', {})
            
            # Count operational services
            operational_services = 0
            total_services = len(services)
            
            for service_name, service_status in services.items():
                if service_status in ['connected', 'running', 'active', 'available', 'ready', 'learning', 'coding']:
                    operational_services += 1
            
            health_percentage = (operational_services / total_services * 100) if total_services > 0 else 0
            
            if health_percentage >= 85:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ SYSTEM HEALTH EXCELLENT! {operational_services}/{total_services} services operational ({health_percentage:.1f}% health)"
                )
            elif health_percentage >= 70:
                self.log_test(test_name, "WARN", f"⚠️ System health good: {health_percentage:.1f}% ({operational_services}/{total_services})")
            else:
                self.log_test(test_name, "FAIL", f"❌ System health poor: {health_percentage:.1f}% ({operational_services}/{total_services})")
        else:
            self.log_test(test_name, "FAIL", f"❌ System not healthy: {data}")

    # ============= AI EVOLUTION & SELF-CODING TESTS =============
    
    async def test_ai_evolution_status(self):
        """Test AI Evolution Status"""
        test_name = "🎯 AI EVOLUTION STATUS"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        response = await self.test_api_endpoint("/ai/evolution/status", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Evolution Status API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            evolution_status = data.get('evolution_status', {})
            learning_cycles = evolution_status.get('total_evolution_cycles', 0)
            evolution_enabled = evolution_status.get('evolution_enabled', False)
            
            if evolution_enabled:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI EVOLUTION STATUS WORKING! Evolution enabled, {learning_cycles} cycles completed"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI Evolution not enabled: {evolution_status}")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Evolution Status error: {data}")

    async def test_ai_coding_plugins(self):
        """Test AI Coding Plugins"""
        test_name = "🎯 AI CODING PLUGINS"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        response = await self.test_api_endpoint("/ai/coding/plugins", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Coding Plugins API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            plugin_status = data.get('plugin_status', {})
            statistics = plugin_status.get('statistics', {})
            total_plugins = statistics.get('total_plugins', 0)
            
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ AI CODING PLUGINS WORKING! {total_plugins} total plugins available"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Coding Plugins error: {data}")

    async def test_ai_data_quality(self):
        """Test AI Data Quality"""
        test_name = "🎯 AI DATA QUALITY"
        
        response = await self.test_api_endpoint("/ai-data/data-quality")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Data Quality API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            quality_metrics = data.get('quality_metrics', {})
            overall_score = quality_metrics.get('overall_score', 0)
            bitcoin_dominance = quality_metrics.get('bitcoin_dominance', 0)
            
            if overall_score > 0.5 and bitcoin_dominance == 59.0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI DATA QUALITY EXCELLENT! Overall: {overall_score:.1%}, BTC Dominance: {bitcoin_dominance}%"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Data quality needs improvement: {overall_score:.1%}, BTC Dom: {bitcoin_dominance}%")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Data Quality error: {data}")

    # ============= ENHANCED SMART MONEY TESTS =============
    
    async def test_enhanced_smart_money(self):
        """Test Enhanced Smart Money"""
        test_name = "🎯 ENHANCED SMART MONEY"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1h")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Enhanced Smart Money API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            smart_money_data = data.get('data', {})
            
            # Check for available data
            has_liquidation_data = smart_money_data.get('liquidation_heatmap_2d') is not None
            has_oi_data = smart_money_data.get('open_interest_detailed') is not None
            
            if has_liquidation_data or has_oi_data:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ ENHANCED SMART MONEY WORKING! Liquidation: {has_liquidation_data}, OI: {has_oi_data}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Enhanced Smart Money API working but data limited")
        else:
            self.log_test(test_name, "FAIL", f"❌ Enhanced Smart Money error: {data}")

    # ============= REAL-TIME DATA TESTS =============
    
    async def test_real_time_data(self):
        """Test Real-time Data"""
        test_name = "🎯 REAL-TIME DATA"
        
        response = await self.test_api_endpoint("/realtime/latest?symbols=BTC/USDT,ETH/USDT")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Real-time Data API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' in data and data['status'] == 'success':
            realtime_data = data.get('data', {})
            available_symbols = list(realtime_data.keys())
            
            if len(available_symbols) >= 2:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ REAL-TIME DATA WORKING! {len(available_symbols)} symbols: {', '.join(available_symbols)}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Limited real-time data: {len(available_symbols)} symbols")
        else:
            self.log_test(test_name, "FAIL", f"❌ Real-time data error: {data}")

    # ============= PAPER TRADING TESTS =============
    
    async def test_paper_trading_account(self):
        """Test Paper Trading Account"""
        test_name = "🎯 PAPER TRADING ACCOUNT"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        response = await self.test_api_endpoint("/trading/account", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Paper Trading Account API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'account' in data:
            account = data['account']
            balance = account.get('balance', 0)
            equity = account.get('equity', 0)
            
            if balance > 0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ PAPER TRADING ACCOUNT WORKING! Balance: ${balance:,.2f}, Equity: ${equity:,.2f}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Invalid account data: Balance: ${balance}")
        else:
            self.log_test(test_name, "FAIL", f"❌ Paper trading account error: {data}")

    # ============= AI TRADING TESTS =============
    
    async def test_ai_trading_analyze(self):
        """Test AI Trading Analysis"""
        test_name = "🎯 AI TRADING ANALYSIS"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available")
            return
        
        analyze_data = {
            "symbol": "BTC/USDT",
            "context": "Test analysis"
        }
        
        response = await self.test_api_endpoint("/ai-trading/analyze", method="POST", data=analyze_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 UNPROCESSABLE ENTITY ERROR: {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Trading Analysis API failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'recommendation' in data:
            recommendation = data['recommendation']
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            action = recommendation.get('action', '') if isinstance(recommendation, dict) else ''
            
            if len(reasoning) > 50 and action:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI TRADING ANALYSIS WORKING! Reasoning: {len(reasoning)} chars, Action: {action}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI analysis working but limited: {len(reasoning)} chars, action: {action}")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI analysis response incomplete: {data}")

    # ============= NEWS & SENTIMENT TESTS =============
    
    async def test_news_sentiment_system(self):
        """Test News & Sentiment System"""
        test_name = "🎯 NEWS & SENTIMENT SYSTEM"
        
        endpoints = ["/financial-news", "/market-sentiment", "/economic-calendar"]
        working_endpoints = 0
        
        for endpoint in endpoints:
            response = await self.test_api_endpoint(endpoint)
            if response['success']:
                working_endpoints += 1
        
        success_rate = (working_endpoints / len(endpoints)) * 100
        
        if success_rate >= 75:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ NEWS & SENTIMENT SYSTEM WORKING! {working_endpoints}/{len(endpoints)} endpoints ({success_rate:.1f}%)"
            )
        else:
            self.log_test(test_name, "WARN", f"⚠️ Partial news/sentiment functionality: {working_endpoints}/{len(endpoints)} endpoints")

    # ============= MAIN TEST EXECUTION =============
    
    async def run_all_tests(self):
        """Run all targeted tests"""
        print("🔥 PHASE 1: SYSTEM HEALTH")
        await self.test_system_health()
        
        print("🔥 PHASE 2: AI EVOLUTION & SELF-CODING")
        await self.test_ai_evolution_status()
        await self.test_ai_coding_plugins()
        await self.test_ai_data_quality()
        
        print("🔥 PHASE 3: ENHANCED SMART MONEY & REAL-TIME")
        await self.test_enhanced_smart_money()
        await self.test_real_time_data()
        
        print("🔥 PHASE 4: PAPER TRADING")
        await self.test_paper_trading_account()
        
        print("🔥 PHASE 5: AI TRADING")
        await self.test_ai_trading_analyze()
        
        print("🔥 PHASE 6: NEWS & SENTIMENT")
        await self.test_news_sentiment_system()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("🎯 CHAiNALYZE TARGETED TESTING RESULTS")
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
        
        if success_rate >= 85:
            print(f"🎉 TARGET ACHIEVED: {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 70:
            print(f"⚠️ GOOD PERFORMANCE: {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️ NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        
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
    tester = CHAiNALYZETargetedTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())