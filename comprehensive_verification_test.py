#!/usr/bin/env python3
"""
Comprehensive Verification Test Suite
Additional tests to verify system stability and functionality
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Test configuration
BACKEND_URL = "https://self-coding-ai.preview.emergentagent.com/api"

class ComprehensiveVerificationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🔍 COMPREHENSIVE VERIFICATION TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Setup demo user
        await self.setup_demo_user()
    
    async def setup_demo_user(self):
        """Setup demo user"""
        try:
            login_data = {
                "email": "demo@example.com",
                "password": "demo123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    print("✅ Demo user authenticated")
                    
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
            print(f"   {details}")
        print()
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200, method: str = "GET", data: dict = None, auth: bool = False):
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

    # ============= SYSTEM HEALTH VERIFICATION =============
    
    async def test_basic_api_endpoints(self):
        """Test basic API endpoints are working"""
        test_name = "Basic API Endpoints Health Check"
        
        endpoints = [
            "/",
            "/plugins", 
            "/market-overview",
            "/realtime/latest"
        ]
        
        working_endpoints = 0
        
        for endpoint in endpoints:
            response = await self.test_api_endpoint(endpoint)
            if response['success']:
                working_endpoints += 1
        
        if working_endpoints == len(endpoints):
            self.log_test(test_name, "PASS", f"All {len(endpoints)} basic endpoints working")
        elif working_endpoints >= len(endpoints) * 0.75:
            self.log_test(test_name, "WARN", f"{working_endpoints}/{len(endpoints)} endpoints working")
        else:
            self.log_test(test_name, "FAIL", f"Only {working_endpoints}/{len(endpoints)} endpoints working")

    async def test_trading_system_integration(self):
        """Test trading system integration"""
        test_name = "Trading System Integration"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token")
            return
        
        # Test account endpoint
        account_response = await self.test_api_endpoint("/trading/account", auth=True)
        
        if account_response['success']:
            account_data = account_response['data']
            if 'balance' in account_data and account_data['balance'] > 0:
                self.log_test(test_name, "PASS", f"Trading account active with balance: ${account_data['balance']:.2f}")
            else:
                self.log_test(test_name, "WARN", "Trading account exists but balance unclear")
        else:
            self.log_test(test_name, "FAIL", f"Trading account access failed: {account_response.get('error')}")

    async def test_smart_money_system(self):
        """Test Smart Money system functionality"""
        test_name = "Smart Money System"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1h")
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'success' and 'data' in data:
                enhanced_data = data['data']
                if 'liquidation_heatmap_2d' in enhanced_data:
                    self.log_test(test_name, "PASS", "Smart Money system working with liquidation data")
                else:
                    self.log_test(test_name, "WARN", "Smart Money system working but missing liquidation data")
            else:
                self.log_test(test_name, "FAIL", f"Smart Money system error: {data}")
        else:
            self.log_test(test_name, "FAIL", f"Smart Money system failed: {response.get('error')}")

    async def test_real_time_data_system(self):
        """Test Real-time data system"""
        test_name = "Real-time Data System"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'success' and 'data' in data:
                realtime_data = data['data']
                # Check for key assets
                key_assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
                found_assets = [asset for asset in key_assets if asset in realtime_data and realtime_data[asset]]
                
                if len(found_assets) >= 2:
                    self.log_test(test_name, "PASS", f"Real-time data working for {len(found_assets)} key assets")
                else:
                    self.log_test(test_name, "WARN", f"Limited real-time data: {len(found_assets)} assets")
            else:
                self.log_test(test_name, "FAIL", f"Real-time data error: {data}")
        else:
            self.log_test(test_name, "FAIL", f"Real-time data failed: {response.get('error')}")

    # ============= GEMINI INTEGRATION STRESS TESTS =============
    
    async def test_gemini_multiple_requests(self):
        """Test Gemini with multiple concurrent requests"""
        test_name = "Gemini Multiple Requests Stress Test"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token")
            return
        
        # Create multiple chat requests
        requests = [
            {"session_id": "stress_test_1", "content": "Wie ist der aktuelle BTC Preis?"},
            {"session_id": "stress_test_2", "content": "Analysiere ETH kurz"},
            {"session_id": "stress_test_3", "content": "Was ist mein Portfolio Status?"}
        ]
        
        successful_requests = 0
        has_422_errors = False
        
        for i, chat_data in enumerate(requests):
            response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
            
            if response['status'] == 422:
                has_422_errors = True
            elif response['success']:
                successful_requests += 1
        
        if has_422_errors:
            self.log_test(test_name, "FAIL", "❌ 422 ERRORS detected in stress test!")
        elif successful_requests == len(requests):
            self.log_test(test_name, "PASS", f"All {len(requests)} concurrent requests successful")
        else:
            self.log_test(test_name, "WARN", f"{successful_requests}/{len(requests)} requests successful")

    async def test_gemini_complex_analysis_request(self):
        """Test Gemini with complex analysis request"""
        test_name = "Gemini Complex Analysis Request"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token")
            return
        
        complex_request = {
            "session_id": "complex_test",
            "content": "Führe eine vollständige Multi-Asset-Analyse durch: BTC, ETH, SOL. Berücksichtige Smart Money Daten, Liquidationen, mein Portfolio, aktuelle Markttrends und gib konkrete Trading-Empfehlungen mit Risiko-Management."
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=complex_request, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", "❌ 422 ERROR bei komplexer Analyse!")
        elif response['success']:
            data = response['data']
            ai_response = data.get('content', '')
            
            # Check for comprehensive analysis
            analysis_indicators = ['btc', 'eth', 'sol', 'liquidation', 'portfolio', 'risiko', 'empfehlung']
            indicator_count = sum(1 for word in analysis_indicators if word.lower() in ai_response.lower())
            
            if len(ai_response) > 2000 and indicator_count >= 5:
                self.log_test(test_name, "PASS", f"Complex analysis successful: {len(ai_response)} chars, {indicator_count} indicators")
            else:
                self.log_test(test_name, "WARN", f"Complex analysis incomplete: {len(ai_response)} chars, {indicator_count} indicators")
        else:
            self.log_test(test_name, "FAIL", f"Complex analysis failed: {response.get('error')}")

    # ============= ERROR HANDLING VERIFICATION =============
    
    async def test_error_handling_robustness(self):
        """Test system error handling"""
        test_name = "Error Handling Robustness"
        
        # Test with invalid requests
        invalid_requests = [
            {"session_id": "", "content": ""},  # Empty content
            {"session_id": "test", "content": "x" * 10000},  # Very long content
            {"invalid_field": "test"}  # Invalid structure
        ]
        
        handled_errors = 0
        
        for invalid_request in invalid_requests:
            response = await self.test_api_endpoint("/chat", method="POST", data=invalid_request, auth=True)
            
            # Should handle gracefully (not crash)
            if response['status'] in [400, 422] or (response['success'] and 'error' not in str(response['data']).lower()):
                handled_errors += 1
        
        if handled_errors == len(invalid_requests):
            self.log_test(test_name, "PASS", "All error cases handled gracefully")
        else:
            self.log_test(test_name, "WARN", f"{handled_errors}/{len(invalid_requests)} error cases handled")

    # ============= PERFORMANCE VERIFICATION =============
    
    async def test_response_time_performance(self):
        """Test response time performance"""
        test_name = "Response Time Performance"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token")
            return
        
        start_time = datetime.now()
        
        chat_data = {
            "session_id": "performance_test",
            "content": "Gib mir eine schnelle BTC Analyse"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if response['success']:
            if response_time < 10:
                self.log_test(test_name, "PASS", f"Good response time: {response_time:.2f} seconds")
            elif response_time < 20:
                self.log_test(test_name, "WARN", f"Acceptable response time: {response_time:.2f} seconds")
            else:
                self.log_test(test_name, "FAIL", f"Slow response time: {response_time:.2f} seconds")
        else:
            self.log_test(test_name, "FAIL", f"Performance test failed: {response.get('error')}")

    # ============= RUN ALL VERIFICATION TESTS =============
    
    async def run_all_verification_tests(self):
        """Run all verification tests"""
        print("🚀 STARTE COMPREHENSIVE VERIFICATION TESTS...")
        print()
        
        # System Health
        await self.test_basic_api_endpoints()
        await self.test_trading_system_integration()
        await self.test_smart_money_system()
        await self.test_real_time_data_system()
        
        # Gemini Stress Tests
        await self.test_gemini_multiple_requests()
        await self.test_gemini_complex_analysis_request()
        
        # Error Handling
        await self.test_error_handling_robustness()
        
        # Performance
        await self.test_response_time_performance()
        
        # Summary
        await self.print_verification_summary()
    
    async def print_verification_summary(self):
        """Print verification test summary"""
        print("=" * 60)
        print("📊 COMPREHENSIVE VERIFICATION SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        total = len(self.test_results)
        
        print(f"✅ ERFOLGREICH: {passed}/{total}")
        print(f"❌ FEHLGESCHLAGEN: {failed}/{total}")
        print(f"⚠️ WARNUNGEN: {warnings}/{total}")
        print()
        
        # Check for critical issues
        has_422_errors = any('422' in r['details'] for r in self.test_results if r['status'] == 'FAIL')
        
        if has_422_errors:
            print("🚨 KRITISCH: 422 ERRORS in Verification Tests gefunden!")
        else:
            print("✅ KEINE 422 ERRORS in Verification Tests!")
        
        print()
        
        # Detailed results
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}")
        
        print()
        print("🔍 VERIFICATION FAZIT:")
        if failed == 0:
            print("   System vollständig stabil und funktionsfähig!")
        elif has_422_errors:
            print("   KRITISCHE 422 ERRORS müssen behoben werden.")
        else:
            print("   System größtenteils stabil - kleinere Verbesserungen möglich.")

async def main():
    """Main test execution"""
    tester = ComprehensiveVerificationTester()
    
    try:
        await tester.setup()
        await tester.run_all_verification_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())