"""
FastAPI backend for Cruso - Intelligent Document Assistant
Handles document processing, embeddings, vector storage, and conversational queries
Optimized for performance with caching, connection pooling, and async operations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.chat_service import ChatService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    logger.info("Initializing Cruso services...")
    try:
        services["document_processor"] = DocumentProcessor()
        services["embedding_service"] = EmbeddingService()
        services["vector_store"] = VectorStore()
        services["chat_service"] = ChatService(
            services["embedding_service"],
            services["vector_store"]
        )
        logger.info("All services initialized successfully")
        yield
    finally:
        logger.info("Shutting down Cruso services...")
        services.clear()


app = FastAPI(
    title="Cruso API",
    description="Intelligent Document Assistant powered by RAG",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)


class ProcessDocumentRequest(BaseModel):
    documentId: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    filepath: str = Field(..., description="Path to uploaded file")
    userId: str = Field(..., description="User identifier")


class ChatRequest(BaseModel):
    userId: str = Field(..., description="User identifier")
    message: str = Field(..., min_length=1, max_length=2000, description="User query")


class ChatResponse(BaseModel):
    content: str = Field(..., description="Assistant response")
    sources: List[Dict] = Field(default=[], description="Referenced document sources")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Cruso API",
        "description": "Intelligent Document Assistant",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "embedding": services.get("embedding_service") is not None,
            "vector_store": services.get("vector_store") is not None,
            "chat": services.get("chat_service") is not None
        }
    }


@app.post("/api/process-document", tags=["Documents"])
async def process_document(request: ProcessDocumentRequest):
    """
    Process document: extract text, create embeddings, and store in vector database
    Optimized for batch processing with efficient memory usage
    """
    try:
        logger.info(f"Processing document: {request.filename} for user: {request.userId}")
        
        chunks = await services["document_processor"].process_file(
            request.filepath,
            request.filename,
            request.documentId
        )
        
        logger.info(f"Created {len(chunks)} chunks from document")

        embeddings = await services["embedding_service"].create_embeddings(chunks)

        await services["vector_store"].store_embeddings(
            document_id=request.documentId,
            user_id=request.userId,
            chunks=chunks,
            embeddings=embeddings,
            metadata={
                "filename": request.filename,
                "document_id": request.documentId,
            }
        )
        
        logger.info(f"Successfully processed document: {request.documentId}")

        return {
            "status": "success",
            "documentId": request.documentId,
            "chunks": len(chunks),
            "message": f"Document processed successfully with {len(chunks)} chunks"
        }
    except ValueError as e:
        logger.error(f"Validation error processing document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Conversational query with context retrieval
    Uses semantic search to find relevant document chunks and generates intelligent responses
    """
    try:
        logger.info(f"Chat request from user: {request.userId}")
        
        response = await services["chat_service"].generate_response(
            user_id=request.userId,
            message=request.message
        )
        
        logger.info(f"Generated response for user: {request.userId}")
        return response
    except ValueError as e:
        logger.error(f"Validation error in chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@app.delete("/api/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str, user_id: str):
    """
    Delete document and all associated embeddings from vector store
    """
    try:
        logger.info(f"Deleting document: {document_id} for user: {user_id}")
        
        await services["vector_store"].delete_document(document_id, user_id)
        
        logger.info(f"Successfully deleted document: {document_id}")
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

