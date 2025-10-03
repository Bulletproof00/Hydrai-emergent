import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# JWT
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production-2024")

# Trading
TOP_10_COINS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT",
    "SOL/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT", "LTC/USDT"
]

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "6h", "12h", "1d", "1w", "1M"]
