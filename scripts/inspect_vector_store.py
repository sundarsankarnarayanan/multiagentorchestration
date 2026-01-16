
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.vector_store import get_vector_store

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

def inspect_vector_store():
    print("Initializing Vector Store...")
    vs = get_vector_store()
    
    print("\nListing documents in Vector Store:")
    docs = vs.list_documents()
    
    if not docs:
        print("  No documents found.")
    else:
        for doc in docs:
            print(f"  - Collection: {doc['id']}")
            print(f"    Count: {doc['count']}")
            print(f"    Metadata: {doc['metadata']}")
            
            # Peek at first chunk if available
            try:
                collection = vs.client.get_collection(doc['id'])
                if collection.count() > 0:
                    peek = collection.peek(limit=1)
                    print(f"    First Chunk Preview: {peek['documents'][0][:100]}...")
            except Exception as e:
                print(f"    Could not peek content: {e}")
            print("-" * 40)

if __name__ == "__main__":
    inspect_vector_store()
