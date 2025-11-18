"""
Vector store service using Pinecone for efficient embedding storage and retrieval
Optimized with connection pooling and batch operations
"""

import os
import logging
from typing import List, Dict, Optional
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)


class VectorStore:
    """
    High-performance vector storage with optimized search and upsert operations
    """
    
    EMBEDDING_DIMENSION = 384
    BATCH_SIZE = 100
    DEFAULT_TOP_K = 5
    
    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
            
        self.api_key = api_key
        self.environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = os.getenv("PINECONE_INDEX", "cruso-documents")

        logger.info(f"Initializing Pinecone vector store: {self.index_name}")
        self.pc = Pinecone(api_key=self.api_key)

        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)
        logger.info("Vector store initialized successfully")
    
    def _ensure_index_exists(self):
        """
        Create index if it doesn't exist
        """
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            logger.info(f"Creating new index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=os.getenv("PINECONE_CLOUD", "aws"),
                    region=os.getenv("PINECONE_REGION", "us-east-1")
                )
            )
            logger.info(f"Index {self.index_name} created successfully")

    async def store_embeddings(
        self,
        document_id: str,
        user_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]],
        metadata: Dict,
    ) -> Dict[str, any]:
        """
        Store embeddings in Pinecone with optimized batch upserts
        
        Args:
            document_id: Unique document identifier
            user_id: User identifier
            chunks: Text chunks with metadata
            embeddings: Embedding vectors
            metadata: Additional document metadata
            
        Returns:
            Dict with upsert statistics
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings length mismatch")
        
        logger.info(f"Storing {len(embeddings)} embeddings for document: {document_id}")
        
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{document_id}_{i}"
            vector_metadata = {
                "user_id": user_id,
                "document_id": document_id,
                "filename": metadata.get("filename", ""),
                "chunk_index": i,
                "text": chunk["text"][:1000],
            }

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": vector_metadata,
            })

        upserted_count = 0
        for i in range(0, len(vectors), self.BATCH_SIZE):
            batch = vectors[i:i + self.BATCH_SIZE]
            self.index.upsert(vectors=batch)
            upserted_count += len(batch)
            
        logger.info(f"Successfully upserted {upserted_count} vectors")
        return {"upserted": upserted_count}

    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: int = DEFAULT_TOP_K,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar vectors with relevance filtering
        
        Args:
            query_embedding: Query vector
            user_id: User identifier for filtering
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of matching documents with metadata
        """
        try:
            results = self.index.query(
                vector=query_embedding,
                filter={"user_id": user_id},
                top_k=top_k,
                include_metadata=True
            )
            
            matches = [
                {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "filename": match.metadata.get("filename", "Unknown"),
                    "document_id": match.metadata.get("document_id", ""),
                    "chunk_index": match.metadata.get("chunk_index", 0)
                }
                for match in results.matches
                if match.score >= min_score
            ]
            
            logger.info(f"Found {len(matches)} relevant documents")
            return matches
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    async def delete_document(
        self,
        document_id: str,
        user_id: str
    ) -> Dict[str, any]:
        """
        Delete all vectors for a document
        
        Args:
            document_id: Document identifier
            user_id: User identifier
            
        Returns:
            Dict with deletion status
        """
        try:
            self.index.delete(
                filter={
                    "document_id": document_id,
                    "user_id": user_id
                }
            )
            logger.info(f"Deleted vectors for document: {document_id}")
            return {"status": "deleted", "document_id": document_id}
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            raise

