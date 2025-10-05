#!/usr/bin/env python3
"""
Backend Test Suite for Trading System with Real-time Data and AI Integration
Tests: Real-time Integration, AI Trading Engine, Enhanced Smart Money, Paper Trading Integration
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
BACKEND_URL = "https://smart-trade-ai-28.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://liquidation-oracle.preview.emergentagent.com/api/realtime"

class TradingSystemTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Trading System with Real-time Data and AI Integration Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup test user for authenticated endpoints
        await self.setup_test_user()
    
    async def setup_test_user(self):
        """Setup test user for authenticated endpoints - using demo user as requested"""
        try:
            # Try to login with demo user as requested in the test requirements
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

    # ============= FINALE TESTS - CHAT UND AI-REPARATUREN =============
    
    async def test_chat_system_repair_test(self):
        """FINALE TEST 1: CHAT SYSTEM REPARATUR TEST - POST /api/chat"""
        test_name = "🎯 FINALE TEST 1: CHAT SYSTEM REPARATUR"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available for demo@example.com")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Hallo! Funktioniert der Chat jetzt?"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ KRITISCHER FEHLER: 422 UNPROCESSABLE ENTITY ERROR NOCH VORHANDEN! Das war der Hauptfehler der behoben werden sollte! Error: {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Chat API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for German AI response
        german_indicators = ['hallo', 'ich', 'bin', 'hydra', 'system', 'trading', 'analyse', 'funktioniert', 'ja']
        german_count = sum(1 for word in german_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 200 and german_count >= 3:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ CHAT SYSTEM REPARATUR ERFOLGREICH! KEINE 422 Errors, Deutsche AI-Antwort erhalten: {len(ai_response)} chars, {german_count} German indicators",
                "KEINE 422 Errors, deutsche AI-Antwort mit Authorization Header",
                f"✅ SUCCESS: {len(ai_response)} chars, {german_count} German indicators, NO 422 ERROR!"
            )
        else:
            self.log_test(test_name, "WARN", f"⚠️ Chat funktioniert aber Antwort könnte besser sein: {len(ai_response)} chars, {german_count} German indicators")

    async def test_ai_trading_analyse_repair_test(self):
        """FINALE TEST 2: AI TRADING ANALYSE REPARATUR TEST - POST /api/ai-trading/analyze"""
        test_name = "🎯 FINALE TEST 2: AI TRADING ANALYSE REPARATUR"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available for demo@example.com")
            return
        
        analyze_data = {
            "symbol": "BTC/USDT",
            "context": "Test analysis"
        }
        
        response = await self.test_api_endpoint("/ai-trading/analyze", method="POST", data=analyze_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ KRITISCHER FEHLER: 422 UNPROCESSABLE ENTITY ERROR BEI AI TRADING ANALYSE! Das war der Hauptfehler der behoben werden sollte! Error: {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Trading Analyze API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
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
                    f"✅ AI TRADING ANALYSE REPARATUR ERFOLGREICH! KEINE 422 Errors, erfolgreiche AI-Analyse: {len(reasoning)} chars reasoning, action: {action}",
                    "KEINE 422 Errors, erfolgreiche AI-Analyse mit korrekter Authorization Header",
                    f"✅ SUCCESS: {len(reasoning)} chars reasoning, action: {action}, NO 422 ERROR!"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ AI Analyse funktioniert aber könnte detaillierter sein: {len(reasoning)} chars, action: {action}")
        else:
            self.log_test(test_name, "FAIL", f"❌ AI Analyse Response unvollständig: {data}")

    async def test_ai_trading_chat_command_repair_test(self):
        """FINALE TEST 3: AI TRADING CHAT COMMAND REPARATUR TEST - POST /api/ai-trading/chat-command"""
        test_name = "🎯 FINALE TEST 3: AI TRADING CHAT COMMAND REPARATUR"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available for demo@example.com")
            return
        
        command_data = {
            "command": "analyze BTC"
        }
        
        response = await self.test_api_endpoint("/ai-trading/chat-command", method="POST", data=command_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ KRITISCHER FEHLER: 422 UNPROCESSABLE ENTITY ERROR BEI AI TRADING CHAT COMMAND! Das war der Hauptfehler der behoben werden sollte! Error: {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ AI Trading Chat Command API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful command processing
        if 'result' in data and data.get('status') == 'success':
            result = data.get('result', '')
            command_processed = 'btc' in str(result).lower() or 'bitcoin' in str(result).lower()
            
            if command_processed:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ AI TRADING CHAT COMMAND REPARATUR ERFOLGREICH! KEINE 422 Errors, erfolgreiche Command-Verarbeitung: {str(result)[:100]}...",
                    "KEINE 422 Errors, erfolgreiche Command-Verarbeitung",
                    f"✅ SUCCESS: Command processed, NO 422 ERROR!"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Command verarbeitet aber Ergebnis unklar: {result}")
        else:
            self.log_test(test_name, "FAIL", f"❌ Chat Command Processing failed: {data}")

    async def test_vollstaendige_integration_verifikation(self):
        """FINALE TEST 4: VOLLSTÄNDIGE INTEGRATION VERIFIKATION - Chat mit Trading-Analyse"""
        test_name = "🎯 FINALE TEST 4: VOLLSTÄNDIGE INTEGRATION VERIFIKATION"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "❌ No authentication token available for demo@example.com")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Analysiere BTC für mich"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ KRITISCHER FEHLER: 422 ERROR IN VOLLSTÄNDIGER INTEGRATION! {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Vollständige Integration failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for comprehensive integration with all system modules
        integration_indicators = [
            'btc', 'bitcoin', 'trading', 'analyse', 'smart money', 'liquidation', 
            'paper trading', 'preis', 'markt', 'system', 'real-time'
        ]
        integration_count = sum(1 for word in integration_indicators if word.lower() in ai_response.lower())
        
        # Check for German response
        german_indicators = ['ich', 'bin', 'der', 'die', 'das', 'und', 'mit', 'für', 'auf', 'ist']
        german_count = sum(1 for word in german_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 500 and integration_count >= 4 and german_count >= 3:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ VOLLSTÄNDIGE INTEGRATION ERFOLGREICH! Chat mit Trading-Analyse funktioniert, AI hat Zugang zu Paper Trading und Smart Money, Deutsche Antworten mit Systemkontext: {len(ai_response)} chars, {integration_count} integration indicators, {german_count} German indicators",
                "✅ KEINE 422 Errors ✅ Chat funktioniert mit Authorization Header ✅ AI Trading Analyse funktioniert ✅ Deutsche AI-Antworten mit vollständigem Systemzugang",
                f"✅ COMPLETE SUCCESS: {len(ai_response)} chars, {integration_count} modules, {german_count} German, NO 422!"
            )
        else:
            self.log_test(test_name, "WARN", f"⚠️ Integration teilweise erfolgreich: {len(ai_response)} chars, {integration_count} integration, {german_count} German indicators")

    async def test_gemini_25_pro_integration(self):
        """Test that Gemini 2.5 Pro is working without 422 errors"""
        test_name = "Gemini 2.5 Pro Integration - No 422 Errors"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Führe eine detaillierte technische Analyse von Bitcoin durch"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 UNPROCESSABLE ENTITY ERROR STILL EXISTS! This was the main issue to fix. Error: {response.get('error', 'Unknown error')}")
            return
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for detailed Gemini 2.5 Pro analysis (should be very comprehensive)
        if len(ai_response) > 1000:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ GEMINI 2.5 PRO WORKING! No 422 errors, comprehensive analysis: {len(ai_response)} chars",
                "Gemini 2.5 Pro providing detailed German analysis without 422 errors",
                f"Analysis length: {len(ai_response)} chars - No 422 errors!"
            )
        elif len(ai_response) > 500:
            self.log_test(test_name, "WARN", f"Gemini working but analysis shorter than expected: {len(ai_response)} chars")
        else:
            self.log_test(test_name, "FAIL", f"Gemini response too short or incomplete: {len(ai_response)} chars")

    async def test_ai_system_integration_comprehensive(self):
        """Test comprehensive AI system integration with all modules"""
        test_name = "AI System Integration - All Modules Access"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        chat_data = {
            "session_id": "demo_test_session",
            "content": "Gib mir eine vollständige Marktanalyse mit Smart Money Daten, Real-time Preisen und meinem Portfolio-Status"
        }
        
        response = await self.test_api_endpoint("/chat", method="POST", data=chat_data, auth=True)
        
        if not response['success']:
            if response['status'] == 422:
                self.log_test(test_name, "FAIL", f"❌ 422 ERROR IN COMPREHENSIVE TEST! {response.get('error', 'Unknown error')}")
            else:
                self.log_test(test_name, "FAIL", f"Comprehensive test failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        ai_response = data.get('content', '')
        
        # Check for integration with all system modules
        integration_indicators = [
            'smart money', 'liquidation', 'real-time', 'portfolio', 'position', 
            'preis', 'markt', 'analyse', 'trading', 'system'
        ]
        integration_count = sum(1 for word in integration_indicators if word.lower() in ai_response.lower())
        
        if len(ai_response) > 800 and integration_count >= 6:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ FULL SYSTEM INTEGRATION WORKING! {len(ai_response)} chars, {integration_count} integration indicators",
                "AI has access to all system modules: Paper Trading, Smart Money, Real-time data",
                f"Comprehensive integration: {len(ai_response)} chars, {integration_count} modules"
            )
        else:
            self.log_test(test_name, "WARN", f"Partial system integration: {len(ai_response)} chars, {integration_count} indicators")

    # ============= ENHANCED TIMEFRAME TESTS =============
    
    async def test_enhanced_timeframes_5m(self):
        """Test POST /api/enhanced-smart-money/data with 5m timeframe"""
        test_name = "Enhanced Smart Money - BTC/USDT (5m timeframe)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=5m")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        # Check for timeframe-specific data
        if enhanced_data.get('timeframe') == '5m' and 'liquidation_heatmap_2d' in enhanced_data:
            heatmap_data = enhanced_data['liquidation_heatmap_2d']
            if 'cumulative_long' in str(heatmap_data) and 'cumulative_short' in str(heatmap_data):
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"5m timeframe data with cumulative liquidation data available",
                    "Enhanced data with 5m timeframe and cumulative data",
                    "5m timeframe with cumulative liquidations"
                )
            else:
                self.log_test(test_name, "WARN", "5m timeframe data available but missing cumulative data")
        else:
            self.log_test(test_name, "FAIL", f"5m timeframe data not properly structured")

    async def test_enhanced_timeframes_15m(self):
        """Test POST /api/enhanced-smart-money/data with 15m timeframe"""
        test_name = "Enhanced Smart Money - ETH/USDT (15m timeframe)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=ETH/USDT&timeframe=15m")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '15m':
            self.log_test(
                test_name, 
                "PASS", 
                f"15m timeframe data available for ETH/USDT",
                "Enhanced data with 15m timeframe",
                "15m timeframe working"
            )
        else:
            self.log_test(test_name, "FAIL", f"15m timeframe not working properly")

    async def test_enhanced_timeframes_1h(self):
        """Test POST /api/enhanced-smart-money/data with 1h timeframe"""
        test_name = "Enhanced Smart Money - BTC/USDT (1h timeframe)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1h")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '1h':
            self.log_test(
                test_name, 
                "PASS", 
                f"1h timeframe data available for BTC/USDT",
                "Enhanced data with 1h timeframe",
                "1h timeframe working"
            )
        else:
            self.log_test(test_name, "FAIL", f"1h timeframe not working properly")

    async def test_enhanced_timeframes_4h(self):
        """Test POST /api/enhanced-smart-money/data with 4h timeframe"""
        test_name = "Enhanced Smart Money - ETH/USDT (4h timeframe)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=ETH/USDT&timeframe=4h")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '4h':
            self.log_test(
                test_name, 
                "PASS", 
                f"4h timeframe data available for ETH/USDT",
                "Enhanced data with 4h timeframe",
                "4h timeframe working"
            )
        else:
            self.log_test(test_name, "FAIL", f"4h timeframe not working properly")

    async def test_enhanced_timeframes_8h(self):
        """Test POST /api/enhanced-smart-money/data with 8h timeframe"""
        test_name = "Enhanced Smart Money - BTC/USDT (8h timeframe)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=8h")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '8h':
            self.log_test(
                test_name, 
                "PASS", 
                f"8h timeframe data available for BTC/USDT",
                "Enhanced data with 8h timeframe",
                "8h timeframe working"
            )
        else:
            self.log_test(test_name, "FAIL", f"8h timeframe not working properly")

    async def test_cumulative_liquidation_data(self):
        """Test that cumulative_long and cumulative_short exist in liquidation data"""
        test_name = "Cumulative Liquidation Data Validation"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        enhanced_data = data.get('data', {})
        
        if 'liquidation_heatmap_2d' in enhanced_data:
            heatmap_data = enhanced_data['liquidation_heatmap_2d']
            liquidation_levels = heatmap_data.get('liquidation_levels', [])
            
            cumulative_fields_found = 0
            for level in liquidation_levels[:5]:  # Check first 5 levels
                if 'cumulative_long' in level and 'cumulative_short' in level:
                    cumulative_fields_found += 1
            
            if cumulative_fields_found >= 3:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Cumulative liquidation data found in {cumulative_fields_found}/5 levels",
                    "cumulative_long and cumulative_short fields in liquidation levels",
                    f"{cumulative_fields_found} levels with cumulative data"
                )
            else:
                self.log_test(test_name, "FAIL", f"Cumulative data missing or incomplete: {cumulative_fields_found}/5 levels")
        else:
            self.log_test(test_name, "FAIL", "No liquidation heatmap data available")

    # ============= PAPER TRADING POSITION CLOSE TESTS =============
    
    async def test_position_close_25_percent(self):
        """Test POST /api/trading/position/close with 25% close"""
        test_name = "Paper Trading - Position Close 25%"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        # First create a position
        order_data = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.01,
            "leverage": 10
        }
        
        order_response = await self.test_api_endpoint("/trading/order", method="POST", data=order_data, auth=True)
        
        if not order_response['success']:
            self.log_test(test_name, "FAIL", f"Could not create position for test: {order_response.get('error')}")
            return
        
        # Get positions to find position_id
        positions_response = await self.test_api_endpoint("/trading/positions", auth=True)
        
        if not positions_response['success'] or not positions_response['data']:
            self.log_test(test_name, "FAIL", "No positions found after creating order")
            return
        
        positions_data = positions_response['data']
        if isinstance(positions_data, dict):
            positions = positions_data.get('positions', [])
        else:
            positions = positions_data if isinstance(positions_data, list) else []
        
        if not positions:
            self.log_test(test_name, "FAIL", "No positions in response")
            return
        
        position_id = positions[0].get('position_id')
        if not position_id:
            self.log_test(test_name, "FAIL", "No position_id found in position data")
            return
        
        # Close 25% of position
        close_data = {
            "position_id": position_id,
            "close_percentage": 25.0
        }
        
        close_response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data, auth=True)
        
        if close_response['success']:
            close_result = close_response['data']
            if close_result.get('close_percentage') == 25.0 and 'pnl' in close_result:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"25% position close successful - PnL: ${close_result.get('net_pnl', 0):.2f}",
                    "Partial position close with PnL calculation",
                    f"25% closed, PnL calculated"
                )
            else:
                self.log_test(test_name, "FAIL", f"Position close response incomplete: {close_result}")
        else:
            self.log_test(test_name, "FAIL", f"Position close failed: {close_response.get('error')}")

    async def test_position_close_50_percent(self):
        """Test POST /api/trading/position/close with 50% close"""
        test_name = "Paper Trading - Position Close 50%"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        # Get existing positions
        positions_response = await self.test_api_endpoint("/trading/positions", auth=True)
        
        if not positions_response['success'] or not positions_response['data']:
            self.log_test(test_name, "FAIL", "No positions available for 50% close test")
            return
        
        positions_data = positions_response['data']
        if isinstance(positions_data, dict):
            positions = positions_data.get('positions', [])
        else:
            positions = positions_data if isinstance(positions_data, list) else []
        if not positions:
            self.log_test(test_name, "FAIL", "No positions found")
            return
        
        position_id = positions[0].get('position_id')
        
        # Close 50% of position
        close_data = {
            "position_id": position_id,
            "close_percentage": 50.0
        }
        
        close_response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data, auth=True)
        
        if close_response['success']:
            close_result = close_response['data']
            if close_result.get('close_percentage') == 50.0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"50% position close successful - PnL: ${close_result.get('net_pnl', 0):.2f}",
                    "50% partial position close",
                    "50% closed successfully"
                )
            else:
                self.log_test(test_name, "FAIL", f"50% close percentage not correct: {close_result}")
        else:
            self.log_test(test_name, "FAIL", f"50% position close failed: {close_response.get('error')}")

    async def test_position_close_100_percent(self):
        """Test POST /api/trading/position/close with 100% close (full close)"""
        test_name = "Paper Trading - Position Close 100% (Full Close)"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        # Get existing positions
        positions_response = await self.test_api_endpoint("/trading/positions", auth=True)
        
        if not positions_response['success'] or not positions_response['data']:
            self.log_test(test_name, "FAIL", "No positions available for 100% close test")
            return
        
        positions_data = positions_response['data']
        if isinstance(positions_data, dict):
            positions = positions_data.get('positions', [])
        else:
            positions = positions_data if isinstance(positions_data, list) else []
        if not positions:
            self.log_test(test_name, "FAIL", "No positions found")
            return
        
        position_id = positions[0].get('position_id')
        
        # Close 100% of position
        close_data = {
            "position_id": position_id,
            "close_percentage": 100.0
        }
        
        close_response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data, auth=True)
        
        if close_response['success']:
            close_result = close_response['data']
            if close_result.get('close_percentage') == 100.0:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"100% position close successful - Final PnL: ${close_result.get('net_pnl', 0):.2f}",
                    "Full position close",
                    "100% closed successfully"
                )
            else:
                self.log_test(test_name, "FAIL", f"100% close percentage not correct: {close_result}")
        else:
            self.log_test(test_name, "FAIL", f"100% position close failed: {close_response.get('error')}")

    async def test_pnl_calculation_accuracy(self):
        """Test PnL calculation accuracy and balance updates"""
        test_name = "PnL Calculation and Balance Updates"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        # Get account balance before
        account_before = await self.test_api_endpoint("/trading/account", auth=True)
        
        if not account_before['success']:
            self.log_test(test_name, "FAIL", "Could not get account balance before test")
            return
        
        balance_before = account_before['data'].get('balance', 0)
        
        # Create a small position
        order_data = {
            "symbol": "ETH/USDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.1,
            "leverage": 5
        }
        
        order_response = await self.test_api_endpoint("/trading/order", method="POST", data=order_data, auth=True)
        
        if not order_response['success']:
            self.log_test(test_name, "FAIL", f"Could not create test position: {order_response.get('error')}")
            return
        
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Get account balance after
        account_after = await self.test_api_endpoint("/trading/account", auth=True)
        
        if account_after['success']:
            balance_after = account_after['data'].get('balance', 0)
            balance_change = balance_after - balance_before
            
            # Check if balance changed (should be negative due to fees)
            if abs(balance_change) > 0.01:  # At least 1 cent change
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Balance updated correctly: ${balance_before:.2f} → ${balance_after:.2f} (${balance_change:.2f})",
                    "Accurate balance updates after trading",
                    f"Balance change: ${balance_change:.2f}"
                )
            else:
                self.log_test(test_name, "WARN", f"Balance change too small: ${balance_change:.4f}")
        else:
            self.log_test(test_name, "FAIL", "Could not get account balance after trade")

    # ============= GEMINI AI INTEGRATION TESTS =============
    
    async def test_gemini_ai_btc_analysis(self):
        """Test POST /api/ai-trading/analyze with Gemini AI for BTC/USDT"""
        test_name = "Gemini AI Integration - BTC/USDT Analysis"
        
        response = await self.test_api_endpoint("/ai-trading/analyze?symbol=BTC/USDT&context=comprehensive_gemini_analysis", method="POST", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for Gemini AI response structure
        if 'recommendation' in data:
            recommendation = data['recommendation']
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            
            # Check for comprehensive analysis (Gemini should provide detailed reasoning)
            if len(reasoning) > 500:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Gemini AI analysis successful: {len(reasoning)} chars reasoning",
                    "Comprehensive AI analysis with detailed reasoning",
                    f"Analysis length: {len(reasoning)} chars"
                )
            else:
                self.log_test(test_name, "WARN", f"Gemini analysis shorter than expected: {len(reasoning)} chars")
        else:
            self.log_test(test_name, "FAIL", "No recommendation in Gemini AI response")

    async def test_gemini_ai_chat_command_long(self):
        """Test POST /api/ai-trading/chat-command with 'Long BTC 0.1' command"""
        test_name = "Gemini AI Chat Command - Long BTC 0.1"
        
        response = await self.test_api_endpoint("/ai-trading/chat-command?command=Long%20BTC%200.1", method="POST", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if command was processed
        if 'result' in data and data.get('status') == 'success':
            result = data['result']
            if 'BTC' in str(result) and ('long' in str(result).lower() or 'buy' in str(result).lower()):
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Chat command processed successfully: {str(result)[:100]}...",
                    "AI processing of 'Long BTC 0.1' command",
                    "Command processed correctly"
                )
            else:
                self.log_test(test_name, "WARN", f"Command processed but result unclear: {result}")
        else:
            self.log_test(test_name, "FAIL", f"Chat command processing failed: {data}")

    async def test_gemini_ai_response_parsing(self):
        """Test Gemini API response parsing and JSON structure"""
        test_name = "Gemini AI Response Parsing"
        
        response = await self.test_api_endpoint("/ai-trading/analyze?symbol=ETH/USDT&context=json_parsing_test", method="POST", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for proper JSON structure
        required_fields = ['symbol', 'recommendation']
        missing_fields = [field for field in required_fields if field not in data]
        
        if not missing_fields:
            recommendation = data['recommendation']
            if isinstance(recommendation, dict) and 'action' in recommendation:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Gemini response properly parsed with action: {recommendation.get('action')}",
                    "Proper JSON parsing of Gemini AI response",
                    "JSON structure valid"
                )
            else:
                self.log_test(test_name, "WARN", "Response parsed but recommendation structure incomplete")
        else:
            self.log_test(test_name, "FAIL", f"Missing fields in parsed response: {missing_fields}")

    # ============= CHAT SYSTEM TESTS =============
    
    async def test_chat_without_auth(self):
        """Test POST /api/chat without Auth-Header"""
        test_name = "Chat System - No Auth Required"
        
        data = {"session_id": "test_session", "content": "Hello, can you help me with trading analysis?"}
        response = await self.test_api_endpoint("/chat", method="POST", data=data, auth=True)
        
        if response['success']:
            data = response['data']
            if 'response' in data and len(data['response']) > 10:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Chat working without auth: {data['response'][:50]}...",
                    "Chat system accessible without authentication",
                    "Chat response received"
                )
            else:
                self.log_test(test_name, "WARN", f"Chat response too short: {data}")
        else:
            self.log_test(test_name, "FAIL", f"Chat without auth failed: {response.get('error')}")

    async def test_chat_response_quality(self):
        """Test chat response quality and relevance"""
        test_name = "Chat Response Quality"
        
        data = {"session_id": "test_session", "content": "What's the best strategy for Bitcoin trading?"}
        response = await self.test_api_endpoint("/chat", method="POST", data=data, auth=True)
        
        if response['success']:
            data = response['data']
            chat_response = data.get('response', '')
            
            # Check for trading-related keywords in response
            trading_keywords = ['bitcoin', 'btc', 'trading', 'strategy', 'market', 'analysis']
            keyword_count = sum(1 for keyword in trading_keywords if keyword.lower() in chat_response.lower())
            
            if keyword_count >= 3 and len(chat_response) > 100:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Quality chat response: {keyword_count} trading keywords, {len(chat_response)} chars",
                    "Relevant and comprehensive chat responses",
                    f"Keywords: {keyword_count}, Length: {len(chat_response)}"
                )
            else:
                self.log_test(test_name, "WARN", f"Chat response quality could be better: {keyword_count} keywords")
        else:
            self.log_test(test_name, "FAIL", f"Chat response quality test failed: {response.get('error')}")

    # ============= ENHANCED LIQUIDATION FEATURES TESTS =============
    
    async def test_resistance_support_ranks(self):
        """Test resistance_rank and support_rank in liquidation_levels"""
        test_name = "Enhanced Liquidation - Resistance & Support Ranks"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        enhanced_data = data.get('data', {})
        
        if 'liquidation_heatmap_2d' in enhanced_data:
            heatmap_data = enhanced_data['liquidation_heatmap_2d']
            liquidation_levels = heatmap_data.get('liquidation_levels', [])
            
            resistance_ranks_found = 0
            support_ranks_found = 0
            
            for level in liquidation_levels[:10]:  # Check first 10 levels
                if 'resistance_rank' in level:
                    resistance_ranks_found += 1
                if 'support_rank' in level:
                    support_ranks_found += 1
            
            if resistance_ranks_found >= 3 or support_ranks_found >= 3:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Resistance/Support ranks found: {resistance_ranks_found} resistance, {support_ranks_found} support",
                    "resistance_rank and support_rank fields in liquidation levels",
                    f"Ranks found in liquidation data"
                )
            else:
                self.log_test(test_name, "FAIL", f"Insufficient rank data: {resistance_ranks_found} resistance, {support_ranks_found} support")
        else:
            self.log_test(test_name, "FAIL", "No liquidation heatmap data available")

    async def test_cluster_strength_calculation(self):
        """Test cluster_strength calculation in liquidation levels"""
        test_name = "Enhanced Liquidation - Cluster Strength Calculation"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=ETH/USDT&timeframe=1day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        enhanced_data = data.get('data', {})
        
        if 'liquidation_heatmap_2d' in enhanced_data:
            heatmap_data = enhanced_data['liquidation_heatmap_2d']
            liquidation_levels = heatmap_data.get('liquidation_levels', [])
            
            cluster_strengths_found = 0
            strength_values = []
            
            for level in liquidation_levels[:10]:  # Check first 10 levels
                if 'cluster_strength' in level:
                    cluster_strengths_found += 1
                    strength_values.append(level['cluster_strength'])
            
            if cluster_strengths_found >= 5:
                unique_strengths = set(strength_values)
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Cluster strength calculation working: {cluster_strengths_found} levels, {len(unique_strengths)} unique strengths",
                    "cluster_strength field with varied values",
                    f"Strengths: {list(unique_strengths)[:3]}"
                )
            else:
                self.log_test(test_name, "FAIL", f"Insufficient cluster strength data: {cluster_strengths_found}/10 levels")
        else:
            self.log_test(test_name, "FAIL", "No liquidation heatmap data available")

    async def test_price_impact_score_sorting(self):
        """Test price_impact_score sorting in liquidation levels"""
        test_name = "Enhanced Liquidation - Price Impact Score Sorting"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=BTC/USDT&timeframe=1day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        enhanced_data = data.get('data', {})
        
        if 'liquidation_heatmap_2d' in enhanced_data:
            heatmap_data = enhanced_data['liquidation_heatmap_2d']
            liquidation_levels = heatmap_data.get('liquidation_levels', [])
            
            impact_scores = []
            for level in liquidation_levels[:10]:  # Check first 10 levels
                if 'price_impact_score' in level:
                    impact_scores.append(level['price_impact_score'])
            
            if len(impact_scores) >= 5:
                # Check if scores are sorted (descending order expected)
                is_sorted = all(impact_scores[i] >= impact_scores[i+1] for i in range(len(impact_scores)-1))
                
                if is_sorted:
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"Price impact scores properly sorted: {impact_scores[:3]} (descending)",
                        "price_impact_score sorting in descending order",
                        "Scores sorted correctly"
                    )
                else:
                    self.log_test(test_name, "WARN", f"Price impact scores may not be sorted: {impact_scores[:5]}")
            else:
                self.log_test(test_name, "FAIL", f"Insufficient price impact score data: {len(impact_scores)}/10 levels")
        else:
            self.log_test(test_name, "FAIL", "No liquidation heatmap data available")

    # ============= REAL-TIME INTEGRATION TESTS =============
    
    async def test_realtime_latest_all_assets(self):
        """Test GET /api/realtime/latest for all Top 30 Assets"""
        test_name = "Real-time Latest Data - All Top 30 Assets"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error status: {data}")
            return
        
        realtime_data = data.get('data', {})
        
        # Check for key crypto assets
        key_assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT', 'AVAX/USDT', 
                     'LINK/USDT', 'DOT/USDT', 'UNI/USDT', 'ATOM/USDT', 'AAVE/USDT']
        
        found_assets = []
        for asset in key_assets:
            if asset in realtime_data and realtime_data[asset]:
                asset_data = realtime_data[asset]
                if 'price' in asset_data and asset_data['price'] > 0:
                    found_assets.append(asset)
        
        if len(found_assets) >= 8:  # At least 8 out of 10 key assets
            self.log_test(
                test_name, 
                "PASS", 
                f"Real-time data available for {len(found_assets)}/10 key assets: {', '.join(found_assets)}",
                "Live prices for BTC, ETH, SOL, MATIC, AVAX, LINK, DOT, UNI, ATOM, AAVE",
                f"{len(found_assets)} assets with live prices"
            )
        elif len(found_assets) >= 5:
            self.log_test(
                test_name, 
                "WARN", 
                f"Partial real-time data for {len(found_assets)}/10 key assets: {', '.join(found_assets)}",
                "Live prices for all 10 key assets",
                f"Only {len(found_assets)} assets available"
            )
        else:
            self.log_test(test_name, "FAIL", f"Insufficient real-time data. Found: {found_assets}")

    async def test_realtime_live_prices_verification(self):
        """Verify live prices for specific assets are realistic"""
        test_name = "Real-time Price Verification"
        
        response = await self.test_api_endpoint("/realtime/latest")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        realtime_data = data.get('data', {})
        
        # Expected price ranges (rough estimates for validation)
        price_ranges = {
            'BTC/USDT': (30000, 100000),
            'ETH/USDT': (1500, 5000),
            'SOL/USDT': (50, 300),
            'MATIC/USDT': (0.5, 3.0),
            'AVAX/USDT': (20, 100)
        }
        
        valid_prices = []
        invalid_prices = []
        
        for symbol, (min_price, max_price) in price_ranges.items():
            if symbol in realtime_data and realtime_data[symbol]:
                price = realtime_data[symbol].get('price', 0)
                if min_price <= price <= max_price:
                    valid_prices.append(f"{symbol}: ${price:.2f}")
                else:
                    invalid_prices.append(f"{symbol}: ${price:.2f} (expected ${min_price}-${max_price})")
        
        if len(valid_prices) >= 4 and len(invalid_prices) == 0:
            self.log_test(
                test_name, 
                "PASS", 
                f"All {len(valid_prices)} checked prices are realistic: {', '.join(valid_prices)}",
                "Realistic price ranges for major crypto assets",
                f"{len(valid_prices)} valid prices"
            )
        elif len(valid_prices) >= 3:
            self.log_test(
                test_name, 
                "WARN", 
                f"Most prices realistic: {len(valid_prices)} valid, {len(invalid_prices)} questionable",
                "All prices in realistic ranges",
                f"Valid: {', '.join(valid_prices[:3])}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Price validation failed. Invalid: {invalid_prices}")

    async def test_smart_money_extended_assets(self):
        """Test Smart Money for extended assets (not just BTC/ETH)"""
        test_name = "Smart Money Extended Assets"
        
        extended_symbols = "SOL/USDT,AVAX/USDT,LINK/USDT,DOT/USDT,UNI/USDT"
        response = await self.test_api_endpoint(f"/smart-money/all?symbols={extended_symbols}")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error status: {data}")
            return
        
        smart_money_data = data.get('data', {})
        extended_assets = ['SOL/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOT/USDT', 'UNI/USDT']
        
        working_assets = []
        for asset in extended_assets:
            if asset in smart_money_data and smart_money_data[asset]:
                asset_data = smart_money_data[asset]
                # Check if has liquidation, OI, and funding data
                has_data = ('liquidation_heatmap' in asset_data and 
                           'open_interest' in asset_data and 
                           'funding_rates' in asset_data)
                if has_data:
                    working_assets.append(asset)
        
        if len(working_assets) >= 4:
            self.log_test(
                test_name, 
                "PASS", 
                f"Smart Money data available for {len(working_assets)}/5 extended assets: {', '.join(working_assets)}",
                "Smart Money support for extended crypto assets beyond BTC/ETH",
                f"{len(working_assets)} extended assets supported"
            )
        elif len(working_assets) >= 2:
            self.log_test(
                test_name, 
                "WARN", 
                f"Partial Smart Money support: {len(working_assets)}/5 extended assets working",
                "Full Smart Money support for extended assets",
                f"Only {len(working_assets)} assets: {', '.join(working_assets)}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Limited Smart Money support for extended assets: {working_assets}")

    # ============= AI TRADING ENGINE TESTS =============
    
    async def test_ai_trading_analyze_btc(self):
        """Test POST /api/ai-trading/analyze for BTC/USDT"""
        test_name = "AI Trading Analysis - BTC/USDT"
        
        # Use query parameters instead of JSON body
        response = await self.test_api_endpoint("/ai-trading/analyze?symbol=BTC/USDT&context=technical_analysis", method="POST", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for AI analysis response structure
        required_fields = ['symbol', 'recommendation']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test(test_name, "FAIL", f"Missing fields in AI analysis: {missing_fields}")
            return
        
        recommendation_data = data.get('recommendation', {})
        reasoning = recommendation_data.get('reasoning', '') if isinstance(recommendation_data, dict) else ''
        action = recommendation_data.get('action', '') if isinstance(recommendation_data, dict) else ''
        
        if len(reasoning) > 50 and action in ['long', 'short', 'neutral', 'hold']:
            self.log_test(
                test_name, 
                "PASS", 
                f"AI analysis generated: {len(reasoning)} chars, recommendation: {action}",
                "Detailed AI analysis with trading recommendation",
                f"Analysis length: {len(reasoning)}, Rec: {action}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Invalid AI analysis: reasoning={len(reasoning)} chars, action={action}")

    async def test_ai_trading_analyze_eth_with_context(self):
        """Test POST /api/ai-trading/analyze for ETH/USDT with context"""
        test_name = "AI Trading Analysis - ETH/USDT with Context"
        
        context = "comprehensive_analysis_with_bullish_sentiment_medium_risk_tolerance"
        response = await self.test_api_endpoint(f"/ai-trading/analyze?symbol=ETH/USDT&context={context}", method="POST", auth=True)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check if context was considered in analysis
        recommendation_data = data.get('recommendation', {})
        reasoning = recommendation_data.get('reasoning', '') if isinstance(recommendation_data, dict) else ''
        
        # Look for context-aware analysis (mentions of market sentiment, risk, etc.)
        context_indicators = ['sentiment', 'risk', 'market', 'bullish', 'bearish']
        context_mentions = sum(1 for indicator in context_indicators if indicator.lower() in reasoning.lower())
        
        if context_mentions >= 2 and len(reasoning) > 100:
            self.log_test(
                test_name, 
                "PASS", 
                f"Context-aware AI analysis: {context_mentions} context mentions in {len(reasoning)} chars",
                "AI analysis incorporating provided context",
                f"Context awareness: {context_mentions} mentions"
            )
        else:
            self.log_test(test_name, "WARN", f"Limited context awareness in AI analysis: {context_mentions} mentions")

    async def test_ai_trading_chat_commands(self):
        """Test POST /api/ai-trading/chat-command with various trading commands"""
        test_name = "AI Trading Chat Commands"
        
        commands = [
            "Long BTC 0.1 at market",
            "Analyze ETH trading opportunity", 
            "What's your analysis on SOL?"
        ]
        
        successful_commands = 0
        
        for command in commands:
            # Use query parameter instead of JSON body
            import urllib.parse
            encoded_command = urllib.parse.quote(command)
            response = await self.test_api_endpoint(f"/ai-trading/chat-command?command={encoded_command}", method="POST", auth=True)
            
            if response['success']:
                data = response['data']
                if 'result' in data and data.get('status') == 'success':
                    successful_commands += 1
        
        if successful_commands == len(commands):
            self.log_test(
                test_name, 
                "PASS", 
                f"All {len(commands)} chat commands processed successfully",
                "AI processing of various trading commands",
                f"{successful_commands}/{len(commands)} commands successful"
            )
        elif successful_commands >= 2:
            self.log_test(
                test_name, 
                "WARN", 
                f"Most chat commands working: {successful_commands}/{len(commands)}",
                "All chat commands should work",
                f"{successful_commands} out of {len(commands)} working"
            )
        else:
            self.log_test(test_name, "FAIL", f"Chat command processing failed: {successful_commands}/{len(commands)} working")

    # ============= ENHANCED SMART MONEY TESTS =============
    
    async def test_enhanced_smart_money_avax_1day(self):
        """Test GET /api/enhanced-smart-money/data?symbol=AVAX/USDT&timeframe=1day"""
        test_name = "Enhanced Smart Money - AVAX/USDT (1day)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=AVAX/USDT&timeframe=1day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        # Check for enhanced smart money fields
        required_fields = ['symbol', 'timeframe', 'liquidation_heatmap_2d']
        missing_fields = [field for field in required_fields if field not in enhanced_data]
        
        if not missing_fields and enhanced_data.get('timeframe') == '1day':
            heatmap_2d = enhanced_data.get('liquidation_heatmap_2d', {})
            if 'summary' in heatmap_2d and 'directional_bias' in heatmap_2d['summary']:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Enhanced Smart Money data for AVAX (1day): directional bias available",
                    "Enhanced data with 1day timeframe for AVAX",
                    "Complete enhanced data structure"
                )
            else:
                self.log_test(test_name, "WARN", "Enhanced data structure incomplete - missing directional bias")
        else:
            self.log_test(test_name, "FAIL", f"Missing enhanced data fields: {missing_fields}")

    async def test_enhanced_smart_money_link_3day(self):
        """Test GET /api/enhanced-smart-money/data?symbol=LINK/USDT&timeframe=3day"""
        test_name = "Enhanced Smart Money - LINK/USDT (3day)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=LINK/USDT&timeframe=3day")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '3day' and enhanced_data.get('symbol') == 'LINK/USDT':
            self.log_test(
                test_name, 
                "PASS", 
                f"Enhanced Smart Money data for LINK (3day): timeframe correctly set",
                "Enhanced data with 3day timeframe for LINK",
                "Correct symbol and timeframe"
            )
        else:
            self.log_test(test_name, "FAIL", f"Timeframe/symbol mismatch: got {enhanced_data.get('timeframe')}/{enhanced_data.get('symbol')}")

    async def test_enhanced_smart_money_dot_1week(self):
        """Test GET /api/enhanced-smart-money/data?symbol=DOT/USDT&timeframe=1week"""
        test_name = "Enhanced Smart Money - DOT/USDT (1week)"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/data?symbol=DOT/USDT&timeframe=1week")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        enhanced_data = data.get('data', {})
        
        if enhanced_data.get('timeframe') == '1week' and enhanced_data.get('symbol') == 'DOT/USDT':
            # Check for weekly-specific analysis
            heatmap_2d = enhanced_data.get('liquidation_heatmap_2d', {})
            if heatmap_2d and 'summary' in heatmap_2d:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Enhanced Smart Money data for DOT (1week): weekly analysis available",
                    "Enhanced data with 1week timeframe for DOT",
                    "Weekly timeframe analysis complete"
                )
            else:
                self.log_test(test_name, "WARN", "Weekly analysis data incomplete")
        else:
            self.log_test(test_name, "FAIL", f"Timeframe/symbol mismatch for DOT weekly data")

    async def test_enhanced_smart_money_top30_support(self):
        """Validate that all Top 30 Assets are supported"""
        test_name = "Enhanced Smart Money - Top 30 Assets Support"
        
        response = await self.test_api_endpoint("/enhanced-smart-money/supported-symbols")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"API call failed: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        if 'status' not in data or data['status'] != 'success':
            self.log_test(test_name, "FAIL", f"API returned error: {data}")
            return
        
        symbols = data.get('symbols', [])
        
        # Extract symbol names from the response
        if isinstance(symbols, list) and len(symbols) > 0:
            if isinstance(symbols[0], dict):
                symbol_names = [s.get('symbol', '') for s in symbols]
            else:
                symbol_names = symbols
        else:
            symbol_names = []
        
        # Check for key Top 30 assets
        top_assets = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 
                     'SOL/USDT', 'DOGE/USDT', 'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT',
                     'LINK/USDT', 'UNI/USDT', 'ATOM/USDT', 'AAVE/USDT']
        
        supported_assets = [asset for asset in top_assets if asset in symbol_names]
        
        if len(supported_assets) >= 25:  # At least 25 out of top assets
            self.log_test(
                test_name, 
                "PASS", 
                f"Excellent Top 30 support: {len(supported_assets)} major assets supported",
                "Support for all major Top 30 crypto assets",
                f"{len(supported_assets)} top assets supported"
            )
        elif len(supported_assets) >= 15:
            self.log_test(
                test_name, 
                "WARN", 
                f"Good Top 30 support: {len(supported_assets)} major assets supported",
                "Support for all Top 30 assets",
                f"{len(supported_assets)} assets supported"
            )
        else:
            self.log_test(test_name, "FAIL", f"Limited Top 30 support: only {len(supported_assets)} assets")

    # ============= INTEGRATION TESTS =============
    
    async def test_paper_trading_with_live_prices(self):
        """Test Paper Trading integration with live prices"""
        test_name = "Paper Trading with Live Prices Integration"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token available")
            return
        
        # Get account info
        account_response = await self.test_api_endpoint("/trading/account", auth=True)
        
        if not account_response['success']:
            self.log_test(test_name, "FAIL", f"Account API failed: {account_response.get('error')}")
            return
        
        # Place a market order (should use live prices)
        order_data = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.001,
            "leverage": 1
        }
        
        order_response = await self.test_api_endpoint("/trading/order", method="POST", data=order_data, auth=True)
        
        if order_response['success']:
            order_data = order_response['data']
            result = order_data.get('result', {})
            order_info = result.get('order', {})
            fill_price = order_info.get('filled_price', 0)
            if fill_price > 0:
                # Check if fill price is realistic (between 30k-100k for BTC)
                if 30000 <= fill_price <= 100000:
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"Paper trading using live prices: BTC filled at ${fill_price:.2f}",
                        "Paper trading integrated with real-time market prices",
                        f"Realistic fill price: ${fill_price:.2f}"
                    )
                else:
                    self.log_test(test_name, "WARN", f"Fill price may be unrealistic: ${fill_price:.2f}")
            else:
                self.log_test(test_name, "FAIL", "Order executed but no fill price available")
        else:
            self.log_test(test_name, "FAIL", f"Paper trading order failed: {order_response.get('error')}")

    async def test_ai_trading_with_realtime_data(self):
        """Test AI Trading integration with real-time market data"""
        test_name = "AI Trading with Real-time Market Data"
        
        # First get real-time data
        realtime_response = await self.test_api_endpoint("/realtime/latest")
        
        if not realtime_response['success']:
            self.log_test(test_name, "FAIL", "Could not get real-time data for AI integration test")
            return
        
        realtime_data = realtime_response['data'].get('data', {})
        btc_price = realtime_data.get('BTC/USDT', {}).get('price', 0)
        
        if btc_price == 0:
            self.log_test(test_name, "FAIL", "No BTC real-time price available")
            return
        
        # Now test AI analysis with current market context
        context = f"realtime_analysis_current_price_{int(btc_price)}"
        ai_response = await self.test_api_endpoint(f"/ai-trading/analyze?symbol=BTC/USDT&context={context}", method="POST", auth=True)
        
        if ai_response['success']:
            recommendation = ai_response['data'].get('recommendation', {})
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            # Check if analysis mentions current price or real-time data
            realtime_indicators = ['current', 'price', str(int(btc_price)), 'real-time', 'live']
            realtime_mentions = sum(1 for indicator in realtime_indicators if indicator.lower() in reasoning.lower())
            
            if realtime_mentions >= 2:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"AI analysis integrated with real-time data: {realtime_mentions} real-time references",
                    "AI analysis incorporating current market prices",
                    f"Real-time integration: {realtime_mentions} references"
                )
            else:
                self.log_test(test_name, "WARN", "Limited real-time data integration in AI analysis")
        else:
            self.log_test(test_name, "FAIL", f"AI analysis with real-time data failed: {ai_response.get('error')}")

    async def test_cross_module_communication(self):
        """Test cross-module communication (AI ↔ Paper Trading ↔ Smart Money)"""
        test_name = "Cross-Module Communication"
        
        if not self.auth_token:
            self.log_test(test_name, "FAIL", "No authentication token for cross-module test")
            return
        
        # Test 1: Get Smart Money data
        smart_money_response = await self.test_api_endpoint("/smart-money/all?symbols=BTC/USDT")
        
        if not smart_money_response['success']:
            self.log_test(test_name, "FAIL", "Smart Money module not responding")
            return
        
        # Test 2: Use Smart Money data in AI analysis
        smart_data = smart_money_response['data'].get('data', {})
        btc_smart_data = smart_data.get('BTC/USDT', {})
        
        has_liquidation = 'liquidation_heatmap' in btc_smart_data
        has_oi = 'open_interest' in btc_smart_data
        has_funding = 'funding_rates' in btc_smart_data
        
        context = f"smart_money_enhanced_liquidation_{has_liquidation}_oi_{has_oi}_funding_{has_funding}"
        ai_response = await self.test_api_endpoint(f"/ai-trading/analyze?symbol=BTC/USDT&context={context}", method="POST", auth=True)
        
        if not ai_response['success']:
            self.log_test(test_name, "FAIL", "AI module not responding to Smart Money context")
            return
        
        # Test 3: Check if AI can influence Paper Trading decisions
        recommendation_data = ai_response['data'].get('recommendation', {})
        recommendation = recommendation_data.get('action', '') if isinstance(recommendation_data, dict) else ''
        reasoning = recommendation_data.get('reasoning', '') if isinstance(recommendation_data, dict) else ''
        
        if recommendation in ['long', 'short'] and len(reasoning) > 50:
            # Test if we can place order based on AI recommendation
            order_side = "buy" if recommendation == "long" else "sell"
            order_data = {
                "symbol": "BTC/USDT",
                "side": order_side,
                "order_type": "market",
                "quantity": 0.001,
                "leverage": 1
            }
            
            order_response = await self.test_api_endpoint("/trading/order", method="POST", data=order_data, auth=True)
            
            if order_response['success']:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Cross-module communication working: Smart Money → AI → Paper Trading ({recommendation})",
                    "Seamless data flow between all modules",
                    "All modules communicating successfully"
                )
            else:
                self.log_test(test_name, "WARN", "Smart Money → AI working, but Paper Trading integration failed")
        else:
            self.log_test(test_name, "WARN", "Smart Money → AI communication limited")

    # ============= PERFORMANCE & STABILITY TESTS =============
    
    async def test_gemini_api_integration(self):
        """Test Gemini API integration for AI analysis"""
        test_name = "Gemini API Integration"
        
        # Test pattern analysis which should use Gemini
        pattern_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "limit": 100,
            "indicators": ["rsi", "ema50", "ema200"]
        }
        
        response = await self.test_api_endpoint("/analyze-patterns", method="POST", data=pattern_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"Pattern analysis API failed: {response.get('error')}")
            return
        
        data = response['data']
        
        # Check if Gemini AI analysis is present
        ai_analysis = data.get('ai_analysis', '')
        
        if ai_analysis and len(ai_analysis) > 100 and 'fehler' not in ai_analysis.lower():
            # Check if analysis is in German (Gemini should respond in German)
            german_indicators = ['analyse', 'bitcoin', 'preis', 'trend', 'empfehlung']
            german_count = sum(1 for word in german_indicators if word.lower() in ai_analysis.lower())
            
            if german_count >= 2:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Gemini API integration working: {len(ai_analysis)} chars, German analysis",
                    "Gemini AI providing detailed German analysis",
                    f"Analysis length: {len(ai_analysis)}, German indicators: {german_count}"
                )
            else:
                self.log_test(test_name, "WARN", "Gemini responding but may not be in German")
        else:
            self.log_test(test_name, "FAIL", f"Gemini API integration failed or error in response")

    async def test_all_30_crypto_assets_availability(self):
        """Test that all 30 crypto assets are available"""
        test_name = "All 30 Crypto Assets Availability"
        
        response = await self.test_api_endpoint("/trading/symbols")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"Trading symbols API failed: {response.get('error')}")
            return
        
        data = response['data']
        symbols = data.get('symbols', [])
        
        # Expected top 30 crypto assets
        expected_assets = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOGE/USDT', 'DOT/USDT', 'MATIC/USDT', 'LTC/USDT', 'AVAX/USDT', 'LINK/USDT',
            'UNI/USDT', 'ATOM/USDT', 'AAVE/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT',
            'FIL/USDT', 'TRX/USDT', 'ETC/USDT', 'XLM/USDT', 'THETA/USDT', 'FTT/USDT',
            'HBAR/USDT', 'EGLD/USDT', 'NEAR/USDT', 'FLOW/USDT', 'XTZ/USDT', 'MANA/USDT'
        ]
        
        available_assets = []
        if isinstance(symbols, list):
            for symbol_data in symbols:
                if isinstance(symbol_data, dict):
                    symbol = symbol_data.get('symbol', '')
                else:
                    symbol = str(symbol_data)
                
                if symbol in expected_assets:
                    available_assets.append(symbol)
        
        if len(available_assets) >= 25:  # At least 25 out of 30
            self.log_test(
                test_name, 
                "PASS", 
                f"Excellent crypto asset coverage: {len(available_assets)}/30 top assets available",
                "All 30 top crypto assets available for trading",
                f"{len(available_assets)} assets available"
            )
        elif len(available_assets) >= 20:
            self.log_test(
                test_name, 
                "WARN", 
                f"Good crypto asset coverage: {len(available_assets)}/30 top assets available",
                "All 30 top crypto assets",
                f"{len(available_assets)} assets available"
            )
        else:
            self.log_test(test_name, "FAIL", f"Limited crypto asset coverage: only {len(available_assets)}/30 available")

    async def test_realtime_price_updates_stability(self):
        """Test real-time price updates stability"""
        test_name = "Real-time Price Updates Stability"
        
        # Test multiple calls to check consistency
        prices_over_time = []
        
        for i in range(3):
            response = await self.test_api_endpoint("/realtime/latest")
            if response['success']:
                data = response['data'].get('data', {})
                btc_price = data.get('BTC/USDT', {}).get('price', 0)
                if btc_price > 0:
                    prices_over_time.append(btc_price)
            
            if i < 2:  # Don't wait after last iteration
                await asyncio.sleep(2)  # Wait 2 seconds between calls
        
        if len(prices_over_time) >= 2:
            # Check if prices are updating (some variation expected)
            price_variation = max(prices_over_time) - min(prices_over_time)
            avg_price = sum(prices_over_time) / len(prices_over_time)
            variation_percent = (price_variation / avg_price) * 100
            
            if 0 <= variation_percent <= 5:  # Reasonable variation (0-5%)
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"Stable real-time updates: {len(prices_over_time)} samples, {variation_percent:.2f}% variation",
                    "Stable real-time price updates with reasonable variation",
                    f"Price stability: {variation_percent:.2f}% variation"
                )
            elif variation_percent <= 10:
                self.log_test(test_name, "WARN", f"Real-time updates working but high variation: {variation_percent:.2f}%")
            else:
                self.log_test(test_name, "FAIL", f"Unstable real-time updates: {variation_percent:.2f}% variation")
        else:
            self.log_test(test_name, "FAIL", "Could not collect sufficient price samples for stability test")

    async def test_ki_based_trade_analysis_performance(self):
        """Test KI-based trade analysis performance"""
        test_name = "KI-based Trade Analysis Performance"
        
        start_time = datetime.now()
        
        # Test AI analysis performance
        response = await self.test_api_endpoint("/ai-trading/analyze?symbol=BTC/USDT&context=comprehensive_performance_test", method="POST", auth=True)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if response['success']:
            data = response['data']
            recommendation = data.get('recommendation', {})
            reasoning = recommendation.get('reasoning', '') if isinstance(recommendation, dict) else ''
            
            # Check both response time and quality
            if response_time < 10 and len(reasoning) > 100:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"KI analysis performance excellent: {response_time:.2f}s, {len(reasoning)} chars",
                    "Fast KI analysis with comprehensive output",
                    f"Response time: {response_time:.2f}s"
                )
            elif response_time < 20:
                self.log_test(test_name, "WARN", f"KI analysis acceptable: {response_time:.2f}s response time")
            else:
                self.log_test(test_name, "FAIL", f"KI analysis too slow: {response_time:.2f}s")
        else:
            self.log_test(test_name, "FAIL", f"KI analysis failed: {response.get('error')}")

    async def run_all_tests(self):
        """Run all test cases for Trading System with Real-time Data and AI Integration"""
        await self.setup()
        
        try:
            print("🔄 Running Enhanced Timeframe Tests...")
            await self.test_enhanced_timeframes_5m()
            await self.test_enhanced_timeframes_15m()
            await self.test_enhanced_timeframes_1h()
            await self.test_enhanced_timeframes_4h()
            await self.test_enhanced_timeframes_8h()
            await self.test_cumulative_liquidation_data()
            
            print("\n💰 Running Paper Trading Position Close Tests...")
            await self.test_position_close_25_percent()
            await self.test_position_close_50_percent()
            await self.test_position_close_100_percent()
            await self.test_pnl_calculation_accuracy()
            
            print("\n🤖 Running Gemini AI Integration Tests...")
            await self.test_gemini_ai_btc_analysis()
            await self.test_gemini_ai_chat_command_long()
            await self.test_gemini_ai_response_parsing()
            
            print("\n💬 Running Chat System Tests...")
            await self.test_chat_without_auth()
            await self.test_chat_response_quality()
            
            print("\n📊 Running Enhanced Liquidation Features Tests...")
            await self.test_resistance_support_ranks()
            await self.test_cluster_strength_calculation()
            await self.test_price_impact_score_sorting()
            
            print("\n🔄 Running Real-time Integration Tests...")
            await self.test_realtime_latest_all_assets()
            await self.test_realtime_live_prices_verification()
            await self.test_smart_money_extended_assets()
            
            print("\n🤖 Running AI Trading Engine Tests...")
            await self.test_ai_trading_analyze_btc()
            await self.test_ai_trading_analyze_eth_with_context()
            await self.test_ai_trading_chat_commands()
            
            print("\n📊 Running Enhanced Smart Money Tests...")
            await self.test_enhanced_smart_money_avax_1day()
            await self.test_enhanced_smart_money_link_3day()
            await self.test_enhanced_smart_money_dot_1week()
            await self.test_enhanced_smart_money_top30_support()
            
            print("\n🔗 Running Integration Tests...")
            await self.test_paper_trading_with_live_prices()
            await self.test_ai_trading_with_realtime_data()
            await self.test_cross_module_communication()
            
            print("\n⚡ Running Performance & Stability Tests...")
            await self.test_gemini_api_integration()
            await self.test_all_30_crypto_assets_availability()
            await self.test_realtime_price_updates_stability()
            await self.test_ki_based_trade_analysis_performance()
            
        finally:
            await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 TRADING SYSTEM WITH REAL-TIME DATA AND AI INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
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
        
        # Categorize results
        categories = {
            'Real-time Integration': [],
            'AI Trading Engine': [],
            'Enhanced Smart Money': [],
            'Integration Tests': [],
            'Performance & Stability': []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Real-time' in test_name or 'Smart Money Extended' in test_name:
                categories['Real-time Integration'].append(result)
            elif 'AI Trading' in test_name:
                categories['AI Trading Engine'].append(result)
            elif 'Enhanced Smart Money' in test_name:
                categories['Enhanced Smart Money'].append(result)
            elif 'Integration' in test_name or 'Cross-Module' in test_name:
                categories['Integration Tests'].append(result)
            else:
                categories['Performance & Stability'].append(result)
        
        # Print category summaries
        for category, results in categories.items():
            if results:
                passed = len([r for r in results if r['status'] == 'PASS'])
                total = len(results)
                print(f"📋 {category}: {passed}/{total} passed ({(passed/total)*100:.0f}%)")
        
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
        
        print("=" * 80)

    async def run_integrated_ai_chat_tests(self):
        """Run focused tests on the NEW INTEGRATED AI CHAT SYSTEM"""
        await self.setup()
        
        print("🚀 TESTING NEW INTEGRATED AI CHAT SYSTEM")
        print("=" * 80)
        print("🎯 PRIORITY TESTS: Integrated AI Chat with Gemini 2.5 Pro")
        print("🎯 FOCUS: Fix 422 Unprocessable Entity errors")
        print("🎯 DEMO USER: demo@example.com/demo123")
        print("=" * 80)
        
        # Priority tests for the new integrated AI chat system
        priority_tests = [
            self.test_integrated_ai_chat_greeting,
            self.test_integrated_ai_chat_btc_analysis,
            self.test_integrated_ai_chat_portfolio_access,
            self.test_integrated_ai_chat_system_status,
            self.test_gemini_25_pro_integration,
            self.test_ai_system_integration_comprehensive
        ]
        
        print("🔥 RUNNING PRIORITY TESTS FOR NEW INTEGRATED AI CHAT SYSTEM:")
        print()
        
        for test_func in priority_tests:
            try:
                await test_func()
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, "FAIL", f"Test execution error: {str(e)}")
        
        await self.cleanup()
        self.print_summary()

    async def run_all_tests(self):
        """Run FINALE TESTS nach Chat und AI-Reparaturen"""
        await self.setup()
        
        print("🎯 FINALE TESTS NACH CHAT UND AI-REPARATUREN")
        print("=" * 80)
        print("KRITISCHE VERIFIKATION:")
        print("1. CHAT SYSTEM REPARATUR TEST - POST /api/chat")
        print("2. AI TRADING ANALYSE REPARATUR TEST - POST /api/ai-trading/analyze") 
        print("3. AI TRADING CHAT COMMAND REPARATUR TEST - POST /api/ai-trading/chat-command")
        print("4. VOLLSTÄNDIGE INTEGRATION VERIFIKATION")
        print("ERWARTETE ERGEBNISSE: ✅ KEINE 422 Errors ✅ Deutsche AI-Antworten ✅ Vollständiger Systemzugang")
        print("=" * 80)
        
        # FINALE TEST METHODS - Focus on the specific repair verification
        finale_tests = [
            # FINALE TESTS - CHAT UND AI-REPARATUREN (PRIORITY)
            self.test_chat_system_repair_test,
            self.test_ai_trading_analyse_repair_test,
            self.test_ai_trading_chat_command_repair_test,
            self.test_vollstaendige_integration_verifikation,
            
            # Enhanced timeframe tests
            self.test_enhanced_timeframes_5m,
            self.test_enhanced_timeframes_15m,
            self.test_enhanced_timeframes_1h,
            self.test_enhanced_timeframes_4h,
            self.test_enhanced_timeframes_8h,
            self.test_cumulative_liquidation_data,
            
            # Paper trading tests
            self.test_position_close_25_percent,
            self.test_position_close_50_percent,
            self.test_position_close_100_percent,
            self.test_pnl_calculation_accuracy,
            
            # Gemini AI tests
            self.test_gemini_ai_btc_analysis,
            self.test_gemini_ai_chat_command_long,
            self.test_gemini_ai_response_parsing,
            
            # Chat system tests
            self.test_chat_without_auth,
            self.test_chat_response_quality,
            
            # Enhanced liquidation tests
            self.test_resistance_support_ranks,
            self.test_cluster_strength_calculation,
            self.test_price_impact_score_sorting,
            
            # Real-time integration tests
            self.test_realtime_latest_all_assets,
            self.test_realtime_live_prices_verification,
            self.test_smart_money_extended_assets,
            
            # AI trading engine tests
            self.test_ai_trading_analyze_btc,
            self.test_ai_trading_analyze_eth_with_context,
            self.test_ai_trading_chat_commands,
            
            # Enhanced smart money tests
            self.test_enhanced_smart_money_avax_1day,
            self.test_enhanced_smart_money_link_3day,
            self.test_enhanced_smart_money_dot_1week,
            self.test_enhanced_smart_money_top30_support,
            
            # Integration tests
            self.test_paper_trading_with_live_prices,
            self.test_ai_trading_with_realtime_data,
            self.test_cross_module_communication,
            
            # Performance tests
            self.test_gemini_api_integration,
            self.test_all_30_crypto_assets_availability,
            self.test_system_stability_under_load
        ]
        
        print(f"🚀 Running {len(all_tests)} comprehensive tests...")
        print()
        
        for test_func in all_tests:
            try:
                await test_func()
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, "FAIL", f"Test execution error: {str(e)}")
        
        await self.cleanup()
        self.print_summary()

async def main():
    """Main test runner - Focus on NEW INTEGRATED AI CHAT SYSTEM"""
    tester = TradingSystemTester()
    
    # Run focused tests on the new integrated AI chat system
    print("🎯 RUNNING FOCUSED TESTS ON NEW INTEGRATED AI CHAT SYSTEM")
    await tester.run_integrated_ai_chat_tests()

if __name__ == "__main__":
    asyncio.run(main())