
import sys
import os

try:
    print("Attempting to import chromadb...")
    import chromadb
    print(f"ChromaDB imported: {chromadb.__version__}")
    
    print("Attempting to verify pydantic settings...")
    from chromadb.config import Settings
    
    print("Initializing Client...")
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_test_db",
        anonymized_telemetry=False
    ))
    print("Client initialized successfully")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
