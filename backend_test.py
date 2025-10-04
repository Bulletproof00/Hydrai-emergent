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
BACKEND_URL = "https://liquidation-oracle.preview.emergentagent.com/api"
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
        """Setup test user for authenticated endpoints"""
        try:
            # Try to login with existing test user
            login_data = {
                "email": "trader@example.com",
                "password": "password123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    print("✅ Logged in with existing test user")
                    return
                    
            # If login fails, register new user
            register_data = {
                "email": "trader@example.com",
                "username": "testtrader",
                "password": "password123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=register_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    print("✅ Registered new test user")
                else:
                    print("⚠️ Could not setup test user - some tests may fail")
                    
        except Exception as e:
            print(f"⚠️ Error setting up test user: {e}")
    
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
        required_fields = ['symbol', 'analysis', 'recommendation']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test(test_name, "FAIL", f"Missing fields in AI analysis: {missing_fields}")
            return
        
        analysis = data.get('analysis', '')
        recommendation = data.get('recommendation', '')
        
        if len(analysis) > 50 and recommendation in ['long', 'short', 'neutral', 'hold']:
            self.log_test(
                test_name, 
                "PASS", 
                f"AI analysis generated: {len(analysis)} chars, recommendation: {recommendation}",
                "Detailed AI analysis with trading recommendation",
                f"Analysis length: {len(analysis)}, Rec: {recommendation}"
            )
        else:
            self.log_test(test_name, "FAIL", f"Invalid AI analysis: analysis={len(analysis)} chars, rec={recommendation}")

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
        analysis = data.get('analysis', '')
        
        # Look for context-aware analysis (mentions of market sentiment, risk, etc.)
        context_indicators = ['sentiment', 'risk', 'market', 'bullish', 'bearish']
        context_mentions = sum(1 for indicator in context_indicators if indicator.lower() in analysis.lower())
        
        if context_mentions >= 2 and len(analysis) > 100:
            self.log_test(
                test_name, 
                "PASS", 
                f"Context-aware AI analysis: {context_mentions} context mentions in {len(analysis)} chars",
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
            if 'fill_price' in order_data and order_data['fill_price'] > 0:
                # Check if fill price is realistic (between 30k-100k for BTC)
                fill_price = order_data['fill_price']
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
        analysis = ai_response['data'].get('analysis', '')
        recommendation = ai_response['data'].get('recommendation', '')
        
        if recommendation in ['long', 'short'] and len(analysis) > 50:
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
        analyze_data = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "analysis_type": "comprehensive"
        }
        
        response = await self.test_api_endpoint("/ai-trading/analyze", method="POST", data=analyze_data, auth=True)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if response['success']:
            data = response['data']
            analysis = data.get('analysis', '')
            
            # Check both response time and quality
            if response_time < 10 and len(analysis) > 100:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"KI analysis performance excellent: {response_time:.2f}s, {len(analysis)} chars",
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
            print("🔄 Running Real-time Integration Tests...")
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

async def main():
    """Main test runner"""
    tester = TradingSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())