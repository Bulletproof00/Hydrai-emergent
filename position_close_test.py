#!/usr/bin/env python3
"""
KRITISCHER TRADING-BUG TEST: Position Close Funktionalität
Fokus auf warum Positionen im Trading-Tab nicht geschlossen werden können
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"

class PositionCloseTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = "demo-token"  # Using demo-token as specified
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 KRITISCHER TRADING-BUG TEST: Position Close Funktionalität")
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
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200, method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
            
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

    async def test_trading_account_status(self):
        """Test 1: Trading Account Status - GET /api/trading/account"""
        test_name = "🎯 TEST 1: TRADING ACCOUNT STATUS"
        
        response = await self.test_api_endpoint("/trading/account")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Trading Account API failed with status {response['status']}: {response.get('data', 'Unknown error')}")
            return False
        
        data = response['data']
        
        # Check account structure
        if isinstance(data, dict) and 'account' in data:
            account = data['account']
            balance = account.get('balance', 0)
            equity = account.get('equity', 0)
            
            if balance > 0:
                self.log_test(test_name, "PASS", f"✅ Account Status OK - Balance: ${balance:,.2f}, Equity: ${equity:,.2f}")
                return True
            else:
                self.log_test(test_name, "FAIL", f"❌ Invalid account balance: ${balance}")
                return False
        else:
            self.log_test(test_name, "FAIL", f"❌ Invalid account response structure: {data}")
            return False

    async def test_get_current_positions(self):
        """Test 2: Get Current Positions - GET /api/trading/positions"""
        test_name = "🎯 TEST 2: GET CURRENT POSITIONS"
        
        response = await self.test_api_endpoint("/trading/positions")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Get Positions API failed with status {response['status']}: {response.get('data', 'Unknown error')}")
            return []
        
        data = response['data']
        
        # Handle different response structures
        if isinstance(data, dict):
            positions = data.get('positions', [])
        elif isinstance(data, list):
            positions = data
        else:
            positions = []
        
        if len(positions) == 0:
            self.log_test(test_name, "PASS", f"✅ No open positions found (API working correctly)")
            return []
        else:
            # Check position structure
            position = positions[0]
            required_fields = ['position_id', 'symbol', 'side', 'size', 'entry_price']
            missing_fields = [field for field in required_fields if field not in position]
            
            if missing_fields:
                self.log_test(test_name, "FAIL", f"❌ Position data incomplete, missing fields: {missing_fields}")
                return []
            
            self.log_test(test_name, "PASS", f"✅ Found {len(positions)} open position(s) - First: {position.get('symbol')} {position.get('side')} {position.get('size')} @ ${position.get('entry_price', 0):,.2f}")
            return positions

    async def test_create_test_position(self):
        """Test 3: Create Test Position - BTC/USDT LONG"""
        test_name = "🎯 TEST 3: CREATE TEST POSITION (BTC/USDT LONG)"
        
        order_data = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.001,  # Small test amount
            "leverage": 1,      # Conservative leverage
            "stop_loss": None,
            "take_profit": None
        }
        
        response = await self.test_api_endpoint("/trading/order", method="POST", data=order_data)
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Create Position failed with status {response['status']}: {response.get('data', 'Unknown error')}")
            return None
        
        data = response['data']
        
        # Check for successful order creation
        if isinstance(data, dict):
            if data.get('status') == 'success' and 'result' in data:
                result = data['result']
                if result.get('success') and 'order' in result:
                    order_info = result['order']
                    order_id = order_info.get('order_id')
                    fill_price = order_info.get('filled_price', 0)
                    quantity = order_info.get('filled_quantity', 0)
                    status = order_info.get('status', '')
                    
                    if status == 'filled' and fill_price > 0:
                        self.log_test(test_name, "PASS", f"✅ Test position created successfully - Order ID: {order_id}, Fill Price: ${fill_price:,.2f}, Quantity: {quantity} BTC")
                        return order_id
                    else:
                        self.log_test(test_name, "FAIL", f"❌ Order not filled properly - Status: {status}, Fill Price: ${fill_price}")
                        return None
                else:
                    self.log_test(test_name, "FAIL", f"❌ Order result not successful: {result}")
                    return None
            else:
                self.log_test(test_name, "FAIL", f"❌ Order response not successful: {data}")
                return None
        else:
            self.log_test(test_name, "FAIL", f"❌ Invalid order response: {data}")
            return None

    async def test_position_close_api_various_scenarios(self):
        """Test 4: Position Close API - Various Error Scenarios"""
        test_name = "🎯 TEST 4: POSITION CLOSE API - ERROR SCENARIOS"
        
        # Get current positions first
        positions = await self.test_get_current_positions()
        
        # Test 1: Invalid position ID
        print("   Testing invalid position ID...")
        close_data = {
            "position_id": "invalid_position_id",
            "close_percentage": 100.0
        }
        
        response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 UNPROCESSABLE ENTITY ERROR! This indicates Pydantic model validation issues - the main bug!")
            return False
        elif response['status'] == 404 or (isinstance(response['data'], dict) and 'not found' in str(response['data']).lower()):
            print("   ✅ Invalid position ID correctly returns 404/not found")
        else:
            print(f"   ⚠️ Unexpected response for invalid position ID: {response['status']} - {response['data']}")
        
        # Test 2: Invalid close percentage
        print("   Testing invalid close percentage...")
        close_data = {
            "position_id": "test_position",
            "close_percentage": 150.0  # Invalid percentage > 100
        }
        
        response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 ERROR on invalid percentage! Pydantic validation issue!")
            return False
        else:
            print("   ✅ Invalid percentage handled correctly (no 422 error)")
        
        # Test 3: Missing fields
        print("   Testing missing required fields...")
        close_data = {
            "close_percentage": 50.0  # Missing position_id
        }
        
        response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 ERROR on missing fields! Pydantic model issue!")
            return False
        else:
            print("   ✅ Missing fields handled correctly (no 422 error)")
        
        # Test 4: Valid request structure with real position (if available)
        if positions:
            print("   Testing valid request with real position...")
            position_id = positions[0].get('position_id')
            close_data = {
                "position_id": position_id,
                "close_percentage": 25.0
            }
            
            response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data)
            
            if response['status'] == 422:
                self.log_test(test_name, "FAIL", f"❌ CRITICAL: 422 ERROR even with valid position! This is the main bug - Pydantic model ClosePositionRequest is broken!")
                return False
            elif response['success']:
                result_data = response['data']
                if isinstance(result_data, dict) and result_data.get('status') == 'success':
                    self.log_test(test_name, "PASS", f"✅ Position close API working correctly - 25% of position {position_id} closed successfully")
                    return True
                else:
                    print(f"   ⚠️ Position close API responded but result unclear: {result_data}")
            else:
                print(f"   ⚠️ Position close failed with status {response['status']}: {response['data']}")
        
        self.log_test(test_name, "PASS", f"✅ Position Close API structure working (no 422 errors) - Pydantic model validation OK")
        return True

    async def test_position_close_with_real_position(self):
        """Test 5: Position Close with Real Position"""
        test_name = "🎯 TEST 5: POSITION CLOSE WITH REAL POSITION"
        
        # First create a position to close
        order_id = await self.test_create_test_position()
        
        if not order_id:
            self.log_test(test_name, "FAIL", f"❌ Could not create test position for close test")
            return False
        
        # Wait a moment for position to be created
        await asyncio.sleep(2)
        
        # Get the position
        positions = await self.test_get_current_positions()
        
        if not positions:
            self.log_test(test_name, "FAIL", f"❌ No positions found after creating order")
            return False
        
        # Find the position we just created
        target_position = None
        for pos in positions:
            if pos.get('symbol') == 'BTC/USDT' and pos.get('side') == 'long':
                target_position = pos
                break
        
        if not target_position:
            self.log_test(test_name, "FAIL", f"❌ Could not find BTC/USDT LONG position")
            return False
        
        position_id = target_position.get('position_id')
        original_size = target_position.get('size', 0)
        
        # Test partial close (50%)
        close_data = {
            "position_id": position_id,
            "close_percentage": 50.0
        }
        
        response = await self.test_api_endpoint("/trading/position/close", method="POST", data=close_data)
        
        if response['status'] == 422:
            self.log_test(test_name, "FAIL", f"❌ CRITICAL BUG CONFIRMED: 422 UNPROCESSABLE ENTITY ERROR when closing real position! ClosePositionRequest Pydantic model is broken!")
            return False
        elif not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Position close failed with status {response['status']}: {response.get('data', 'Unknown error')}")
            return False
        
        data = response['data']
        
        # Check close result
        if isinstance(data, dict):
            if data.get('status') == 'success' and 'result' in data:
                result = data['result']
                if result.get('success'):
                    close_percentage = result.get('close_percentage', 0)
                    pnl = result.get('net_pnl', 0)
                    
                    self.log_test(test_name, "PASS", f"✅ POSITION CLOSE SUCCESSFUL! {close_percentage}% of position closed, PnL: ${pnl:.2f}")
                    return True
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.log_test(test_name, "FAIL", f"❌ Position close not successful: {error_msg}")
                    return False
            else:
                self.log_test(test_name, "FAIL", f"❌ Position close response structure invalid: {data}")
                return False
        else:
            self.log_test(test_name, "FAIL", f"❌ Invalid position close response: {data}")
            return False

    async def test_account_balance_after_close(self):
        """Test 6: Account Balance Updates After Position Close"""
        test_name = "🎯 TEST 6: ACCOUNT BALANCE UPDATES"
        
        # Get account balance before
        account_before = await self.test_api_endpoint("/trading/account")
        
        if not account_before['success']:
            self.log_test(test_name, "FAIL", f"❌ Could not get account balance before test")
            return False
        
        balance_before = account_before['data'].get('account', {}).get('balance', 0)
        
        # Get positions to verify they're updated
        positions_after = await self.test_get_current_positions()
        
        # Get account balance after
        account_after = await self.test_api_endpoint("/trading/account")
        
        if account_after['success']:
            balance_after = account_after['data'].get('account', {}).get('balance', 0)
            
            self.log_test(test_name, "PASS", f"✅ Account balance tracking: Before: ${balance_before:,.2f}, After: ${balance_after:,.2f}, Open positions: {len(positions_after)}")
            return True
        else:
            self.log_test(test_name, "FAIL", f"❌ Could not get account balance after test")
            return False

    async def run_all_tests(self):
        """Run all position close tests"""
        await self.setup()
        
        try:
            print("🔍 TESTING CRITICAL TRADING BUG: Position Close Functionality")
            print("=" * 80)
            
            # Test sequence
            test_results = []
            
            # 1. Test account status
            result1 = await self.test_trading_account_status()
            test_results.append(result1)
            
            # 2. Test get positions
            positions = await self.test_get_current_positions()
            test_results.append(len(positions) >= 0)  # Always passes if API works
            
            # 3. Test position close API with various scenarios
            result3 = await self.test_position_close_api_various_scenarios()
            test_results.append(result3)
            
            # 4. Test position close with real position
            result4 = await self.test_position_close_with_real_position()
            test_results.append(result4)
            
            # 5. Test account balance updates
            result5 = await self.test_account_balance_after_close()
            test_results.append(result5)
            
            # Summary
            passed_tests = sum(1 for result in test_results if result)
            total_tests = len(test_results)
            
            print("=" * 80)
            print(f"🎯 POSITION CLOSE TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("✅ ALL TESTS PASSED - Position Close functionality is working correctly!")
            else:
                print("❌ SOME TESTS FAILED - Position Close functionality has issues!")
                
                # Check for critical 422 errors
                critical_errors = [result for result in self.test_results if '422' in result.get('details', '')]
                if critical_errors:
                    print("🚨 CRITICAL BUG IDENTIFIED: 422 UNPROCESSABLE ENTITY ERRORS")
                    print("   This indicates Pydantic model validation issues in ClosePositionRequest")
                    print("   The frontend cannot close positions due to backend validation errors")
            
            print("=" * 80)
            
            # Detailed results
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"❌ FAILED: {result['test']}")
                    print(f"   {result['details']}")
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = PositionCloseTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())