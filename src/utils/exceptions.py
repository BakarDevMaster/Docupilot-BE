"""
Custom exceptions for the application.
"""
from fastapi import HTTPException, status

class DocuPilotException(HTTPException):
    """Base exception for DocuPilot application."""
    pass

class DocumentNotFoundError(DocuPilotException):
    """Raised when a document is not found."""
    def __init__(self, doc_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found"
        )

class UserNotFoundError(DocuPilotException):
    """Raised when a user is not found."""
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )

class UnauthorizedError(DocuPilotException):
    """Raised when user is not authorized."""
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ValidationError(DocuPilotException):
    """Raised when validation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class AgentError(DocuPilotException):
    """Raised when agent operations fail."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent operation failed: {detail}"
        )

class EmbeddingError(DocuPilotException):
    """Raised when embedding operations fail."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding operation failed: {detail}"
        )

