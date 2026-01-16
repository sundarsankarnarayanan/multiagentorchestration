"""
Prompt templates for RAG system.
"""

from typing import List, Dict, Any


class RAGPrompts:
    """Prompt templates for different RAG tasks."""
    
    SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided document context.

Instructions:
- Answer questions using ONLY the information from the provided context
- If the answer is not in the context, say "I don't have information about that in the document"
- Be concise and accurate
- Cite specific parts of the context when relevant
- If the context contains conflicting information, mention both perspectives"""
    
    QA_TEMPLATE = """Context from the document:
{context}

Question: {question}

Answer based on the context above:"""
    
    QA_WITH_HISTORY_TEMPLATE = """Context from the document:
{context}

Previous conversation:
{history}

Current question: {question}

Answer based on the context and conversation history:"""
    
    NO_CONTEXT_RESPONSE = "I don't have information about that in the document. Please ask a question related to the uploaded document."
    
    @staticmethod
    def format_qa_prompt(question: str, context: List[str]) -> str:
        """
        Format a Q&A prompt with context.
        
        Args:
            question: User's question
            context: List of relevant text chunks
        
        Returns:
            Formatted prompt
        """
        context_text = "\n\n".join([
            f"[Source {i+1}]: {chunk}"
            for i, chunk in enumerate(context)
        ])
        
        return RAGPrompts.QA_TEMPLATE.format(
            context=context_text,
            question=question
        )
    
    @staticmethod
    def format_qa_with_history(
        question: str,
        context: List[str],
        history: List[Dict[str, str]]
    ) -> str:
        """
        Format a Q&A prompt with context and conversation history.
        
        Args:
            question: User's question
            context: List of relevant text chunks
            history: Previous conversation messages
        
        Returns:
            Formatted prompt
        """
        context_text = "\n\n".join([
            f"[Source {i+1}]: {chunk}"
            for i, chunk in enumerate(context)
        ])
        
        history_text = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in history[-5:]  # Last 5 messages
        ])
        
        return RAGPrompts.QA_WITH_HISTORY_TEMPLATE.format(
            context=context_text,
            history=history_text,
            question=question
        )
    
    @staticmethod
    def extract_sources(context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract source information from context chunks.
        
        Args:
            context_chunks: List of chunks with metadata
        
        Returns:
            List of source citations
        """
        sources = []
        for i, chunk in enumerate(context_chunks):
            sources.append({
                "index": i + 1,
                "content": chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'],
                "metadata": chunk.get('metadata', {}),
                "relevance": 1.0 - chunk.get('distance', 0.0)  # Convert distance to relevance
            })
        return sources
