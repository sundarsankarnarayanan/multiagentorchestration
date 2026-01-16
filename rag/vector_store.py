"""
Vector store manager using ChromaDB for document storage and retrieval.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from rag.embeddings import get_embedding_model

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages document storage and retrieval using ChromaDB.

    Features:
    - Document chunking
    - Embedding generation
    - Similarity search
    - Metadata storage
    """

    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize vector store manager.

        Args:
            persist_directory: Directory to persist ChromaDB data
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize ChromaDB client with new API
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

        # Initialize embedding model
        self.embedding_model = get_embedding_model()

        logger.info(f"Vector store initialized at {self.persist_directory}")

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending
                last_period = chunk.rfind(". ")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = chunk[: break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]  # Remove empty chunks

    def _get_collection_name(self, document_id: str) -> str:
        """
        Get collection name for a document.

        Args:
            document_id: Document identifier

        Returns:
            Collection name
        """
        # ChromaDB collection names must be 3-63 characters, alphanumeric + _ - .
        # Hash the document_id to ensure valid name
        hash_suffix = hashlib.md5(document_id.encode()).hexdigest()[:8]
        return f"doc_{hash_suffix}"

    def add_document(
        self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a document to the vector store.

        Args:
            document_id: Unique document identifier
            content: Document content
            metadata: Optional metadata

        Returns:
            Number of chunks created
        """
        logger.info(f"Adding document {document_id} to vector store")

        # Chunk the document
        chunks = self._chunk_text(content)
        logger.info(f"Created {len(chunks)} chunks")

        if not chunks:
            logger.warning("No chunks created from document")
            return 0

        # Generate embeddings
        import numpy as np

        embeddings_list = self.embedding_model.embed_batch(chunks)
        # Convert to numpy array for ChromaDB compatibility
        embeddings = np.array(embeddings_list)

        # Get or create collection
        collection_name = self._get_collection_name(document_id)
        try:
            collection = self.client.get_collection(collection_name)
            # Delete existing collection to replace
            self.client.delete_collection(collection_name)
        except:
            pass

        collection = self.client.create_collection(
            name=collection_name, metadata={"document_id": document_id}
        )

        # Prepare metadata for each chunk
        chunk_metadata = []
        for i in range(len(chunks)):
            chunk_meta = {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
            }
            if metadata:
                chunk_meta.update(metadata)
            chunk_metadata.append(chunk_meta)

        # Add to collection
        collection.add(
            embeddings=embeddings_list,  # Use original list format
            documents=chunks,
            metadatas=chunk_metadata,
            ids=[f"{document_id}_chunk_{i}" for i in range(len(chunks))],
        )

        logger.info(f"Added {len(chunks)} chunks to collection {collection_name}")
        return len(chunks)

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its chunks from the vector store.

        Args:
            document_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        collection_name = self._get_collection_name(document_id)
        try:
            self.client.delete_collection(collection_name)
            logger.info(
                f"Deleted document {document_id} (collection {collection_name})"
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to delete document {document_id}: {e}")
            return False

    def search(
        self, query: str, document_id: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.

        Args:
            query: Search query
            document_id: Optional document ID to search within
            top_k: Number of results to return

        Returns:
            List of results with content, metadata, and distance
        """
        # Embed the query
        query_embedding = self.embedding_model.embed_text(query)

        results = []

        if document_id:
            # Search in specific document
            collection_name = self._get_collection_name(document_id)
            try:
                collection = self.client.get_collection(collection_name)
                count = collection.count()
                if count == 0:
                    return results

                search_results = collection.query(
                    query_embeddings=[query_embedding], n_results=min(top_k, count)
                )
                results.extend(self._format_results(search_results))
            except Exception as e:
                logger.warning(f"Collection {collection_name} not found: {e}")
        else:
            # Search across all collections
            collections = self.client.list_collections()
            for collection in collections:
                try:
                    count = collection.count()
                    if count == 0:
                        continue

                    search_results = collection.query(
                        query_embeddings=[query_embedding], n_results=min(top_k, count)
                    )
                    results.extend(self._format_results(search_results))
                except Exception as e:
                    logger.warning(f"Error searching collection {collection.name}: {e}")

            # Sort by distance and take top_k
            results.sort(key=lambda x: x["distance"])
            results = results[:top_k]

        logger.info(f"Found {len(results)} results for query")
        return results

    def _format_results(self, search_results) -> List[Dict[str, Any]]:
        """Format ChromaDB search results."""
        formatted = []

        # Handle ChromaDB QueryResult object
        if hasattr(search_results, "ids"):
            ids = search_results.ids[0] if search_results.ids else []
            documents = search_results.documents[0] if search_results.documents else []
            metadatas = search_results.metadatas[0] if search_results.metadatas else []
            distances = search_results.distances[0] if search_results.distances else []
        else:
            # Fallback for dict format
            if not search_results.get("ids") or not search_results["ids"][0]:
                return formatted
            ids = search_results["ids"][0]
            documents = (
                search_results["documents"][0]
                if search_results.get("documents")
                else []
            )
            metadatas = (
                search_results["metadatas"][0]
                if search_results.get("metadatas")
                else []
            )
            distances = (
                search_results["distances"][0]
                if search_results.get("distances")
                else []
            )

        for i in range(len(ids)):
            formatted.append(
                {
                    "id": ids[i] if i < len(ids) else None,
                    "content": documents[i] if i < len(documents) else None,
                    "metadata": metadatas[i] if i < len(metadatas) else None,
                    "distance": distances[i] if i < len(distances) else None,
                }
            )

        return formatted

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents (collections) in the vector store.

        Returns:
            List of dicts with document metadata
        """
        try:
            collections = self.client.list_collections()
            results = []

            for col in collections:
                # Get basic info
                count = col.count()

                # Try to get metadata from first item
                metadata = {}
                try:
                    peek = col.peek(limit=1)
                    if peek and peek["metadatas"] and len(peek["metadatas"]) > 0:
                        # Common metadata fields we expect
                        m = peek["metadatas"][0]
                        metadata = {
                            "filename": m.get("filename", col.name),
                            "document_type": m.get("document_type", "unknown"),
                        }
                except:
                    pass

                results.append({"id": col.name, "count": count, "metadata": metadata})

            return results
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

    def deduplicate_content(self, content: str) -> bool:
        """
        Deduplicate content (placeholder).
        """
        # TODO: Implement content deduplication logic
        return True


# Global vector store instance
_vector_store: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store
