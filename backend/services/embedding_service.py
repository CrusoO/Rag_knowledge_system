"""
Embedding service for creating vector embeddings using sentence-transformers
Optimized with model caching, batch processing, and efficient memory usage
"""

import asyncio
import logging
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    High-performance embedding service with caching and batch optimization
    """
    
    BATCH_SIZE = 32
    MODEL_NAME = 'all-MiniLM-L6-v2'
    
    def __init__(self):
        logger.info(f"Initializing embedding model: {self.MODEL_NAME}")
        self.model = self._get_model()
        logger.info("Embedding model loaded successfully")

    @classmethod
    @lru_cache(maxsize=1)
    def _get_model(cls) -> SentenceTransformer:
        """
        Get or create cached model instance
        """
        return SentenceTransformer(cls.MODEL_NAME)

    async def create_embeddings(
        self,
        chunks: List[Dict],
        batch_size: int = BATCH_SIZE,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Create embeddings for text chunks with batch processing
        
        Args:
            chunks: List of text chunks with metadata
            batch_size: Number of texts to process in each batch
            show_progress: Whether to log progress
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk["text"] for chunk in chunks]
        
        if not texts:
            return []
        
        logger.info(f"Creating embeddings for {len(texts)} chunks")
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            self._encode_batch,
            texts,
            batch_size,
            show_progress
        )
        
        logger.info(f"Successfully created {len(embeddings)} embeddings")
        return embeddings.tolist()

    def _encode_batch(
        self,
        texts: List[str],
        batch_size: int,
        show_progress: bool
    ):
        """
        Encode texts in batches for memory efficiency
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    async def create_query_embedding(self, query: str) -> List[float]:
        """
        Create embedding for a single query (optimized for speed)
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self._encode_single,
            query.strip()
        )
        
        return embedding.tolist()

    def _encode_single(self, text: str):
        """
        Encode single text efficiently
        """
        return self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

