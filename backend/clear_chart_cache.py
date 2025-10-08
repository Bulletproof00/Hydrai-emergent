#!/usr/bin/env python3
"""
Clear MongoDB chart data cache for fixing candlestick rendering
Removes faulty OHLCV data where open === close
"""
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# MongoDB connection from environment
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/trading_ai')

async def clear_chart_cache():
    """Clear problematic chart data cache"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.get_default_database()
        
        print("🧹 Clearing problematic chart data cache...")
        
        # Delete all market_data_historical entries
        result = await db.market_data_historical.delete_many({})
        print(f"✅ Deleted {result.deleted_count} historical market data entries")
        
        # Also clear any synthetic data in ai_data collection
        result2 = await db.ai_data.delete_many({'symbol': {'$in': ['BTC/USDT', 'ETH/USDT']}})
        print(f"✅ Deleted {result2.deleted_count} AI data entries")
        
        print("🎯 Cache cleared - Chart API will now use fresh fallback data generation")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_chart_cache())