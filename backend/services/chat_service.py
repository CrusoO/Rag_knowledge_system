"""
Chat service for generating intelligent responses using RAG with Groq
Optimized for performance with caching and efficient context building
"""

import os
import logging
from typing import List, Dict, Optional
from groq import AsyncGroq
from functools import lru_cache

logger = logging.getLogger(__name__)


class ChatService:
    """
    Conversational service that retrieves relevant context and generates responses
    """
    
    MAX_CONTEXT_LENGTH = 4000
    MAX_RESPONSE_TOKENS = 1000
    TOP_K_RESULTS = 5
    
    def __init__(self, embedding_service, vector_store):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
            
        self.client = AsyncGroq(api_key=api_key)
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"Chat service initialized with model: {self.model}")

    async def generate_response(
        self,
        user_id: str,
        message: str,
        top_k: int = TOP_K_RESULTS
    ) -> Dict[str, any]:
        """
        Generate contextual response using semantic search and language model
        
        Args:
            user_id: User identifier for filtering relevant documents
            message: User query
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dict containing response content and source references
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
            
        logger.info(f"Generating response for user: {user_id}")
        
        query_embedding = await self.embedding_service.create_query_embedding(message)

        relevant_chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=top_k
        )

        if not relevant_chunks:
            logger.info(f"No relevant documents found for user: {user_id}")
            return {
                "content": "I don't have any relevant information to answer your question. Please upload some documents first, and I'll be able to help you better.",
                "sources": []
            }

        context = self._build_context(relevant_chunks)
        system_prompt = self._get_system_prompt(context)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=self.MAX_RESPONSE_TOKENS,
                top_p=0.9
            )
            
            content = response.choices[0].message.content
            logger.info(f"Successfully generated response ({len(content)} chars)")
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise

        sources = self._format_sources(relevant_chunks)

        return {
            "content": content,
            "sources": sources
        }

    def _build_context(self, chunks: List[Dict], max_length: int = MAX_CONTEXT_LENGTH) -> str:
        """
        Build optimized context string from relevant chunks
        Ensures context stays within token limits
        """
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(chunks, 1):
            chunk_text = chunk['text']
            source_label = f"[Source {i} - {chunk['filename']}]\n{chunk_text}\n\n"
            
            if current_length + len(source_label) > max_length:
                break
                
            context_parts.append(source_label)
            current_length += len(source_label)

        return "".join(context_parts).strip()

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_system_prompt(context: str) -> str:
        """
        Get system prompt with context (cached for performance)
        """
        return f"""You are Cruso, an intelligent document assistant powered by advanced retrieval and language technology.

Your role is to provide accurate, helpful answers based on the user's uploaded documents.

Guidelines:
- Answer questions accurately using the provided context
- Be conversational, clear, and concise
- If the context lacks information, acknowledge limitations
- Cite sources when referencing specific information
- Maintain a professional yet friendly tone
- Never make up information not present in the context

Context from user documents:
{context}
"""

    @staticmethod
    def _format_sources(chunks: List[Dict]) -> List[Dict[str, any]]:
        """
        Format source references for response
        """
        return [
            {
                "documentName": chunk["filename"],
                "excerpt": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "relevance": round(chunk["score"], 3),
            }
            for chunk in chunks[:3]
        ]

