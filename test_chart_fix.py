#!/usr/bin/env python3
"""
Quick test for chart data fix
"""
import requests
import json

def test_chart_data():
    url = "https://crypto-ai-trading-2.preview.emergentagent.com/api/chart-data/BTC-USDT?timeframe=1h&limit=3"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {data.keys()}")
            
            if 'data' in data and len(data['data']) > 0:
                first_candle = data['data'][0]
                print(f"First candle: {json.dumps(first_candle, indent=2)}")
                
                # Check if open != close
                if first_candle.get('open') == first_candle.get('close'):
                    print("❌ PROBLEM: open === close still exists!")
                else:
                    print("✅ SUCCESS: open !== close!")
            else:
                print("❌ No chart data returned")
        else:
            print(f"❌ Bad status: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chart_data()