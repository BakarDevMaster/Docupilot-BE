"""
Free embedding service using Hugging Face sentence-transformers.
Supports both local models and Hugging Face Inference API.
"""
from typing import List, Optional
import os
from sentence_transformers import SentenceTransformer
import requests

class EmbeddingService:
    """
    Service for generating embeddings using free models.
    Supports Hugging Face sentence-transformers (local) or Inference API.
    """
    
    def __init__(self):
        self.use_api = os.getenv("USE_HF_API", "false").lower() == "true"
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        if self.use_api:
            # Use Hugging Face Inference API
            if not self.api_key:
                raise ValueError("HUGGINGFACE_API_KEY required when using API mode")
            self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        else:
            # Use local sentence-transformers model
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise ValueError(f"Failed to load embedding model: {e}")
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        if self.use_api:
            return await self._get_embeddings_api(texts)
        else:
            return await self._get_embeddings_local(texts)
    
    async def _get_embeddings_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local sentence-transformers model."""
        # Run in executor to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            lambda: self.model.encode(texts, convert_to_numpy=True)
        )
        return embeddings.tolist()
    
    async def _get_embeddings_api(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Hugging Face Inference API."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json={"inputs": texts}
        )
        
        if response.status_code != 200:
            raise ValueError(f"Embedding API error: {response.text}")
        
        return response.json()
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        Common dimensions:
        - all-MiniLM-L6-v2: 384
        - all-mpnet-base-v2: 768
        """
        # Default for all-MiniLM-L6-v2
        dimension_map = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/paraphrase-MiniLM-L6-v2": 384,
        }
        return dimension_map.get(self.model_name, 384)

