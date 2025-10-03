from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from config import MONGO_URL, DB_NAME, CORS_ORIGINS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db_instance = client[DB_NAME]

# Create app
app = FastAPI(title="Hydra Trading Platform")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store db in app state
app.state.db = db_instance

# Import routes after db is created
from modules.auth.routes import create_auth_router
from modules.trading.routes import create_trading_router

# Create routers with db
auth_router = create_auth_router(db_instance)
trading_router = create_trading_router(db_instance)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(trading_router, prefix="/api")

@app.on_event("startup")
async def startup():
    logger.info("Starting Hydra Trading Platform...")
    logger.info("Database connected")
    logger.info("Hydra Trading Platform started!")

@app.get("/api/")
async def root():
    return {"message": "Hydra Trading Platform API"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "database": "connected"}
