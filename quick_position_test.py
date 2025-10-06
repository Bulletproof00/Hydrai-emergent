#!/usr/bin/env python3
"""
Quick test to check existing positions and their liquidation prices
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://self-coding-ai.preview.emergentagent.com/api"

async def test_positions():
    async with aiohttp.ClientSession() as session:
        # Register a test user
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        user_data = {
            "email": f"quick_test_{timestamp}@example.com",
            "password": "testpass123",
            "username": f"quick_test_{timestamp}"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
            if response.status == 200:
                data = await response.json()
                auth_token = data.get('access_token')
                print(f"✅ Test user created")
            else:
                print(f"❌ Could not create test user: {response.status}")
                return
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # First create trading account
        async with session.get(f"{BACKEND_URL}/trading/account", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Trading account created: {data}")
            else:
                print(f"❌ Could not create trading account: {response.status}")
                return
        
        # Create a leveraged position
        order_data = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.01,
            "leverage": 10
        }
        
        async with session.post(f"{BACKEND_URL}/trading/order", json=order_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Order placed: {data}")
            else:
                print(f"❌ Order failed: {response.status}")
                return
        
        # Get positions
        async with session.get(f"{BACKEND_URL}/trading/positions", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                positions = data.get('positions', [])
                print(f"✅ Found {len(positions)} positions")
                
                for pos in positions:
                    entry_price = pos.get('entry_price', 0)
                    liquidation_price = pos.get('liquidation_price', 0)
                    leverage = pos.get('leverage', 1)
                    side = pos.get('side', '')
                    
                    if liquidation_price > 0 and entry_price > 0:
                        price_diff_percentage = abs(liquidation_price - entry_price) / entry_price * 100
                        print(f"Position: {pos['symbol']} {side}")
                        print(f"  Entry: ${entry_price:.2f}")
                        print(f"  Liquidation: ${liquidation_price:.2f}")
                        print(f"  Leverage: {leverage}x")
                        print(f"  Distance: {price_diff_percentage:.1f}%")
                        print()
            else:
                print(f"❌ Could not get positions: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_positions())