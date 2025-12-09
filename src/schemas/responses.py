"""
Response schemas for consistent API responses.
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    detail: str
    status_code: int
    timestamp: datetime = datetime.utcnow()

class SuccessResponse(BaseModel):
    """Standard success response schema."""
    message: str
    status: str = "success"
    timestamp: datetime = datetime.utcnow()

class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool

class DocumentListResponse(BaseModel):
    """Response for document list."""
    documents: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool

class EmbeddingCreateResponse(BaseModel):
    """Response for embedding creation."""
    message: str
    doc_id: str
    chunks_count: int
    vector_ids: List[str]

class EmbeddingDeleteResponse(BaseModel):
    """Response for embedding deletion."""
    message: str
    doc_id: str
    deleted_count: int

class AuditResponse(BaseModel):
    """Response for document audit."""
    doc_id: str
    outdated_sections: List[Dict]
    inconsistencies: List[Dict]
    issues_count: int
    status: str

class AgentGenerationResponse(BaseModel):
    """Response for agent generation."""
    doc_id: str
    title: str
    content_preview: str
    context_used: int
    generation_time: Optional[float] = None

