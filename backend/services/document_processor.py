"""
Document processing service for extracting and chunking text from various file formats
Optimized for memory efficiency and intelligent chunking
"""

import os
import logging
from typing import List, Dict, Tuple
from PyPDF2 import PdfReader
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    High-performance document processor with intelligent text chunking
    """
    
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    MIN_CHUNK_SIZE = 100
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        if chunk_size < self.MIN_CHUNK_SIZE:
            raise ValueError(f"Chunk size must be at least {self.MIN_CHUNK_SIZE}")
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Document processor initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")

    async def process_file(
        self,
        filepath: str,
        filename: str,
        document_id: str
    ) -> List[Dict]:
        """
        Process file and extract text chunks with metadata
        
        Args:
            filepath: Path to file
            filename: Original filename
            document_id: Unique document identifier
            
        Returns:
            List of chunks with metadata
        """
        logger.info(f"Processing file: {filename}")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        text = await self._extract_text(filepath, filename)
        
        if not text or not text.strip():
            raise ValueError(f"No text extracted from file: {filename}")
        
        chunks = self._chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks from {filename}")

        return [
            {
                "text": chunk,
                "document_id": document_id,
                "filename": filename,
                "chunk_index": idx,
                "char_count": len(chunk)
            }
            for idx, chunk in enumerate(chunks)
        ]

    async def _extract_text(self, filepath: str, filename: str) -> str:
        """
        Extract text from file based on file type
        """
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension == ".pdf":
            return self._extract_from_pdf(filepath)
        elif file_extension in [".txt", ".md", ".markdown"]:
            return self._extract_from_text(filepath)
        else:
            raise ValueError(
                f"Unsupported file type: {file_extension}. "
                f"Supported formats: .pdf, .txt, .md, .markdown"
            )

    def _extract_from_pdf(self, filepath: str) -> str:
        """
        Extract text from PDF file with improved error handling
        """
        try:
            reader = PdfReader(filepath)
            
            if len(reader.pages) == 0:
                raise ValueError("PDF file has no pages")
            
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {str(e)}")
                    continue
            
            if not text_parts:
                raise ValueError("No text could be extracted from PDF")
            
            logger.info(f"Extracted text from {len(text_parts)} pages")
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to extract PDF: {str(e)}")

    def _extract_from_text(self, filepath: str) -> str:
        """
        Extract text from plain text or markdown file
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    text = f.read()
                logger.info(f"Successfully read file with {encoding} encoding")
                return text
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise ValueError(f"Error reading text file: {str(e)}")
        
        raise ValueError(f"Could not decode file with any supported encoding")

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into semantically meaningful overlapping chunks
        Uses sentence boundaries for clean breaks
        """
        text = self._clean_text(text)
        
        if len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            if end < len(text):
                end = self._find_sentence_boundary(text, end)

            chunk = text[start:end].strip()
            
            if len(chunk) >= self.MIN_CHUNK_SIZE:
                chunks.append(chunk)

            if end >= len(text):
                break
                
            start = end - self.chunk_overlap

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text while preserving structure
        """
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        return text

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """
        Find the nearest sentence boundary after position
        Prioritizes natural break points
        """
        boundary_chars = [
            '. ', '.\n', '! ', '!\n', '? ', '?\n',
            '\n\n', '\n'
        ]
        
        nearest = len(text)
        search_window = min(position + 200, len(text))

        for boundary in boundary_chars:
            pos = text.find(boundary, position, search_window)
            if pos != -1:
                boundary_end = pos + len(boundary)
                if boundary_end < nearest:
                    nearest = boundary_end
                break

        return min(nearest, len(text))

