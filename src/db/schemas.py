"""
Pydantic schemas for request/response validation.
Note: SQLModel models can be used directly, but these schemas provide
additional validation and separation for API requests/responses.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from src.db.models import UserRole

# Additional request/response schemas if needed beyond SQLModel models
# Most schemas are now defined in models.py as SQLModel classes

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
