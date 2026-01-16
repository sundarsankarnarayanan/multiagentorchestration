"""
RAG Engine - Orchestrates retrieval and generation pipeline.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.vector_store import get_vector_store
from rag.llm_client import get_ollama_client
from rag.prompts import RAGPrompts

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Engine.
    
    Orchestrates the complete RAG pipeline:
    1. Retrieve relevant context from vector store
    2. Format prompt with context
    3. Generate answer using LLM
    4. Return answer with sources
    """
    
    def __init__(
        self,
        model: str = "llama2",
        top_k: int = 5,
        temperature: float = 0.7
    ):
        """
        Initialize RAG engine.
        
        Args:
            model: LLM model name
            top_k: Number of context chunks to retrieve
            temperature: LLM sampling temperature
        """
        self.vector_store = get_vector_store()
        self.llm_client = get_ollama_client(model=model)
        self.top_k = top_k
        self.temperature = temperature
        
        logger.info(f"RAG Engine initialized with model: {model}")
    
    async def check_llm_available(self) -> bool:
        """
        Check if LLM is available.
        
        Returns:
            True if LLM is accessible
        """
        return await self.llm_client.check_connection()
    
    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add a document to the RAG system.
        
        Args:
            document_id: Unique document identifier
            content: Document content
            metadata: Optional metadata
        
        Returns:
            Number of chunks created
        """
        logger.info(f"Adding document {document_id} to RAG system")
        return self.vector_store.add_document(document_id, content, metadata)
    
    async def query(
        self,
        question: str,
        document_id: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system (non-streaming).
        
        Args:
            question: User's question
            document_id: Optional document ID to search within
            conversation_history: Optional conversation history
        
        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve relevant context
        context_chunks = self.vector_store.search(
            query=question,
            document_id=document_id,
            top_k=self.top_k
        )
        
        if not context_chunks:
            return {
                "answer": RAGPrompts.NO_CONTEXT_RESPONSE,
                "sources": [],
                "has_context": False
            }
        
        # Format prompt
        context_texts = [chunk['content'] for chunk in context_chunks]
        
        if conversation_history:
            prompt = RAGPrompts.format_qa_with_history(
                question=question,
                context=context_texts,
                history=conversation_history
            )
        else:
            prompt = RAGPrompts.format_qa_prompt(
                question=question,
                context=context_texts
            )
        
        # Generate answer
        answer = await self.llm_client.generate(
            prompt=prompt,
            system_prompt=RAGPrompts.SYSTEM_PROMPT,
            temperature=self.temperature
        )
        
        # Extract sources
        sources = RAGPrompts.extract_sources(context_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "has_context": True,
            "num_sources": len(sources)
        }
    
    async def query_stream(
        self,
        question: str,
        document_id: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Query the RAG system with streaming response.
        
        Args:
            question: User's question
            document_id: Optional document ID to search within
            conversation_history: Optional conversation history
        
        Yields:
            Dicts with answer chunks, sources, and metadata
        """
        # Retrieve relevant context
        context_chunks = self.vector_store.search(
            query=question,
            document_id=document_id,
            top_k=self.top_k
        )
        
        if not context_chunks:
            yield {
                "type": "answer",
                "content": RAGPrompts.NO_CONTEXT_RESPONSE,
                "done": True
            }
            return
        
        # Send sources first
        sources = RAGPrompts.extract_sources(context_chunks)
        yield {
            "type": "sources",
            "sources": sources,
            "num_sources": len(sources)
        }
        
        # Format prompt
        context_texts = [chunk['content'] for chunk in context_chunks]
        
        if conversation_history:
            prompt = RAGPrompts.format_qa_with_history(
                question=question,
                context=context_texts,
                history=conversation_history
            )
        else:
            prompt = RAGPrompts.format_qa_prompt(
                question=question,
                context=context_texts
            )
        
        # Stream answer
        async for chunk in self.llm_client.generate_stream(
            prompt=prompt,
            system_prompt=RAGPrompts.SYSTEM_PROMPT,
            temperature=self.temperature
        ):
            yield {
                "type": "answer",
                "content": chunk,
                "done": False
            }
        
        # Send completion signal
        yield {
            "type": "answer",
            "content": "",
            "done": True
        }
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the RAG system.
        
        Args:
            document_id: Document identifier
        
        Returns:
            True if deleted
        """
        return self.vector_store.delete_document(document_id)
    
    def list_documents(self) -> List[str]:
        """
        List all documents in the RAG system.
        
        Returns:
            List of document IDs
        """
        return self.vector_store.list_documents()


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine(model: str = "llama2") -> RAGEngine:
    """Get the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None or _rag_engine.llm_client.model != model:
        _rag_engine = RAGEngine(model=model)
    return _rag_engine
