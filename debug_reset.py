#!/usr/bin/env python3
"""
Debug script to check account reset response structure
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ai-trade-hub-4.preview.emergentagent.com/api"

async def debug_reset():
    async with aiohttp.ClientSession() as session:
        # Login first
        login_data = {
            "email": "demo@example.com",
            "password": "demo123"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                auth_token = data.get('access_token')
                print(f"✅ Logged in successfully")
            else:
                print(f"❌ Login failed: {response.status}")
                return
        
        # Test account reset
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        async with session.post(f"{BACKEND_URL}/trading/account/reset", headers=headers) as response:
            print(f"Reset Response Status: {response.status}")
            print(f"Reset Response Headers: {dict(response.headers)}")
            
            if response.content_type == 'application/json':
                data = await response.json()
                print(f"Reset Response Data: {json.dumps(data, indent=2)}")
            else:
                text = await response.text()
                print(f"Reset Response Text: {text}")

if __name__ == "__main__":
    asyncio.run(debug_reset())