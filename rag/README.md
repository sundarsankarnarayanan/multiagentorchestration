# RAG System Documentation

The Retrieval-Augmented Generation (RAG) system enables chatting with your documents using local LLMs.

## Components

1.  **Vector Database**: ChromaDB (stores document embeddings)
2.  **Embeddings**: `all-MiniLM-L6-v2` (sentence-transformers)
3.  **LLM**: Ollama (runs Llama 2, Mistral, etc.)
4.  **Interface**: WebSocket-based chat

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install & Setup Ollama**:
    ```bash
    ./scripts/setup_ollama.sh
    ```
    This script will:
    - Install Ollama if missing
    - Start the Ollama service
    - Download the `llama2` model

## Usage

1.  Start the web server:
    ```bash
    python web/server.py
    ```

2.  Open http://localhost:8001

3.  Upload a document using the drag-and-drop info.

4.  Click the chat bubble 💬 in the bottom right to open the chat panel.

5.  Ask questions about your document!

## Configuration

You can configure the RAG system in `rag/config.py` (or modify `web/server.py` initialization):

- **Model**: Change `llama2` to `mistral` or `codellama` (make sure to `ollama pull modelname` first).
- **Chunk Size**: Adjust chunk size in `rag/vector_store.py` (default 500 chars).
- **Persistence**: ChromaDB data is stored in `data/chromadb`. Deleting this folder resets the database.

## Troubleshooting

**Ollama connection failed**:
- Ensure Ollama is running: `ollama serve`
- Check port 11434 is accessible.

**ChromaDB errors**:
- If you see Pydantic errors, use the provided patched configuration or compatible versions.
- Running `pip install --upgrade chromadb` might help if looking for newer features, but be careful of Pydantic v2 conflicts.
