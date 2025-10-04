#!/usr/bin/env python3
"""
Test script for real-time market data fetching
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to sys.path
sys.path.append('/app/backend')

from modules.real_time_market_data import RealTimeMarketDataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_time_data():
    """Test the real-time data fetcher"""
    print("🚀 Testing Real-Time Market Data Fetcher...")
    
    # Create a mock DB (we don't need it for basic quote testing)
    fetcher = RealTimeMarketDataFetcher(db=None)
    
    # Test symbols
    test_symbols = ['NASDAQ', 'SPX', 'GOLD', 'DXY']
    
    print("\n📊 Testing individual quotes:")
    for symbol in test_symbols:
        try:
            quote = await fetcher.get_real_time_quote(symbol)
            if quote:
                print(f"✅ {symbol}: ${quote['price']:.2f} (from {quote['source']})")
            else:
                print(f"❌ {symbol}: No data available")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
    
    print("\n📈 Testing multiple quotes at once:")
    try:
        quotes = await fetcher.get_multiple_quotes(test_symbols)
        for symbol, quote in quotes.items():
            print(f"✅ {symbol}: ${quote['price']:.2f} (from {quote['source']})")
        
        if 'NASDAQ' in quotes:
            nasdaq_price = quotes['NASDAQ']['price']
            print(f"\n🎯 NASDAQ Current Price: ${nasdaq_price:.2f}")
            if nasdaq_price > 23000:
                print("✅ NASDAQ price looks current (above 23k)")
            else:
                print("⚠️  NASDAQ price might be outdated")
    
    except Exception as e:
        print(f"❌ Error testing multiple quotes: {e}")
    
    print("\n🧪 Testing enhanced OHLCV format:")
    try:
        nasdaq_ohlcv = await fetcher.fetch_enhanced_traditional_ohlcv('NASDAQ', '1h', 10)
        if nasdaq_ohlcv:
            latest = nasdaq_ohlcv[-1]
            print(f"✅ NASDAQ OHLCV: Latest close ${latest['close']:.2f}")
            print(f"   Timestamp: {latest['timestamp']}")
            print(f"   OHLC: O:{latest['open']:.2f} H:{latest['high']:.2f} L:{latest['low']:.2f} C:{latest['close']:.2f}")
        else:
            print("❌ No OHLCV data available")
    except Exception as e:
        print(f"❌ Error testing OHLCV: {e}")
    
    # Clean up
    await fetcher.close_session()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_real_time_data())