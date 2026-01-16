"""
WebSocket Logger for real-time agent execution broadcasting.

This module provides a custom logging handler that broadcasts log messages
and agent status updates to connected WebSocket clients.
"""

import logging
import json
from typing import Set, Dict, Any
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that broadcasts to WebSocket clients.
    
    Captures log messages and agent status changes, formatting them
    for real-time display in the web UI.
    """
    
    def __init__(self):
        super().__init__()
        self.clients: Set[Any] = set()
        self.agent_status: Dict[str, AgentStatus] = {
            "scout": AgentStatus.IDLE,
            "maker": AgentStatus.IDLE,
            "checker": AgentStatus.IDLE,
            "curator": AgentStatus.IDLE,
        }
    
    def add_client(self, websocket) -> None:
        """Add a WebSocket client."""
        self.clients.add(websocket)
    
    def remove_client(self, websocket) -> None:
        """Remove a WebSocket client."""
        self.clients.discard(websocket)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        
        # Send to all clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send_text(message_json)
            except Exception:
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to WebSocket clients.
        
        This is called automatically by the logging system.
        """
        try:
            # Format the log message
            message = {
                "type": "log",
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            
            # Detect agent from logger name
            agent_name = self._extract_agent_name(record.name)
            if agent_name:
                message["agent"] = agent_name
            
            # Schedule broadcast (will be handled by event loop)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.broadcast(message))
            except RuntimeError:
                # No event loop running, skip broadcast
                pass
                
        except Exception as e:
            self.handleError(record)
    
    def _extract_agent_name(self, logger_name: str) -> str:
        """Extract agent name from logger name."""
        logger_lower = logger_name.lower()
        
        if "scout" in logger_lower:
            return "scout"
        elif "maker" in logger_lower:
            return "maker"
        elif "checker" in logger_lower:
            return "checker"
        elif "curator" in logger_lower:
            return "curator"
        
        return None
    
    async def update_agent_status(
        self,
        agent_name: str,
        status: AgentStatus,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Update and broadcast agent status.
        
        Args:
            agent_name: Name of the agent (scout, maker, checker, curator)
            status: New status
            metadata: Optional metadata about the status change
        """
        self.agent_status[agent_name] = status
        
        message = {
            "type": "agent_status",
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": status.value,
            "metadata": metadata or {}
        }
        
        await self.broadcast(message)
    
    async def send_result(self, result: Dict[str, Any]) -> None:
        """
        Send workflow result to clients.
        
        Args:
            result: Workflow result data
        """
        message = {
            "type": "result",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
        await self.broadcast(message)
    
    async def send_error(self, error: str) -> None:
        """
        Send error message to clients.
        
        Args:
            error: Error message
        """
        message = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "message": error
        }
        
        await self.broadcast(message)
    
    def get_status_summary(self) -> Dict[str, str]:
        """Get current status of all agents."""
        return {
            agent: status.value
            for agent, status in self.agent_status.items()
        }
    
    def reset_status(self) -> None:
        """Reset all agent statuses to idle."""
        for agent in self.agent_status:
            self.agent_status[agent] = AgentStatus.IDLE


# Global WebSocket log handler instance
_ws_handler: WebSocketLogHandler = None


def get_ws_handler() -> WebSocketLogHandler:
    """Get the global WebSocket log handler."""
    global _ws_handler
    if _ws_handler is None:
        _ws_handler = WebSocketLogHandler()
        _ws_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        _ws_handler.setFormatter(formatter)
    return _ws_handler


def setup_websocket_logging() -> WebSocketLogHandler:
    """
    Set up WebSocket logging for all agents.
    
    Returns:
        WebSocketLogHandler instance
    """
    handler = get_ws_handler()
    
    # Add handler to agent loggers
    agent_loggers = [
        "agent.scout",
        "agent.maker",
        "agent.checker",
        "agent.curator",
    ]
    
    for logger_name in agent_loggers:
        logger = logging.getLogger(logger_name)
        if handler not in logger.handlers:
            logger.addHandler(handler)
    
    return handler
