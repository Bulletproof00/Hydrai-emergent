#!/usr/bin/env python3
"""
Priority Test Suite for Gemini 2.5 Flash AI Chat System
Focus: Testing the specific priority areas mentioned in the request
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Test configuration
BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"

class GeminiPriorityTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🎯 GEMINI 2.5 FLASH PRIORITY TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Setup demo user as requested
        await self.setup_demo_user()
    
    async def setup_demo_user(self):
        """Setup demo user (demo@example.com/demo123) as requested"""
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
                    print("✅ Demo user login successful (demo@example.com)")
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
                    print("✅ Demo user registered (demo@example.com)")
                else:
                    print("⚠️ Could not setup demo user")
                    
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

    # ============= PRIORITY TEST 1: GEMINI 2.5 FLASH INTEGRATION =============
    
    async def test_gemini_25_flash_greeting(self):
        """Test: Hallo! Wie geht es dir heute? (einfacher Gruß)"""
        test_name = "PRIORITY 1a: Gemini 2.5 Flash - Einfacher Gruß"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Hallo! Wie geht es dir heute?"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 UNPROCESSABLE ENTITY ERROR - Das ist der Hauptfehler! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check if response is in German and comprehensive
        german_indicators = ['hallo', 'ich', 'bin', 'hydra', 'system', 'trading', 'gut', 'heute']
        german_count = sum(1 for word in german_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 100 and german_count >= 3:
            self.log_test(test_name, "PASS", f"✅ KEINE 422 ERRORS! Deutsche Antwort: {len(ai_response)} chars, {german_count} deutsche Indikatoren")
        else:
            self.log_test(test_name, "WARN", f"Antwort möglicherweise unvollständig: {len(ai_response)} chars, {german_count} deutsche Indikatoren")

    async def test_gemini_25_flash_btc_analysis(self):
        """Test: Analysiere Bitcoin für mich bitte (BTC-Analyse)"""
        test_name = "PRIORITY 1b: Gemini 2.5 Flash - BTC Analyse"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Analysiere Bitcoin für mich bitte"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 ERROR NOCH VORHANDEN! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for comprehensive BTC analysis
        btc_indicators = ['btc', 'bitcoin', 'preis', 'analyse', 'trading', 'markt', 'trend', 'empfehlung']
        btc_count = sum(1 for word in btc_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 300 and btc_count >= 4:
            self.log_test(test_name, "PASS", f"✅ BTC ANALYSE FUNKTIONIERT! {len(ai_response)} chars, {btc_count} BTC Indikatoren")
        else:
            self.log_test(test_name, "WARN", f"BTC Analyse möglicherweise unvollständig: {len(ai_response)} chars, {btc_count} Indikatoren")

    async def test_gemini_25_flash_portfolio_status(self):
        """Test: Was ist mein aktueller Paper Trading Status? (Portfolio Abfrage)"""
        test_name = "PRIORITY 1c: Gemini 2.5 Flash - Portfolio Status"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Was ist mein aktueller Paper Trading Status?"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 ERROR WEITERHIN VORHANDEN! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for portfolio data access
        portfolio_indicators = ['balance', 'position', 'portfolio', 'trading', 'account', 'status', 'paper']
        portfolio_count = sum(1 for word in portfolio_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 200 and portfolio_count >= 3:
            self.log_test(test_name, "PASS", f"✅ PORTFOLIO ZUGRIFF FUNKTIONIERT! {len(ai_response)} chars, {portfolio_count} Portfolio Indikatoren")
        else:
            self.log_test(test_name, "WARN", f"Portfolio Zugriff möglicherweise eingeschränkt: {len(ai_response)} chars, {portfolio_count} Indikatoren")

    # ============= PRIORITY TEST 2: AI TRADING ENGINE ENDPOINTS =============
    
    async def test_ai_trading_analyze_endpoint(self):
        """Test: POST /api/ai-trading/analyze"""
        test_name = "PRIORITY 2a: AI Trading Engine - Analyze Endpoint"
        
        response = await self.test_api_endpoint("/ai-trading/analyze?symbol=BTC/USDT&context=simple_analysis", method="POST", auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 ERROR im AI Trading Analyze! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"AI Trading Analyze failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for AI analysis response structure
        if 'recommendation' in data and 'symbol' in data:
            recommendation = data.get('recommendation', {})
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            
            if len(reasoning) > 100:
                self.log_test(test_name, "PASS", f"✅ AI Trading Analyze funktioniert! {len(reasoning)} chars Analyse")
            else:
                self.log_test(test_name, "WARN", f"AI Analyse kürzer als erwartet: {len(reasoning)} chars")
        else:
            self.log_test(test_name, "FAIL", "Unvollständige AI Analyse Antwort")

    async def test_ai_trading_chat_command_endpoint(self):
        """Test: POST /api/ai-trading/chat-command"""
        test_name = "PRIORITY 2b: AI Trading Engine - Chat Command Endpoint"
        
        import urllib.parse
        command = "Analysiere ETH für Trading"
        encoded_command = urllib.parse.quote(command)
        
        response = await self.test_api_endpoint(f"/ai-trading/chat-command?command={encoded_command}", method="POST", auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ 422 ERROR im AI Trading Chat Command! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"AI Trading Chat Command failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if command was processed
        if 'result' in data and data.get('status') == 'success':
            result = data['result']
            if 'ETH' in str(result) or 'eth' in str(result).lower():
                self.log_test(test_name, "PASS", f"✅ AI Trading Chat Command funktioniert! Command verarbeitet")
            else:
                self.log_test(test_name, "WARN", f"Command verarbeitet aber Ergebnis unklar: {str(result)[:100]}")
        else:
            self.log_test(test_name, "FAIL", f"Chat Command Verarbeitung fehlgeschlagen: {data}")

    # ============= PRIORITY TEST 3: GEMINI API VERBESSERUNGEN =============
    
    async def test_gemini_api_improvements_verification(self):
        """Test: Verify Gemini API improvements (google-genai SDK, gemini-2.5-flash model)"""
        test_name = "PRIORITY 3: Gemini API Verbesserungen Verifikation"
        
        # Test with a complex request that should use the new API structure
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Führe eine detaillierte technische Analyse von Bitcoin durch mit allen verfügbaren Systemdaten"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ KRITISCH: 422 ERROR - Gemini API Verbesserungen nicht erfolgreich! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"Gemini API Test failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for comprehensive analysis (should be very detailed with new model)
        if len(ai_response) > 1000:
            self.log_test(test_name, "PASS", f"✅ GEMINI API VERBESSERUNGEN ERFOLGREICH! Detaillierte Analyse: {len(ai_response)} chars")
        elif len(ai_response) > 500:
            self.log_test(test_name, "WARN", f"Gemini funktioniert aber Analyse kürzer als erwartet: {len(ai_response)} chars")
        else:
            self.log_test(test_name, "FAIL", f"Gemini Antwort zu kurz oder unvollständig: {len(ai_response)} chars")

    # ============= COMPREHENSIVE TEST SUMMARY =============
    
    async def run_all_priority_tests(self):
        """Run all priority tests"""
        print("🚀 STARTE ALLE PRIORITÄTSTESTS...")
        print()
        
        # Priority 1: Gemini 2.5 Flash Integration Tests
        await self.test_gemini_25_flash_greeting()
        await self.test_gemini_25_flash_btc_analysis()
        await self.test_gemini_25_flash_portfolio_status()
        
        # Priority 2: AI Trading Engine Endpoints Tests
        await self.test_ai_trading_analyze_endpoint()
        await self.test_ai_trading_chat_command_endpoint()
        
        # Priority 3: Gemini API Improvements Verification
        await self.test_gemini_api_improvements_verification()
        
        # Summary
        await self.print_test_summary()
    
    async def print_test_summary(self):
        """Print comprehensive test summary"""
        print("=" * 60)
        print("📊 GEMINI 2.5 FLASH PRIORITY TEST ZUSAMMENFASSUNG")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        total = len(self.test_results)
        
        print(f"✅ ERFOLGREICH: {passed}/{total}")
        print(f"❌ FEHLGESCHLAGEN: {failed}/{total}")
        print(f"⚠️ WARNUNGEN: {warnings}/{total}")
        print()
        
        # Critical 422 error check
        has_422_errors = any('422' in r['details'] for r in self.test_results if r['status'] == 'FAIL')
        
        if has_422_errors:
            print("🚨 KRITISCH: 422 UNPROCESSABLE ENTITY ERRORS NOCH VORHANDEN!")
            print("   Das war das Hauptproblem das behoben werden sollte.")
        else:
            print("🎯 ERFOLG: KEINE 422 ERRORS MEHR GEFUNDEN!")
            print("   Das Hauptproblem wurde erfolgreich behoben.")
        
        print()
        
        # Detailed results
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}")
        
        print()
        print("🔍 FAZIT:")
        if failed == 0:
            print("   Alle Prioritätstests erfolgreich! Gemini 2.5 Flash System funktioniert.")
        elif has_422_errors:
            print("   KRITISCHE 422 ERRORS müssen noch behoben werden.")
        else:
            print("   Teilweise erfolgreich - einige Verbesserungen möglich.")

async def main():
    """Main test execution"""
    tester = GeminiPriorityTester()
    
    try:
        await tester.setup()
        await tester.run_all_priority_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())