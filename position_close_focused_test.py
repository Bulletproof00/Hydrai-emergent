#!/usr/bin/env python3
"""
FOCUSED TEST: Position Close with Existing Position
Testing the exact position close bug with the existing BTC/USDT position
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"

async def test_position_close_bug():
    """Test the exact position close bug"""
    
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': 'Bearer demo-token'}
        
        print("🔍 TESTING POSITION CLOSE BUG WITH EXISTING POSITION")
        print("=" * 60)
        
        # 1. Get current positions
        print("1. Getting current positions...")
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
                else:
                    print("   ❌ No positions found")
                    return
            else:
                print(f"   ❌ Failed to get positions: {response.status}")
                return
        
        # 2. Test position close with different payloads
        print("\n2. Testing position close with various payloads...")
        
        # Test 1: Valid payload
        print("   Test 1: Valid payload (50% close)")
        close_data = {
            "position_id": position_id,
            "close_percentage": 50.0
        }
        
        async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
            status = response.status
            try:
                result = await response.json()
            except:
                result = await response.text()
            
            print(f"   Status: {status}")
            print(f"   Response: {result}")
            
            if status == 422:
                print("   🚨 CRITICAL BUG: 422 UNPROCESSABLE ENTITY ERROR!")
                print("   This confirms the Pydantic model validation issue")
            elif status == 200:
                print("   ✅ Position close request processed successfully")
            else:
                print(f"   ⚠️ Unexpected status: {status}")
        
        # Test 2: Missing position_id
        print("\n   Test 2: Missing position_id")
        close_data = {
            "close_percentage": 25.0
        }
        
        async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
            status = response.status
            try:
                result = await response.json()
            except:
                result = await response.text()
            
            print(f"   Status: {status}")
            if status == 422:
                print("   🚨 422 ERROR: Pydantic validation failing on missing required field")
                print(f"   Error details: {result}")
            else:
                print(f"   Response: {result}")
        
        # Test 3: Invalid close_percentage
        print("\n   Test 3: Invalid close_percentage (150%)")
        close_data = {
            "position_id": position_id,
            "close_percentage": 150.0
        }
        
        async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
            status = response.status
            try:
                result = await response.json()
            except:
                result = await response.text()
            
            print(f"   Status: {status}")
            if status == 422:
                print("   🚨 422 ERROR: Pydantic validation failing on invalid percentage")
                print(f"   Error details: {result}")
            else:
                print(f"   Response: {result}")
        
        # Test 4: Wrong data types
        print("\n   Test 4: Wrong data types")
        close_data = {
            "position_id": position_id,
            "close_percentage": "50"  # String instead of float
        }
        
        async with session.post(f"{BACKEND_URL}/trading/position/close", json=close_data, headers=headers) as response:
            status = response.status
            try:
                result = await response.json()
            except:
                result = await response.text()
            
            print(f"   Status: {status}")
            if status == 422:
                print("   🚨 422 ERROR: Pydantic validation failing on wrong data type")
                print(f"   Error details: {result}")
            else:
                print(f"   Response: {result}")
        
        print("\n" + "=" * 60)
        print("🎯 CONCLUSION:")
        print("If any of the above tests show 422 errors, it confirms the")
        print("ClosePositionRequest Pydantic model has validation issues")
        print("preventing the frontend from closing positions properly.")

if __name__ == "__main__":
    asyncio.run(test_position_close_bug())