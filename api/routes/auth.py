"""
Authentication API routes for SwissKnife AI Scraper
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings

# Setup
router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class ValidationRequest(BaseModel):
    token: str

class ValidationResponse(BaseModel):
    valid: bool
    user: Dict[str, Any] = None
    expires_at: str = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str
    reset_instructions: str

class PasswordUpdateRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)

# Temporary in-memory user storage (replace with database)
USERS_DB = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError("Invalid token")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return access token"""
    try:
        # Check if user exists
        user = USERS_DB.get(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        
        # Return token and user info
        user_info = {
            "id": str(user["id"]),  # Convert to string for frontend compatibility
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": True,
            "is_verified": True,
            "subscription_tier": "free",
            "created_at": user["created_at"],
            "updated_at": user["created_at"],
            "metadata": {}
        }
        
        logger.info(f"User logged in: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        if request.email in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = len(USERS_DB) + 1
        password_hash = get_password_hash(request.password)
        
        user = {
            "id": user_id,
            "email": request.email,
            "full_name": request.full_name,
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        USERS_DB[request.email] = user
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        
        # Return token and user info
        user_info = {
            "id": str(user["id"]),  # Convert to string for frontend compatibility
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": True,
            "is_verified": True,
            "subscription_tier": "free",
            "created_at": user["created_at"],
            "updated_at": user["created_at"],
            "metadata": {}
        }
        
        logger.info(f"New user registered: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/validate", response_model=ValidationResponse)
async def validate_token(request: ValidationRequest):
    """Validate a JWT token"""
    try:
        payload = verify_token(request.token)
        email = payload.get("sub")
        user = USERS_DB.get(email)
        
        if not user:
            return ValidationResponse(valid=False)
        
        user_info = {
            "id": str(user["id"]),  # Convert to string for frontend compatibility
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": True,
            "is_verified": True,
            "subscription_tier": "free",
            "created_at": user["created_at"],
            "updated_at": user["created_at"],
            "metadata": {}
        }
        
        return ValidationResponse(
            valid=True,
            user=user_info,
            expires_at=datetime.fromtimestamp(payload["exp"]).isoformat()
        )
        
    except HTTPException:
        return ValidationResponse(valid=False)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return ValidationResponse(valid=False)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: ValidationRequest):
    """Refresh an access token"""
    try:
        payload = verify_token(request.token)
        email = payload.get("sub")
        user = USERS_DB.get(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        
        user_info = {
            "id": str(user["id"]),  # Convert to string for frontend compatibility
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": True,
            "is_verified": True,
            "subscription_tier": "free",
            "created_at": user["created_at"],
            "updated_at": user["created_at"],
            "metadata": {}
        }
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    try:
        payload = verify_token(credentials.credentials)
        email = payload.get("sub")
        user = USERS_DB.get(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: PasswordResetRequest):
    """Request password reset (simplified version for demo)"""
    try:
        # Check if user exists
        if request.email not in USERS_DB:
            # For security, don't reveal if email exists or not
            return PasswordResetResponse(
                message="If this email is registered, you will receive reset instructions.",
                reset_instructions="For demo purposes: Use the 'Reset Password' endpoint with your email and new password."
            )

        user = USERS_DB[request.email]
        logger.info(f"Password reset requested for: {request.email}")

        return PasswordResetResponse(
            message="Password reset instructions sent.",
            reset_instructions=f"For demo purposes: Use the 'Reset Password' endpoint with email '{request.email}' and your new password."
        )

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/reset-password", response_model=dict)
async def reset_password(request: PasswordUpdateRequest):
    """Reset password (simplified version for demo)"""
    try:
        # Check if user exists
        if request.email not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user = USERS_DB[request.email]
        user["password_hash"] = get_password_hash(request.new_password)
        user["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Password reset completed for: {request.email}")

        return {
            "message": "Password reset successful",
            "email": request.email,
            "instructions": "You can now login with your new password"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
