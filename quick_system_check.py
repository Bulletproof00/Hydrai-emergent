#!/usr/bin/env python3
"""
Quick System Check - Fast verification of key components
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://ai-trade-hub-4.preview.emergentagent.com/api"

async def quick_system_check():
    """Quick system health check"""
    print("🔍 QUICK SYSTEM CHECK")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        # Test basic endpoints
        endpoints = [
            ("/", "Root API"),
            ("/plugins", "Plugins"),
            ("/market-overview", "Market Overview"),
            ("/realtime/latest", "Real-time Data")
        ]
        
        for endpoint, name in endpoints:
            try:
                async with session.get(f"{BACKEND_URL}{endpoint}", timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ {name}: OK")
                    else:
                        print(f"⚠️ {name}: Status {response.status}")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)[:50]}")
        
        print()
        
        # Test authentication
        try:
            login_data = {"email": "demo@example.com", "password": "demo123"}
            async with session.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    auth_token = data.get('access_token')
                    print("✅ Authentication: OK")
                    
                    # Test chat endpoint with auth
                    headers = {'Authorization': f'Bearer {auth_token}'}
                    chat_data = {"session_id": "quick_test", "content": "Hallo, kurzer Test"}
                    
                    async with session.post(f"{BACKEND_URL}/chat", json=chat_data, headers=headers, timeout=30) as chat_response:
                        if chat_response.status == 422:
                            print("❌ Chat System: 422 ERROR - HAUPTPROBLEM NOCH VORHANDEN!")
                        elif chat_response.status == 200:
                            chat_data = await chat_response.json()
                            response_content = chat_data.get('content', '')
                            print(f"✅ Chat System: OK ({len(response_content)} chars)")
                        else:
                            print(f"⚠️ Chat System: Status {chat_response.status}")
                else:
                    print(f"❌ Authentication: Status {response.status}")
        except Exception as e:
            print(f"❌ Authentication/Chat: Error - {str(e)[:50]}")
        
        print()
        print("🎯 QUICK CHECK COMPLETE")

if __name__ == "__main__":
    asyncio.run(quick_system_check())