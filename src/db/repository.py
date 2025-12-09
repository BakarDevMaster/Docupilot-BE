"""
Database repository pattern for data access using SQLModel.
"""
from sqlmodel import Session, select
from typing import List, Optional
from src.db import models

class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document: models.DocumentCreate, user_id: str) -> models.Document:
        """Create a new document."""
        db_document = models.Document(
            **document.model_dump(),
            created_by=user_id
        )
        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)
        return db_document
    
    def get_by_id(self, doc_id: str) -> Optional[models.Document]:
        """Get document by ID."""
        return self.db.get(models.Document, doc_id)
    
    def get_all(self, skip: int = 0, limit: int = 100, user_id: Optional[str] = None) -> List[models.Document]:
        """Get all documents with pagination. Optionally filter by user."""
        statement = select(models.Document)
        if user_id:
            statement = statement.where(models.Document.created_by == user_id)
        statement = statement.offset(skip).limit(limit).order_by(models.Document.created_at.desc())
        return list(self.db.exec(statement))
    
    def update(self, doc_id: str, document: models.DocumentUpdate) -> Optional[models.Document]:
        """Update a document."""
        db_document = self.get_by_id(doc_id)
        if not db_document:
            return None
        
        update_data = document.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)
        
        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)
        return db_document
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        db_document = self.get_by_id(doc_id)
        if not db_document:
            return False
        
        self.db.delete(db_document)
        self.db.commit()
        return True

class DocumentVersionRepository:
    """Repository for document version operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        doc_id: str,
        content: str,
        user_id: str,
        diff: Optional[str] = None
    ) -> models.DocumentVersion:
        """Create a new document version."""
        # Get the latest version number
        statement = select(models.DocumentVersion).where(
            models.DocumentVersion.doc_id == doc_id
        ).order_by(models.DocumentVersion.version_number.desc())
        
        latest_version = self.db.exec(statement).first()
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        db_version = models.DocumentVersion(
            doc_id=doc_id,
            version_number=version_number,
            content=content,
            diff=diff,
            updated_by=user_id
        )
        self.db.add(db_version)
        self.db.commit()
        self.db.refresh(db_version)
        return db_version
    
    def get_by_doc_id(self, doc_id: str) -> List[models.DocumentVersion]:
        """Get all versions for a document."""
        statement = select(models.DocumentVersion).where(
            models.DocumentVersion.doc_id == doc_id
        ).order_by(models.DocumentVersion.version_number.desc())
        return list(self.db.exec(statement))
    
    def get_version(self, doc_id: str, version_number: int) -> Optional[models.DocumentVersion]:
        """Get a specific version of a document."""
        statement = select(models.DocumentVersion).where(
            models.DocumentVersion.doc_id == doc_id,
            models.DocumentVersion.version_number == version_number
        )
        return self.db.exec(statement).first()

class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: models.UserCreate, hashed_password: str) -> models.User:
        """Create a new user."""
        db_user = models.User(
            name=user.name,
            email=user.email,
            role=user.role,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_by_email(self, email: str) -> Optional[models.User]:
        """Get user by email."""
        statement = select(models.User).where(models.User.email == email)
        return self.db.exec(statement).first()
    
    def get_by_id(self, user_id: str) -> Optional[models.User]:
        """Get user by ID."""
        return self.db.get(models.User, user_id)

class EmbeddingRepository:
    """Repository for embedding operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, embedding: models.EmbeddingCreate) -> models.Embedding:
        """Create a new embedding record."""
        db_embedding = models.Embedding(**embedding.model_dump())
        self.db.add(db_embedding)
        self.db.commit()
        self.db.refresh(db_embedding)
        return db_embedding
    
    def get_by_doc_id(self, doc_id: str) -> List[models.Embedding]:
        """Get all embeddings for a document."""
        statement = select(models.Embedding).where(
            models.Embedding.doc_id == doc_id
        ).order_by(models.Embedding.chunk_index)
        return list(self.db.exec(statement))
    
    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all embeddings for a document."""
        statement = select(models.Embedding).where(models.Embedding.doc_id == doc_id)
        embeddings = list(self.db.exec(statement))
        for embedding in embeddings:
            self.db.delete(embedding)
        self.db.commit()
        return len(embeddings)
