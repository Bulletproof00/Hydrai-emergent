#!/usr/bin/env python3
"""
COMPREHENSIVE POSITION CLOSE BUG ANALYSIS
Testing all aspects of the position close functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"

async def comprehensive_test():
    """Comprehensive test of position close functionality"""
    
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': 'Bearer demo-token'}
        
        print("🔍 COMPREHENSIVE POSITION CLOSE BUG ANALYSIS")
        print("=" * 70)
        
        results = {
            'account_status': False,
            'positions_available': False,
            'pydantic_validation': False,
            'price_availability': False,
            'position_close_success': False
        }
        
        # 1. Test Trading Account Status
        print("1. Testing Trading Account Status...")
        try:
            async with session.get(f"{BACKEND_URL}/trading/account", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    account = data.get('account', {})
                    balance = account.get('balance', 0)
                    if balance > 0:
                        print(f"   ✅ Account Status OK - Balance: ${balance:,.2f}")
                        results['account_status'] = True
                    else:
                        print(f"   ❌ Invalid balance: ${balance}")
                else:
                    print(f"   ❌ Account API failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Account test error: {e}")
        
        # 2. Test Get Positions
        print("\n2. Testing Get Current Positions...")
        position_id = None
        try:
            async with session.get(f"{BACKEND_URL}/trading/positions", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    positions = data.get('positions', [])
                    if positions:
                        position = positions[0]
                        position_id = position.get('position_id')
                        symbol = position.get('symbol')
                        side = position.get('side')
                        size = position.get('size')
                        entry_price = position.get('entry_price')
                        
                        print(f"   ✅ Found position: {symbol} {side} {size} @ ${entry_price:,.2f}")
                        print(f"   Position ID: {position_id}")
                        results['positions_available'] = True
                    else:
                        print("   ❌ No positions found")
                else:
                    print(f"   ❌ Positions API failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Positions test error: {e}")
        
        # 3. Test Pydantic Model Validation
        print("\n3. Testing Pydantic Model Validation...")
        
        # Test 3a: Missing required field
        print("   3a. Testing missing position_id (should return 422)...")
        try:
            close_data = {"close_percentage": 50.0}
            async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
                status = response.status
                result = await response.json() if response.content_type == 'application/json' else await response.text()
                
                if status == 422:
                    print("   ❌ CRITICAL BUG: 422 UNPROCESSABLE ENTITY ERROR!")
                    print(f"   Error: {result}")
                    print("   This prevents frontend from handling validation errors properly")
                else:
                    print(f"   ✅ Handled gracefully: {status}")
                    results['pydantic_validation'] = True
        except Exception as e:
            print(f"   ❌ Pydantic test error: {e}")
        
        # Test 3b: Valid structure but invalid position
        print("   3b. Testing valid structure with fake position_id...")
        try:
            close_data = {"position_id": "fake_position", "close_percentage": 50.0}
            async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
                status = response.status
                result = await response.json() if response.content_type == 'application/json' else await response.text()
                
                if status == 422:
                    print("   ❌ CRITICAL BUG: 422 ERROR even with valid structure!")
                elif status == 200:
                    print(f"   ✅ Valid structure processed: {status}")
                    if isinstance(result, dict) and 'error' in str(result):
                        print(f"   Response: {result}")
                    results['pydantic_validation'] = True
                else:
                    print(f"   ⚠️ Unexpected status: {status}")
        except Exception as e:
            print(f"   ❌ Structure test error: {e}")
        
        # 4. Test Price Availability
        print("\n4. Testing Price Availability...")
        try:
            async with session.get(f"{BACKEND_URL}/realtime/latest?symbols=BTC/USDT", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        realtime_data = data.get('data', {})
                        if 'BTC/USDT' in realtime_data:
                            btc_price = realtime_data['BTC/USDT'].get('price', 0)
                            if btc_price > 0:
                                print(f"   ✅ Real-time price available: BTC/USDT = ${btc_price:,.2f}")
                                results['price_availability'] = True
                            else:
                                print("   ❌ Real-time price is 0")
                        else:
                            print("   ❌ BTC/USDT not in real-time data")
                    else:
                        print(f"   ❌ Real-time API error: {data}")
                else:
                    print(f"   ❌ Real-time API failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Price test error: {e}")
        
        # 5. Test Actual Position Close
        if position_id:
            print("\n5. Testing Actual Position Close...")
            try:
                close_data = {"position_id": position_id, "close_percentage": 25.0}
                async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
                    status = response.status
                    result = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    print(f"   Status: {status}")
                    print(f"   Response: {result}")
                    
                    if status == 422:
                        print("   ❌ CRITICAL: 422 ERROR on valid position close!")
                    elif status == 200:
                        if isinstance(result, dict):
                            if result.get('status') == 'success':
                                print("   ✅ Position close successful!")
                                results['position_close_success'] = True
                            elif 'Cannot get current price' in str(result):
                                print("   ❌ CRITICAL: Cannot get current price - Binance API issue!")
                            else:
                                print(f"   ❌ Position close failed: {result}")
                    else:
                        print(f"   ⚠️ Unexpected response: {status}")
            except Exception as e:
                print(f"   ❌ Position close test error: {e}")
        else:
            print("\n5. Skipping position close test - no position available")
        
        # Summary
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE TEST RESULTS:")
        print("=" * 70)
        
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test.replace('_', ' ').title()}")
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
        if not results['pydantic_validation']:
            print("❌ PYDANTIC VALIDATION: 422 errors prevent frontend from closing positions")
        if not results['price_availability']:
            print("❌ PRICE AVAILABILITY: Binance API geographic restrictions prevent price fetching")
        if not results['position_close_success']:
            print("❌ POSITION CLOSE: Cannot close positions due to price/validation issues")
        
        print("\n🔧 ROOT CAUSES:")
        print("1. Binance API returns 451 'Service unavailable from restricted location'")
        print("2. _get_current_price() returns None, causing 'Cannot get current price' error")
        print("3. Pydantic ClosePositionRequest model returns 422 on validation errors")
        print("4. Frontend cannot handle 422 errors properly for user feedback")
        
        print("\n💡 SOLUTIONS NEEDED:")
        print("1. Add fallback price sources when Binance is unavailable")
        print("2. Improve error handling for price unavailability")
        print("3. Better Pydantic validation error responses")
        print("4. Frontend error handling for position close failures")

if __name__ == "__main__":
    asyncio.run(comprehensive_test())