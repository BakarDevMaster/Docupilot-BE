from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from pydantic import BaseModel, EmailStr, Field, validator
from src.db.database import get_db
from src.db import models
from src.db.repository import UserRepository
from src.db.schemas import UserLogin, Token
from src.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from src.utils.validators import validate_email, validate_password
from src.utils.exceptions import ValidationError, UnauthorizedError
from typing import Optional

router = APIRouter()

# Simple Bearer token scheme for Swagger UI
# This will show a simple token input field instead of OAuth2 form
bearer_scheme = HTTPBearer()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency to get user repository."""
    return UserRepository(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from credentials
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: models.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    try:
        user_repo = UserRepository(db)
        
        # Validate email
        try:
            validate_email(user_data.email)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validate password
        try:
            validate_password(user_data.password)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Check if user already exists
        existing_user = user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Hash password
        # Get password from Pydantic model (should already be a string)
        password = user_data.password
        if not password:
            raise ValidationError("Password is required")
        
        # Ensure it's a plain string
        if isinstance(password, bytes):
            password = password.decode('utf-8', errors='ignore')
        elif not isinstance(password, str):
            password = str(password)
        
        # Remove any extra whitespace
        password = password.strip()
        
        # Check byte length before hashing
        try:
            password_bytes = password.encode('utf-8')
            byte_length = len(password_bytes)
            
            if byte_length > 72:
                raise ValidationError(
                    f"Password is too long ({byte_length} bytes). "
                    "Bcrypt supports passwords up to 72 bytes. Please use a shorter password."
                )
        except (UnicodeEncodeError, AttributeError) as e:
            raise ValidationError(f"Invalid password format: {str(e)}")
        
        # Hash the password - passlib handles bcrypt internally
        # Make sure we're passing a plain string, not bytes
        try:
            hashed_password = get_password_hash(password)
        except ValueError as e:
            # Re-raise validation errors as-is
            raise ValidationError(str(e))
        except Exception as e:
            # Catch any other errors
            error_msg = str(e)
            raise ValidationError(f"Password hashing failed: {error_msg}")
        
        # Create user
        user = user_repo.create(user_data, hashed_password)
        
        return user
    
    except (ValidationError):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login and get access token.
    Simple email and password login.
    """
    try:
        user_repo = UserRepository(db)
        
        # Validate email format
        try:
            validate_email(login_data.email)
        except ValueError:
            raise UnauthorizedError("Invalid email format")
        
        # Get user by email
        user = user_repo.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except (UnauthorizedError):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=models.UserResponse)
async def get_current_user_endpoint(
    current_user: models.User = Depends(get_current_user)
):
    """
    Get current authenticated user.
    """
    return current_user

@router.post("/logout")
async def logout(current_user: models.User = Depends(get_current_user)):
    """
    Logout user.
    Note: Since JWT is stateless, logout is handled client-side by removing the token.
    This endpoint can be used for logging purposes or to invalidate tokens server-side
    if implementing token blacklisting.
    """
    return {"message": "Successfully logged out"}

