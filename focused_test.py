#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import urllib.parse

async def focused_test():
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {'email': 'trader@example.com', 'password': 'password123'}
        async with session.post('https://crypto-ai-trading-2.preview.emergentagent.com/api/auth/login', json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                token = data.get('access_token')
                headers = {'Authorization': f'Bearer {token}'}
                
                print('=== AI TRADING TESTS ===')
                
                # Test 1: AI Analysis
                async with session.post('https://crypto-ai-trading-2.preview.emergentagent.com/api/ai-trading/analyze?symbol=BTC/USDT&context=comprehensive_test', headers=headers) as ai_response:
                    if ai_response.status == 200:
                        ai_data = await ai_response.json()
                        rec = ai_data.get('recommendation', {})
                        reasoning = rec.get('reasoning', '') if isinstance(rec, dict) else ''
                        action = rec.get('action', '') if isinstance(rec, dict) else ''
                        print(f'✅ AI Analysis: {len(reasoning)} chars reasoning, action: {action}')
                    else:
                        print(f'❌ AI Analysis failed: {ai_response.status}')
                
                # Test 2: Chat Command
                command = urllib.parse.quote('Analyze BTC trading opportunity')
                async with session.post(f'https://crypto-ai-trading-2.preview.emergentagent.com/api/ai-trading/chat-command?command={command}', headers=headers) as chat_response:
                    if chat_response.status == 200:
                        chat_data = await chat_response.json()
                        if chat_data.get('status') == 'success':
                            print('✅ Chat Command: Working')
                        else:
                            print(f'⚠️ Chat Command: {chat_data.get("status")}')
                    else:
                        print(f'❌ Chat Command failed: {chat_response.status}')
                
                print('\n=== PAPER TRADING TESTS ===')
                
                # Test 3: Paper Trading Order
                order_data = {
                    'symbol': 'BTC/USDT',
                    'side': 'buy',
                    'order_type': 'market',
                    'quantity': 0.001,
                    'leverage': 1
                }
                async with session.post('https://crypto-ai-trading-2.preview.emergentagent.com/api/trading/order', json=order_data, headers=headers) as order_response:
                    if order_response.status == 200:
                        order_data_resp = await order_response.json()
                        fill_price = order_data_resp.get('fill_price', 0)
                        if fill_price > 0:
                            print(f'✅ Paper Trading: Order filled at ${fill_price:.2f}')
                        else:
                            print('⚠️ Paper Trading: Order executed but no fill price')
                    else:
                        print(f'❌ Paper Trading failed: {order_response.status}')
                
                print('\n=== REAL-TIME DATA TESTS ===')
                
                # Test 4: Real-time data
                async with session.get('https://crypto-ai-trading-2.preview.emergentagent.com/api/realtime/latest') as rt_response:
                    if rt_response.status == 200:
                        rt_data = await rt_response.json()
                        data = rt_data.get('data', {})
                        btc_price = data.get('BTC/USDT', {}).get('price', 0)
                        asset_count = len([k for k, v in data.items() if v and v.get('price', 0) > 0])
                        print(f'✅ Real-time Data: {asset_count} assets, BTC: ${btc_price:.2f}')
                    else:
                        print(f'❌ Real-time Data failed: {rt_response.status}')

if __name__ == "__main__":
    asyncio.run(focused_test())