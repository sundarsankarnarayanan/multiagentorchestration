"""
Embedding model for document and query vectorization.

Uses sentence-transformers for generating embeddings.
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Wrapper for sentence-transformers embedding model.
    
    Uses all-MiniLM-L6-v2 by default - fast, good quality, 384 dimensions.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        
        logger.info(f"Initializing embedding model: {model_name}")
    
    def load(self) -> None:
        """Load the model into memory."""
        if self.model is None:
            logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        if self.model is None:
            self.load()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed multiple texts in batches for efficiency.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
        
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load()
        
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self.model is None:
            self.load()
        return self.dimension


# Global embedding model instance
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """Get the global embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
