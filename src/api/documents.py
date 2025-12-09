from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from sqlmodel import Session
from src.db.database import get_db
from src.db import models
from src.db.repository import DocumentRepository, DocumentVersionRepository
from src.api.auth import get_current_user
from src.agents.generator_agent import GeneratorAgent
from src.agents.maintenance_agent import MaintenanceAgent
from src.services.vector_store import VectorStore
from src.utils.exceptions import (
    DocumentNotFoundError,
    UnauthorizedError,
    ValidationError,
    AgentError
)
from src.utils.validators import (
    validate_document_title,
    validate_document_content,
    validate_doc_type
)

router = APIRouter()

# Request models with validation
class DocumentGenerateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Document title")
    source: str = Field(..., min_length=10, description="Source material for generation")
    doc_type: Optional[str] = Field(default="api", description="Type of document")
    context_doc_ids: Optional[List[str]] = Field(default=None, description="Optional document IDs for context")
    
    @validator('title')
    def validate_title(cls, v):
        return validate_document_title(v)
    
    @validator('doc_type')
    def validate_doc_type(cls, v):
        if v:
            return validate_doc_type(v)
        return v

class DocumentUpdateRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID to update")
    section: str = Field(..., min_length=1, description="Section identifier or description")
    new_content: str = Field(..., min_length=1, description="New content or update instructions")

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Document title")
    content: str = Field(..., min_length=10, description="Document content")
    doc_type: Optional[str] = Field(default="api", description="Type of document")
    
    @validator('title')
    def validate_title(cls, v):
        return validate_document_title(v)
    
    @validator('content')
    def validate_content(cls, v):
        return validate_document_content(v)
    
    @validator('doc_type')
    def validate_doc_type(cls, v):
        if v:
            return validate_doc_type(v)
        return v

class DocumentUpdateContentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200, description="Updated title")
    content: Optional[str] = Field(None, min_length=10, description="Updated content")
    doc_type: Optional[str] = Field(None, description="Updated document type")
    
    @validator('title')
    def validate_title(cls, v):
        if v:
            return validate_document_title(v)
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if v:
            return validate_document_content(v)
        return v
    
    @validator('doc_type')
    def validate_doc_type(cls, v):
        if v:
            return validate_doc_type(v)
        return v

