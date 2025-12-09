"""
Authentication utilities for password hashing and JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
import os

# Password hashing context
# Use bcrypt with proper configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Standard bcrypt rounds
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    Uses bcrypt directly for consistency with get_password_hash.
    """
    # Ensure password is bytes
    if isinstance(plain_password, str):
        plain_password_bytes = plain_password.encode('utf-8')
    else:
        plain_password_bytes = plain_password
    
    # Ensure hash is bytes
    if isinstance(hashed_password, str):
        hashed_password_bytes = hashed_password.encode('utf-8')
    else:
        hashed_password_bytes = hashed_password
    
    # Use bcrypt directly
    try:
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    Bcrypt has a 72-byte limit, but we handle this properly.
    
    Uses bcrypt directly to avoid passlib encoding issues.
    """
    # Ensure password is a plain string (not bytes)
    if isinstance(password, bytes):
        password = password.decode('utf-8', errors='ignore')
    elif not isinstance(password, str):
        password = str(password)
    
    # Remove any leading/trailing whitespace
    password = password.strip()
    
    # Verify byte length (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')
    byte_length = len(password_bytes)
    
    if byte_length > 72:
        raise ValueError(f"Password exceeds 72 bytes: {byte_length} bytes")
    
    # Use bcrypt directly instead of passlib to avoid encoding issues
    # bcrypt.hashpw expects bytes, not a string
    try:
        # Generate salt and hash the password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string (bcrypt hash is ASCII-safe)
        return hashed.decode('utf-8')
    except Exception as e:
        # If there's an error, provide detailed information
        error_msg = str(e)
        raise ValueError(
            f"Password hashing failed: {error_msg}. "
            f"Password has {byte_length} bytes (characters: {len(password)})."
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data (typically user ID)
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

