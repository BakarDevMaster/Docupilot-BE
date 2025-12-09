"""
Vector store service that combines Pinecone and embedding models.
Supports two modes:
- Default: local/HF embeddings (EmbeddingService)
- Managed: Pinecone-managed embeddings (using index model)
"""
from typing import List, Dict, Optional
from src.services.pinecone_service import PineconeService
from src.services.embedding_service import EmbeddingService
import os
import asyncio


class ManagedPineconeEmbeddingService:
    """
    Uses Pinecone's managed embedding inference (server-side, matches index model).
    """

    def __init__(self):
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY is required for managed embeddings")

        # If not provided, default to the index's built-in model (llama-text-embed-v2)
        self.model_name = os.getenv("PINECONE_MANAGED_MODEL", "llama-text-embed-v2")
        self.pc = Pinecone(api_key=api_key)

    async def get_embeddings(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """
        Generate embeddings using Pinecone-managed model.
        """
        loop = asyncio.get_event_loop()

        def _embed():
            resp = self.pc.inference.embed(
                model=self.model_name,
                inputs=texts,
                parameters={"input_type": input_type}
            )
            # Handle EmbeddingsList or dict formats
            # Pinecone Inference returns EmbeddingsList with .data list items
            if hasattr(resp, "data"):
                embeddings = []
                for item in resp.data:
                    if isinstance(item, dict):
                        vals = item.get("values") or item.get("embedding") or []
                    else:
                        vals = getattr(item, "values", None) or getattr(item, "embedding", None) or []
                    embeddings.append(vals)
                return embeddings
            if isinstance(resp, dict) and "data" in resp:
                return [item.get("values", []) for item in resp["data"]]
            raise ValueError(f"Unexpected embed response format: {resp}")

        return await loop.run_in_executor(None, _embed)


class VectorStore:
    """
    High-level vector store service that handles:
    - Chunking documents
    - Generating embeddings (local/HF or Pinecone-managed)
    - Storing in Pinecone
    - Retrieving similar content
    """
    
    def __init__(self):
        self.pinecone = PineconeService()
        self.use_managed = os.getenv("PINECONE_USE_MANAGED", "false").lower() == "true"
        if self.use_managed:
            self.embedding_service = ManagedPineconeEmbeddingService()
        else:
            self.embedding_service = EmbeddingService()
    
    async def store_document(
        self,
        doc_id: str,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """
        Store a document by chunking it and storing embeddings.
        
        Args:
            doc_id: Document ID
            text: Document text content
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
        
        Returns:
            List of vector IDs created
        """
        # Chunk the document
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        
        # Generate embeddings (managed or local)
        if self.use_managed:
            embeddings = await self.embedding_service.get_embeddings(chunks, input_type="passage")
        else:
            embeddings = await self.embedding_service.get_embeddings(chunks)
        
        # Prepare vectors for Pinecone
        vectors = []
        vector_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{doc_id}_chunk_{i}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "chunk_text": chunk[:500]  # Store first 500 chars for preview
                }
            })
            vector_ids.append(vector_id)
        
        # Store in Pinecone
        await self.pinecone.upsert_vectors(vectors)
        
        return vector_ids
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        doc_id_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar document chunks.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            doc_id_filter: Optional document ID to filter by
        
        Returns:
            List of similar chunks with metadata
        """
        # Generate query embedding
        if self.use_managed:
            query_embeddings = await self.embedding_service.get_embeddings([query], input_type="query")
        else:
            query_embeddings = await self.embedding_service.get_embeddings([query])
        query_vector = query_embeddings[0]
        
        # Build filter if doc_id provided
        filter_dict = None
        if doc_id_filter:
            filter_dict = {"doc_id": {"$eq": doc_id_filter}}
        
        # Query Pinecone
        results = await self.pinecone.query(
            query_vector=query_vector,
            top_k=top_k,
            filter=filter_dict
        )
        
        return results
    
    async def delete_document_vectors(self, doc_id: str) -> None:
        """
        Delete all vectors for a document.
        
        Args:
            doc_id: Document ID
        """
        filter_dict = {"doc_id": {"$eq": doc_id}}
        await self.pinecone.delete_by_filter(filter_dict)
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - chunk_overlap
        
        return chunks

