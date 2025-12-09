"""
Pinecone vector database service.
"""
from typing import List, Dict, Optional
import os
from pinecone import Pinecone

class PineconeService:
    """
    Service for interacting with Pinecone vector database.
    Handles embedding storage, retrieval, and search.
    """
    
    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            # Don't raise error immediately - allow service to be created but warn
            # This allows the app to start even if Pinecone isn't configured
            self.pc = None
            self.index = None
            self.index_name = os.getenv("PINECONE_INDEX_NAME", "docupilot-docs")
            return
        
        try:
            self.pc = Pinecone(api_key=api_key)
            self.index_name = os.getenv("PINECONE_INDEX_NAME", "docupilot-docs")
            self._ensure_index()
        except Exception as e:
            # If Pinecone initialization fails, set to None but don't crash
            print(f"Warning: Pinecone initialization failed: {e}")
            self.pc = None
            self.index = None
    
    def _ensure_index(self):
        """Ensure the Pinecone index exists, create if it doesn't."""
        if not self.pc:
            return
            
        try:
            # Try to connect to the index
            self.index = self.pc.Index(self.index_name)
            # Test connection by getting index stats
            self.index.describe_index_stats()
        except Exception as e:
            # Index doesn't exist or connection failed, create it
            # Get embedding dimension from environment or default to 384 (all-MiniLM-L6-v2)
            embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))
            
            # Try to dynamically get dimension from embedding service
            try:
                from src.services.embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                embedding_dim = embedding_service.get_embedding_dimension()
            except Exception:
                # Fall back to environment variable
                pass
            
            # Create index using the new API
            # Try different methods for different Pinecone SDK versions
            try:
                # Method 1: Try with ServerlessSpec (older versions)
                from pinecone import ServerlessSpec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=embedding_dim,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=os.getenv("PINECONE_REGION", "us-east-1")
                    )
                )
            except (ImportError, TypeError, AttributeError):
                try:
                    # Method 2: Try with dict format (newer versions)
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=embedding_dim,
                        metric="cosine",
                        spec={
                            "serverless": {
                                "cloud": "aws",
                                "region": os.getenv("PINECONE_REGION", "us-east-1")
                            }
                        }
                    )
                except Exception as create_error:
                    # If creation fails, log and continue - index might already exist
                    print(f"Warning: Could not create Pinecone index: {create_error}")
                    # Try to connect anyway in case it exists
                    try:
                        self.index = self.pc.Index(self.index_name)
                    except:
                        pass
                    return
            
            # Wait a moment for index to be ready, then connect
            import time
            time.sleep(2)
            try:
                self.index = self.pc.Index(self.index_name)
            except Exception as connect_error:
                print(f"Warning: Could not connect to Pinecone index: {connect_error}")
                self.index = None
    
    async def upsert_vectors(
        self,
        vectors: List[Dict],
        namespace: Optional[str] = None
    ) -> None:
        """
        Upsert vectors into Pinecone.
        
        Args:
            vectors: List of dicts with 'id', 'values', and 'metadata'
            namespace: Optional namespace for the vectors
        """
        if not self.index:
            raise ValueError("Pinecone is not configured. Set PINECONE_API_KEY environment variable.")
        self.index.upsert(vectors=vectors, namespace=namespace)
    
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query similar vectors from Pinecone.
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            namespace: Optional namespace to search in
            filter: Optional metadata filter
        
        Returns:
            List of matching vectors with scores
        """
        if not self.index:
            return []  # Return empty list if Pinecone not configured
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_metadata=True
        )
        return results.get("matches", [])
    
    async def delete_vectors(
        self,
        ids: List[str],
        namespace: Optional[str] = None
    ) -> None:
        """
        Delete vectors by IDs.
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
        """
        if not self.index:
            return  # Silently return if Pinecone not configured
        if ids:
            self.index.delete(ids=ids, namespace=namespace)
    
    async def delete_by_filter(
        self,
        filter: Dict,
        namespace: Optional[str] = None
    ) -> None:
        """
        Delete vectors by metadata filter.
        
        Args:
            filter: Metadata filter dict
            namespace: Optional namespace
        """
        if not self.index:
            return  # Silently return if Pinecone not configured
        self.index.delete(filter=filter, namespace=namespace)

