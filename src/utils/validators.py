"""
Validation utilities for request data.
"""
from typing import Optional
from pydantic import BaseModel, validator, EmailStr
import re

def validate_document_title(title: str) -> str:
    """Validate document title."""
    if not title or len(title.strip()) < 3:
        raise ValueError("Title must be at least 3 characters long")
    if len(title) > 200:
        raise ValueError("Title must be less than 200 characters")
    return title.strip()

def validate_document_content(content: str) -> str:
    """Validate document content."""
    if not content or len(content.strip()) < 10:
        raise ValueError("Content must be at least 10 characters long")
    if len(content) > 100000:  # 100KB limit
        raise ValueError("Content must be less than 100,000 characters")
    return content.strip()

def validate_email(email: str) -> str:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    return email.lower().strip()

def validate_password(password: str) -> str:
    """Validate password strength."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be less than 128 characters")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one number")
    return password

def validate_doc_type(doc_type: str) -> str:
    """Validate document type."""
    valid_types = ["api", "architecture", "module", "guide", "tutorial", "reference", "other"]
    if doc_type.lower() not in valid_types:
        raise ValueError(f"Document type must be one of: {', '.join(valid_types)}")
    return doc_type.lower()

def validate_chunk_size(chunk_size: int) -> int:
    """Validate chunk size for embeddings."""
    if chunk_size < 100:
        raise ValueError("Chunk size must be at least 100 characters")
    if chunk_size > 5000:
        raise ValueError("Chunk size must be less than 5000 characters")
    return chunk_size

def validate_top_k(top_k: int) -> int:
    """Validate top_k for search."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if top_k > 50:
        raise ValueError("top_k must be less than 50")
    return top_k