@router.post("/", response_model=models.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new document.
    Requires authentication.
    """
    try:
        doc_repo = DocumentRepository(db)
        
        # Create document
        document_data = models.DocumentCreate(
            title=request.title,
            content=request.content,
            doc_type=request.doc_type
        )
        
        document = doc_repo.create(document_data, current_user.id)
        
        # Create initial version
        version_repo = DocumentVersionRepository(db)
        version_repo.create(
            doc_id=document.id,
            content=document.content,
            user_id=current_user.id
        )
        
        return document
    
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )

@router.get("/", response_model=List[models.DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents with pagination.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    documents = doc_repo.get_all(skip=skip, limit=limit)
    return documents

@router.get("/{doc_id}", response_model=models.DocumentResponse)
async def get_document(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(doc_id)
    
    if not document:
        raise DocumentNotFoundError(doc_id)
    
    return document

@router.put("/{doc_id}", response_model=models.DocumentResponse)
async def update_document(
    doc_id: str,
    request: DocumentUpdateContentRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a document's content, title, or type.
    Creates a new version automatically.
    Requires authentication.
    """
    try:
        doc_repo = DocumentRepository(db)
        version_repo = DocumentVersionRepository(db)
        
        # Check if document exists
        document = doc_repo.get_by_id(doc_id)
        if not document:
            raise DocumentNotFoundError(doc_id)
        
        # Check if at least one field is provided
        if not any([request.title, request.content, request.doc_type]):
            raise ValidationError("At least one field (title, content, or doc_type) must be provided")
        
        # Store old content for versioning
        old_content = document.content
        
        # Update document
        update_data = models.DocumentUpdate(
            title=request.title,
            content=request.content,
            doc_type=request.doc_type
        )
        
        updated_document = doc_repo.update(doc_id, update_data)
        
        if not updated_document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )
        
        # Create new version if content changed
        if request.content and request.content != old_content:
            # Calculate diff (simple text diff for now)
            diff = f"Content updated from {len(old_content)} to {len(request.content)} characters"
            
            version_repo.create(
                doc_id=doc_id,
                content=updated_document.content,
                user_id=current_user.id,
                diff=diff
            )
        
        return updated_document
    
    except (DocumentNotFoundError, ValidationError):
        raise
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document.
    Requires authentication.
    """
    try:
        doc_repo = DocumentRepository(db)
        
        # Check if document exists
        document = doc_repo.get_by_id(doc_id)
        if not document:
            raise DocumentNotFoundError(doc_id)
        
        # Check if user has permission (creator or admin)
        if document.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
            raise UnauthorizedError("Not authorized to delete this document")
        
        success = doc_repo.delete(doc_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
        return None
    
    except (DocumentNotFoundError, UnauthorizedError):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/{doc_id}/versions", response_model=List[models.DocumentVersionResponse])
async def get_document_versions(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get version history for a document.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    
    # Check if document exists
    document = doc_repo.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    versions = version_repo.get_by_doc_id(doc_id)
    return versions

@router.get("/{doc_id}/versions/{version_number}", response_model=models.DocumentVersionResponse)
async def get_document_version(
    doc_id: str,
    version_number: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific version of a document.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    
    # Check if document exists
    document = doc_repo.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    version = version_repo.get_version(doc_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} not found for this document"
        )
    
    return version

# Agent-based endpoints
@router.post("/generate", response_model=models.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: DocumentGenerateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    create_embeddings: bool = Query(True, description="Automatically create embeddings after generation")
):
    """
    Generate a new document using the generator agent.
    Requires authentication.
    
    The agent will:
    1. Understand the intent from the source material
    2. Fetch relevant context from existing documentation
    3. Generate comprehensive documentation using Gemini
    4. Validate the generated content
    5. Create the document with version history
    6. Optionally create embeddings for vector search
    """
    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    generator_agent = GeneratorAgent()
    vector_store = VectorStore()
    
    try:
        # Generate document using agent
        generated_data = await generator_agent.generate_document(
            title=request.title,
            source=request.source,
            doc_type=request.doc_type,
            context_doc_ids=request.context_doc_ids
        )
        
        # Create document in database
        document_data = models.DocumentCreate(
            title=generated_data["title"],
            content=generated_data["content"],
            doc_type=generated_data["doc_type"]
        )
        
        document = doc_repo.create(document_data, current_user.id)
        
        # Create initial version
        version_repo.create(
            doc_id=document.id,
            content=document.content,
            user_id=current_user.id,
            diff=f"Initial generated version. Context used: {generated_data['metadata']['context_used']} chunks"
        )
        
        # Optionally create embeddings for vector search
        if create_embeddings and document.content:
            try:
                await vector_store.store_document(
                    doc_id=document.id,
                    text=document.content,
                    chunk_size=1000,
                    chunk_overlap=200
                )
                
                # Store embedding records in database
                from src.db.repository import EmbeddingRepository
                embedding_repo = EmbeddingRepository(db)
                
                # Get chunks for database storage
                chunks = []
                start = 0
                chunk_size = 1000
                chunk_overlap = 200
                while start < len(document.content):
                    end = start + chunk_size
                    chunk = document.content[start:end]
                    chunks.append(chunk)
                    start = end - chunk_overlap
                
                # Create embedding records
                for i, chunk in enumerate(chunks):
                    vector_id = f"{document.id}_chunk_{i}"
                    embedding_data = models.EmbeddingCreate(
                        doc_id=document.id,
                        chunk_text=chunk,
                        chunk_index=i,
                        vector_id=vector_id
                    )
                    embedding_repo.create(embedding_data)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to create embeddings: {e}")
        
        return document
    
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise AgentError(f"Document generation failed: {str(e)}")

@router.post("/update", response_model=models.DocumentResponse)
async def update_document_section(
    request: DocumentUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    update_embeddings: bool = Query(True, description="Update embeddings after content change")
):
    """
    Update a specific section of a document using the maintenance agent.
    Requires authentication.
    
    The agent will:
    1. Fetch relevant context from the document and related docs
    2. Update the specified section intelligently
    3. Ensure technical consistency
    4. Create a new version
    5. Optionally update embeddings
    """
    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    maintenance_agent = MaintenanceAgent()
    vector_store = VectorStore()
    
    # Check if document exists
    document = doc_repo.get_by_id(request.doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has permission (creator or admin)
    if document.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )
    
    try:
        # Store old content for versioning
        old_content = document.content
        
        # Use maintenance agent to update the section
        update_result = await maintenance_agent.update_document(
            current_content=document.content,
            section=request.section,
            new_content=request.new_content,
            reason=f"Section '{request.section}' update",
            doc_id=request.doc_id
        )
        
        # Update document in database
        update_data = models.DocumentUpdate(content=update_result["updated_content"])
        updated_document = doc_repo.update(request.doc_id, update_data)
        
        if not updated_document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )
        
        # Create new version with diff
        diff = f"Section '{request.section}' updated. Context used: {update_result['context_used']} chunks. Reason: {update_result['reason']}"
        
        version_repo.create(
            doc_id=request.doc_id,
            content=updated_document.content,
            user_id=current_user.id,
            diff=diff
        )
        
        # Update embeddings if content changed significantly
        if update_embeddings and updated_document.content != old_content:
            try:
                # Delete old embeddings
                from src.db.repository import EmbeddingRepository
                embedding_repo = EmbeddingRepository(db)
                await vector_store.delete_document_vectors(request.doc_id)
                embedding_repo.delete_by_doc_id(request.doc_id)
                
                # Create new embeddings
                await vector_store.store_document(
                    doc_id=request.doc_id,
                    text=updated_document.content,
                    chunk_size=1000,
                    chunk_overlap=200
                )
                
                # Store embedding records in database
                chunks = []
                start = 0
                chunk_size = 1000
                chunk_overlap = 200
                while start < len(updated_document.content):
                    end = start + chunk_size
                    chunk = updated_document.content[start:end]
                    chunks.append(chunk)
                    start = end - chunk_overlap
                
                for i, chunk in enumerate(chunks):
                    vector_id = f"{request.doc_id}_chunk_{i}"
                    embedding_data = models.EmbeddingCreate(
                        doc_id=request.doc_id,
                        chunk_text=chunk,
                        chunk_index=i,
                        vector_id=vector_id
                    )
                    embedding_repo.create(embedding_data)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to update embeddings: {e}")
        
        return updated_document
    
    except (DocumentNotFoundError, UnauthorizedError, ValidationError):
        raise
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise AgentError(f"Document update failed: {str(e)}")

@router.post("/{doc_id}/audit")
async def audit_document(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Audit a document for outdated content and inconsistencies using the maintenance agent.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    maintenance_agent = MaintenanceAgent()
    
    # Check if document exists
    document = doc_repo.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Audit the document
        audit_result = await maintenance_agent.audit_document(
            content=document.content,
            doc_id=doc_id
        )
        
        return {
            "doc_id": doc_id,
            "audit_results": audit_result,
            "message": "Document audit completed"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit document: {str(e)}"
        )
