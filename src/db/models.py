"""
Database models using SQLModel ORM.
SQLModel combines SQLAlchemy and Pydantic for type-safe database models.
"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import enum
import uuid

if TYPE_CHECKING:
    from typing import List

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TECHNICAL_WRITER = "technical_writer"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class UserBase(SQLModel):
    name: str
    email: str = Field(unique=True, index=True)
    role: UserRole = Field(default=UserRole.VIEWER)

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    documents: List["Document"] = Relationship(back_populates="creator")
    document_versions: List["DocumentVersion"] = Relationship(back_populates="updater")

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

class DocumentBase(SQLModel):
    title: str = Field(index=True)
    content: str
    doc_type: str = Field(default="api")

class Document(DocumentBase, table=True):
    __tablename__ = "documents"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    creator: Optional["User"] = Relationship(back_populates="documents")
    versions: List["DocumentVersion"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    embeddings: List["Embedding"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

class DocumentVersionBase(SQLModel):
    version_number: int
    content: str
    diff: Optional[str] = None  # JSON string of changes

class DocumentVersion(DocumentVersionBase, table=True):
    __tablename__ = "document_versions"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    doc_id: str = Field(foreign_key="documents.id")
    updated_by: str = Field(foreign_key="users.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    document: Optional["Document"] = Relationship(back_populates="versions")
    updater: Optional["User"] = Relationship(back_populates="document_versions")

class DocumentVersionResponse(DocumentVersionBase):
    id: str
    doc_id: str
    updated_by: str
    timestamp: datetime

class EmbeddingBase(SQLModel):
    chunk_text: str
    chunk_index: int
    vector_id: str = Field(unique=True)  # Pinecone vector ID

class Embedding(EmbeddingBase, table=True):
    __tablename__ = "embeddings"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    doc_id: str = Field(foreign_key="documents.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    document: Optional["Document"] = Relationship(back_populates="embeddings")

class EmbeddingCreate(EmbeddingBase):
    doc_id: str

class EmbeddingResponse(EmbeddingBase):
    id: str
    doc_id: str
    created_at: datetime
