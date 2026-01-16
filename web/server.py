"""
FastAPI web server for AI Agent System.

Provides document upload endpoint and WebSocket for real-time logging.
"""

import sys
from pathlib import Path
import asyncio
import logging
from typing import Optional
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.document import Document, DocumentType
from web.websocket_logger import setup_websocket_logging, get_ws_handler
from web.agent_runner import WebSocketAgentRunner
from rag.rag_engine import get_rag_engine


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Agent System",
    description="Document processing with Scout-Maker-Checker-Curator agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up WebSocket logging
ws_handler = setup_websocket_logging()

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Agent runner
agent_runner = WebSocketAgentRunner()

# RAG engine
rag_engine = get_rag_engine()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("""
        <html>
            <head><title>AI Agent System</title></head>
            <body>
                <h1>AI Agent System</h1>
                <p>Frontend files not found. Please create static/index.html</p>
            </body>
        </html>
    """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time logging and status updates.
    
    Clients connect here to receive:
    - Log messages from agents
    - Agent status updates
    - Workflow results
    """
    await websocket.accept()
    ws_handler.add_client(websocket)
    
    logger.info("WebSocket client connected")
    
    # Send initial status
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to AI Agent System",
        "agent_status": ws_handler.get_status_summary()
    })
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        ws_handler.remove_client(websocket)


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workflow_config: Optional[str] = Form(None)
):
    """
    Upload and process a document through the agent pipeline.

    Args:
        file: Uploaded file
        workflow_config: Optional JSON string containing workflow configuration

    Returns:
        Processing result
    """
    logger.info(f"Received file upload: {file.filename}")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / file.filename
    
    try:
        # Save uploaded file
        content = await file.read()
        temp_path.write_bytes(content)
        
        logger.info(f"Saved file to: {temp_path}")
        
        # Create Document object
        document = Document.from_file(temp_path)
        
        # Check if type is supported
        if document.document_type == DocumentType.UNKNOWN:
            # Clean up immediately
            if temp_path.exists():
                temp_path.unlink()

            supported_types = [t.value for t in DocumentType if t != DocumentType.UNKNOWN]
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. Supported types: {', '.join(supported_types)}"
            )

        # Parse workflow configuration if provided
        parsed_config = None
        if workflow_config:
            try:
                import json
                parsed_config = json.loads(workflow_config)
                logger.info(f"Using custom workflow config: {parsed_config.get('workflow_name', 'unnamed')}")
            except Exception as e:
                logger.warning(f"Failed to parse workflow_config: {e}")

        # Process document with agent runner
        result = await agent_runner.process_document(document, workflow_config=parsed_config)
        
        logger.info(f"Processing complete: {result.get('success', False)}")
        
        # Add document to RAG system for Q&A
        try:
            # Use the processed output (OCR text, extracted content, etc.)
            doc_content = None

            # First, try to use the final output from processing
            if result.get('success') and result.get('final_output'):
                final_output = result['final_output']
                if isinstance(final_output, str):
                    doc_content = final_output
                elif isinstance(final_output, dict):
                    # Try to extract text from dict
                    doc_content = final_output.get('text') or final_output.get('content') or str(final_output)

            # Fallback to document.content (original parsed content)
            if not doc_content:
                doc_content = document.content

            # Last resort: try to decode the raw bytes
            if not doc_content:
                try:
                    doc_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    logger.warning(f"Could not decode content for {file.filename}, skipping RAG indexing")
                    result["rag_error"] = "Binary file content could not be decoded"
                    doc_content = None

            if doc_content:
                # Clean up content (remove excessive whitespace)
                doc_content = doc_content.strip()

                if len(doc_content) > 0:
                    num_chunks = await rag_engine.add_document(
                        document_id=document.get_filename(),
                        content=doc_content,
                        metadata={
                            "filename": document.get_filename(),
                            "document_type": document.document_type.value,
                            "workflow": result.get('workflow_name', 'unknown')
                        }
                    )
                    logger.info(f"Added document to RAG system: {num_chunks} chunks for {document.get_filename()}")
                    result["rag_chunks"] = num_chunks
                else:
                    logger.warning(f"Content is empty after processing for {document.get_filename()}")
            else:
                logger.warning(f"No content available for RAG indexing for {document.get_filename()}")

        except Exception as e:
            logger.error(f"Failed to add document to RAG: {e}", exc_info=True)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Agent System",
        "version": "1.0.0"
    }


@app.get("/status")
async def get_status():
    """Get current agent status."""
    return {
        "agents": ws_handler.get_status_summary()
    }



@app.get("/documents")
async def list_documents():
    """List documents available in the RAG system."""
    docs = rag_engine.list_documents()
    return {"documents": docs}


@app.websocket("/chat")

async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for RAG chat.
    
    Clients connect here to:
    - Send questions about uploaded documents
    - Receive streaming answers
    - Get source citations
    """
    await websocket.accept()
    logger.info("Chat WebSocket client connected")
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to RAG chat. Upload a document first, then ask questions!"
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "question":
                question = data.get("question", "")
                document_id = data.get("document_id")  # Optional
                
                logger.info(f"Received question: {question}")
                
                # Stream answer
                async for chunk in rag_engine.query_stream(
                    question=question,
                    document_id=document_id
                ):
                    await websocket.send_json(chunk)
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
    finally:
        logger.info("Chat WebSocket client disconnected")


def main():
    """Run the web server."""
    print("=" * 60)
    print("AI Agent System - Web Server")
    print("=" * 60)
    print()
    print("Starting server...")
    print("  URL: http://localhost:8001")
    print("  WebSocket: ws://localhost:8001/ws")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
