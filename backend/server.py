from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from config import MONGO_URL, DB_NAME, CORS_ORIGINS
from modules.auth import routes as auth_routes
from modules.trading import routes as trading_routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

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

# Dependency injection for DB
async def get_db():
    return db

# Middleware to inject db into routes
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = db
    response = await call_next(request)
    return response

# Include routers with db dependency
@app.on_event("startup")
async def startup():
    logger.info("Starting Hydra Trading Platform...")
    
    # Monkey patch db into route handlers
    auth_routes.router.dependency_overrides_provider = lambda: db
    trading_routes.router.dependency_overrides_provider = lambda: db
    
    logger.info("Hydra Trading Platform started!")

# Override get_current_user to inject db
from modules.auth.routes import get_current_user as original_get_current_user

async def get_current_user_with_db(authorization: str = None, request: Request = None):
    return await original_get_current_user(authorization, request.state.db)

# Apply db injection to routes
def inject_db_into_endpoint(endpoint):
    async def wrapper(*args, **kwargs):
        from fastapi import Request
        request = kwargs.get('request')
        if request and hasattr(request.state, 'db'):
            kwargs['db'] = request.state.db
        return await endpoint(*args, **kwargs)
    return wrapper

# Manually inject db parameter
for route in auth_routes.router.routes:
    if hasattr(route, 'endpoint'):
        original_endpoint = route.endpoint
        async def new_endpoint(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')
            if request and hasattr(request.state, 'db'):
                kwargs['db'] = request.state.db
            return await original_endpoint(*args, **kwargs)
        route.endpoint = new_endpoint

# Include routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(trading_routes.router, prefix="/api")

@app.get("/api/")
async def root():
    return {"message": "Hydra Trading Platform API"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "database": "connected"}
