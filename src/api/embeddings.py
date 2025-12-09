from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field, validator, root_validator
from sqlmodel import Session
from typing import List, Optional
from src.db.database import get_db
from src.db import models
from src.db.repository import EmbeddingRepository, DocumentRepository
from src.api.auth import get_current_user
from src.services.vector_store import VectorStore
from src.utils.exceptions import (
    DocumentNotFoundError,
    UnauthorizedError,
    ValidationError,
    EmbeddingError
)
from src.utils.validators import validate_chunk_size, validate_top_k

router = APIRouter()

# Request/Response models
class EmbeddingCreateRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID")
    text: Optional[str] = Field(None, min_length=10, description="Full document text (auto-chunked)")
    chunks: Optional[List[str]] = Field(None, description="Pre-chunked text (optional)")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, le=500, description="Chunk overlap in characters")
    
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        return validate_chunk_size(v)
    
    @validator('text', 'chunks', always=True)
    def validate_text_or_chunks(cls, v, values):
        # This validator runs for both fields, but we check in root_validator
        return v
    
    @classmethod
    def root_validator(cls, values):
        if not values.get('text') and not values.get('chunks'):
            raise ValueError("Either 'text' or 'chunks' must be provided")
        return values

class EmbeddingSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    doc_id: Optional[str] = Field(None, description="Optional filter by document ID")
    
    @validator('top_k')
    def validate_top_k(cls, v):
        return validate_top_k(v)

class EmbeddingSearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    chunk_text: str
    chunk_index: int
    score: float

class EmbeddingSearchResponse(BaseModel):
    query: str
    results: List[EmbeddingSearchResult]
    total_results: int

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_embeddings(
    request: EmbeddingCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store chunked embeddings in Pinecone and database.
    Requires authentication.
    
    Either provide 'text' (will be auto-chunked) or 'chunks' (pre-chunked).
    """
    doc_repo = DocumentRepository(db)
    embedding_repo = EmbeddingRepository(db)
    vector_store = VectorStore()
    
    # Verify document exists
    document = doc_repo.get_by_id(request.doc_id)
    if not document:
        raise DocumentNotFoundError(request.doc_id)
    
    # Check if user has permission (creator or admin)
    if document.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise UnauthorizedError("Not authorized to create embeddings for this document")
    
    # Delete existing embeddings if any
    existing_embeddings = embedding_repo.get_by_doc_id(request.doc_id)
    if existing_embeddings:
        # Delete from Pinecone
        await vector_store.delete_document_vectors(request.doc_id)
        # Delete from database
        embedding_repo.delete_by_doc_id(request.doc_id)
    
    try:
        if request.text:
            # Auto-chunk the text and store
            vector_ids = await vector_store.store_document(
                doc_id=request.doc_id,
                text=request.text,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap
            )
            
            # Get chunks for database storage (re-chunk to match what was stored)
            # We need to chunk the same way VectorStore does it
            chunks = []
            start = 0
            while start < len(request.text):
                end = start + request.chunk_size
                chunk = request.text[start:end]
                chunks.append(chunk)
                start = end - request.chunk_overlap
        elif request.chunks:
            # Use pre-chunked text
            chunks = request.chunks
            # Generate embeddings for chunks
            embeddings = await vector_store.embedding_service.get_embeddings(chunks)
            
            # Store in Pinecone
            vectors = []
            vector_ids = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{request.doc_id}_chunk_{i}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "doc_id": request.doc_id,
                        "chunk_index": i,
                        "chunk_text": chunk[:500]
                    }
                })
                vector_ids.append(vector_id)
            
            await vector_store.pinecone.upsert_vectors(vectors)
        else:
            raise ValidationError("Either 'text' or 'chunks' must be provided")
        
        # Store embedding records in database
        created_embeddings = []
        for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
            embedding_data = models.EmbeddingCreate(
                doc_id=request.doc_id,
                chunk_text=chunk,
                chunk_index=i,
                vector_id=vector_id
            )
            embedding = embedding_repo.create(embedding_data)
            created_embeddings.append(embedding)
        
        return {
            "message": "Embeddings created successfully",
            "doc_id": request.doc_id,
            "chunks_count": len(chunks),
            "vector_ids": vector_ids
        }
    
    except (DocumentNotFoundError, UnauthorizedError, ValidationError):
        raise
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise EmbeddingError(f"Failed to create embeddings: {str(e)}")

@router.post("/search", response_model=EmbeddingSearchResponse)
async def search_embeddings(
    request: EmbeddingSearchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for similar document chunks using vector similarity.
    Requires authentication.
    """
    vector_store = VectorStore()
    embedding_repo = EmbeddingRepository(db)
    
    # If doc_id filter is provided, verify document exists
    if request.doc_id:
        doc_repo = DocumentRepository(db)
        document = doc_repo.get_by_id(request.doc_id)
        if not document:
            raise DocumentNotFoundError(request.doc_id)
    
    try:
        # Search for similar chunks
        results = await vector_store.search_similar(
            query=request.query,
            top_k=request.top_k,
            doc_id_filter=request.doc_id
        )
        
        # Format results
        search_results = []
        for match in results:
            # Get full chunk text from database if available
            vector_id = match.get("id", "")
            chunk_text = match.get("metadata", {}).get("chunk_text", "")
            chunk_index = match.get("metadata", {}).get("chunk_index", 0)
            doc_id = match.get("metadata", {}).get("doc_id", "")
            score = match.get("score", 0.0)
            
            # Try to get full chunk text from database
            if doc_id:
                embeddings = embedding_repo.get_by_doc_id(doc_id)
                for emb in embeddings:
                    if emb.vector_id == vector_id:
                        chunk_text = emb.chunk_text
                        break
            
            search_results.append(EmbeddingSearchResult(
                chunk_id=vector_id,
                doc_id=doc_id,
                chunk_text=chunk_text,
                chunk_index=chunk_index,
                score=score
            ))
        
        return EmbeddingSearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
    
    except (DocumentNotFoundError, ValidationError):
        raise
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise EmbeddingError(f"Search failed: {str(e)}")

@router.get("/doc/{doc_id}", response_model=List[models.EmbeddingResponse])
async def get_document_embeddings(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all embeddings for a specific document.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    # Verify document exists
    document = doc_repo.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get embeddings
    embeddings = embedding_repo.get_by_doc_id(doc_id)
    return embeddings

@router.delete("/doc/{doc_id}")
async def delete_document_embeddings(
    doc_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete all embeddings for a specific document from both Pinecone and database.
    Requires authentication.
    """
    doc_repo = DocumentRepository(db)
    embedding_repo = EmbeddingRepository(db)
    vector_store = VectorStore()
    
    # Verify document exists
    document = doc_repo.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has permission (creator or admin)
    if document.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise UnauthorizedError("Not authorized to delete embeddings for this document")
    
    try:
        # Delete from Pinecone
        await vector_store.delete_document_vectors(doc_id)
        
        # Delete from database
        deleted_count = embedding_repo.delete_by_doc_id(doc_id)
        
        return {
            "message": "Embeddings deleted successfully",
            "doc_id": doc_id,
            "deleted_count": deleted_count
        }
    
    except (DocumentNotFoundError, UnauthorizedError):
        raise
    except Exception as e:
        raise EmbeddingError(f"Failed to delete embeddings: {str(e)}")
