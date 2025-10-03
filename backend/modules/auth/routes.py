from fastapi import APIRouter, HTTPException, Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import UserCreate, UserLogin, Token, UserResponse, UserInDB
from .utils import verify_password, get_password_hash, create_access_token, decode_access_token
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["authentication"])

async def get_current_user(authorization: str = Header(None), db = None):
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(' ')[1]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncIOMotorDatabase = None):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    user_id = str(uuid.uuid4())
    user_in_db = UserInDB(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    user_dict = user_in_db.dict()
    user_dict["_id"] = user_id
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        created_at=user_dict["created_at"],
        paper_trading_balance=10000.0
    )
    
    return Token(access_token=access_token, user=user_response)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncIOMotorDatabase = None):
    """Login user"""
    user = await db.users.find_one({"email": user_data.email})
    
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["_id"]})
    
    user_response = UserResponse(
        id=user["_id"],
        email=user["email"],
        username=user["username"],
        created_at=user["created_at"],
        paper_trading_balance=user.get("paper_trading_balance", 10000.0)
    )
    
    return Token(access_token=access_token, user=user_response)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user["_id"],
        email=current_user["email"],
        username=current_user["username"],
        created_at=current_user["created_at"],
        paper_trading_balance=current_user.get("paper_trading_balance", 10000.0)
    )
