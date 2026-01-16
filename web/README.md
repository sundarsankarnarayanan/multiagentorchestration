# Web Frontend for AI Agent System

## Overview

A beautiful web interface for the AI Agent System with real-time agent execution visualization and live logging.

## Features

- 📤 **Drag-and-drop file upload**
- 🎯 **Real-time agent visualization** (Scout → Maker → Checker → Curator)
- 📊 **Live logging** showing what each agent is doing
- ✨ **Modern glassmorphic UI** with smooth animations
- 🔌 **WebSocket** for instant bidirectional communication
- 📱 **Responsive design** works on all devices

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/sundar/Projects/AIproject
source venv/bin/activate
pip install fastapi uvicorn python-multipart websockets
```

### 2. Start the Server

```bash
python web/server.py
```

The server will start on `http://localhost:8000`

### 3. Open in Browser

Navigate to `http://localhost:8000` in your web browser.

## Usage

1. **Upload Document**: Drag and drop a file or click to browse
2. **Process**: Click the "Process Document" button
3. **Watch**: See agents light up in real-time as they process
4. **View Logs**: Live logs appear showing exactly what's happening
5. **See Results**: Final results display at the bottom

## Architecture

### Backend (`web/server.py`)
- FastAPI application
- `/upload` - Document upload endpoint
- `/ws` - WebSocket for real-time updates
- `/health` - Health check
- `/status` - Current agent status

### WebSocket Logger (`web/websocket_logger.py`)
- Custom logging handler
- Broadcasts log messages to all connected clients
- Tracks agent status (idle, running, completed, failed)
- Sends structured events to frontend

### Agent Runner (`web/agent_runner.py`)
- Wraps agent execution with WebSocket integration
- Emits status updates for each agent
- Formats results for web display

### Frontend
- `static/index.html` - Main UI structure
- `static/styles.css` - Glassmorphic styling with animations
- `static/app.js` - WebSocket client and UI logic

## WebSocket Events

### From Server to Client

**Connected**
```json
{
  "type": "connected",
  "message": "Connected to AI Agent System",
  "agent_status": {
    "scout": "idle",
    "maker": "idle",
    "checker": "idle",
    "curator": "idle"
  }
}
```

**Log Message**
```json
{
  "type": "log",
  "timestamp": "2026-01-07T11:30:00",
  "level": "INFO",
  "logger": "scout",
  "message": "Analyzing document...",
  "agent": "scout"
}
```

**Agent Status Update**
```json
{
  "type": "agent_status",
  "timestamp": "2026-01-07T11:30:00",
  "agent": "scout",
  "status": "running",
  "metadata": {
    "message": "Analyzing document: sample.txt"
  }
}
```

**Result**
```json
{
  "type": "result",
  "timestamp": "2026-01-07T11:30:01",
  "data": {
    "success": true,
    "workflow_id": "...",
    "final_output": "...",
    "metadata": {...}
  }
}
```

**Error**
```json
{
  "type": "error",
  "timestamp": "2026-01-07T11:30:00",
  "message": "Error message"
}
```

## Customization

### Change Workflow Configuration

Edit `web/agent_runner.py`:

```python
workflow_config = {
    "workflow_name": "custom_workflow",
    "maker_config": {
        "transformation_type": "classification",  # or "extraction"
        "max_output_length": 1000,
    },
    "checker_config": {
        "min_quality_score": 0.7,
    },
}
```

### Modify UI Colors

Edit CSS variables in `static/styles.css`:

```css
:root {
    --primary: #6366f1;
    --success: #10b981;
    --error: #ef4444;
    /* ... */
}
```

## Troubleshooting

**Server won't start**
- Make sure virtual environment is activated
- Install dependencies: `pip install fastapi uvicorn python-multipart websockets`

**WebSocket won't connect**
- Check browser console for errors
- Ensure server is running on port 8000
- Check firewall settings

**Agents not updating**
- Check browser console for WebSocket messages
- Verify server logs for errors
- Refresh the page

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn web.server:app --reload --host 0.0.0.0 --port 8000
```

### Testing WebSocket

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Production Deployment

For production, use a proper ASGI server:

```bash
pip install gunicorn
gunicorn web.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Screenshots

The UI features:
- Dark theme with glassmorphic cards
- Animated agent cards that light up during execution
- Color-coded log levels (info, success, warning, error)
- Smooth transitions and progress indicators
- Responsive layout for mobile and desktop
