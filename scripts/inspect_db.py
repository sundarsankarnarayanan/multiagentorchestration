
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.vector_store import get_vector_store

def inspect_db():
    print("🔍 Inspecting Vector Database...")
    print("================================")
    
    try:
        vs = get_vector_store()
        client = vs.client
        
        # List all collections
        collections = client.list_collections()
        
        if not collections:
            print("❌ No documents found in the vector database.")
            return
            
        print(f"✅ Found {len(collections)} documents/collections:")
        print("-" * 50)
        
        for i, col in enumerate(collections):
            print(f"{i+1}. Collection Name: {col.name}")
            print(f"   Count: {col.count()} chunks")
            
            # peek at metadata if possible
            try:
                peek = col.peek(limit=1)
                if peek and peek['metadatas'] and len(peek['metadatas']) > 0:
                    meta = peek['metadatas'][0]
                    print(f"   Metadata: {meta}")
            except Exception as e:
                print(f"   (Could not peek metadata: {e})")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_db()
