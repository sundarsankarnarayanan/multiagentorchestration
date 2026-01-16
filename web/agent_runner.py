"""
Agent runner with WebSocket logging integration.

Wraps agent execution with real-time status updates and logging.
"""

import sys
from pathlib import Path
import asyncio
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.document import Document
from agents.curator import CuratorAgent
from web.websocket_logger import get_ws_handler, AgentStatus


class WebSocketAgentRunner:
    """
    Runs agents with WebSocket logging and status updates.
    """
    
    def __init__(self):
        self.ws_handler = get_ws_handler()
    
    async def process_document(
        self,
        document: Document,
        workflow_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the agent pipeline with real-time updates.

        Args:
            document: Document to process
            workflow_config: Optional workflow configuration

        Returns:
            Processing result dictionary
        """
        try:
            # Reset all agent statuses
            self.ws_handler.reset_status()

            # Default configuration
            if workflow_config is None:
                workflow_config = {
                    "workflow_name": "document_processing",
                    "scout_config": {
                        "preview_length": 1000,
                        "extract_metadata": True,
                    },
                    "maker_config": {
                        "transformation_type": "summarization",
                        "max_output_length": 500,
                    },
                    "checker_config": {
                        "min_quality_score": 0.5,
                    },
                }
            else:
                # Use provided configuration (from UI or API)
                # Log the transformation type being used
                transformation_type = workflow_config.get("maker_config", {}).get("transformation_type", "unknown")
                await self.ws_handler.send_log(
                    f"Using transformation type: {transformation_type}",
                    "INFO"
                )
            
            # Create curator agent
            curator = CuratorAgent(
                name="web_curator",
                config=workflow_config
            )
            
            # Update curator status
            await self.ws_handler.update_agent_status(
                "curator",
                AgentStatus.RUNNING,
                {"message": "Starting workflow orchestration"}
            )
            
            # Execute workflow with status tracking
            result = await self._execute_with_tracking(curator, document)
            
            # Update curator status
            if result.is_successful():
                await self.ws_handler.update_agent_status(
                    "curator",
                    AgentStatus.COMPLETED,
                    {"message": "Workflow completed successfully"}
                )
            else:
                await self.ws_handler.update_agent_status(
                    "curator",
                    AgentStatus.FAILED,
                    {"message": "Workflow failed", "errors": result.errors}
                )
            
            # Format and send result
            result_data = self._format_result(result)
            await self.ws_handler.send_result(result_data)
            
            return result_data
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            await self.ws_handler.send_error(error_msg)
            
            # Mark all as failed
            for agent in ["scout", "maker", "checker", "curator"]:
                await self.ws_handler.update_agent_status(
                    agent,
                    AgentStatus.FAILED,
                    {"message": error_msg}
                )
            
            raise
    
    async def _execute_with_tracking(
        self,
        curator: CuratorAgent,
        document: Document
    ):
        """Execute curator with agent status tracking."""
        
        # Track scout execution
        await self.ws_handler.update_agent_status(
            "scout",
            AgentStatus.RUNNING,
            {"message": f"Analyzing document: {document.get_filename()}"}
        )
        
        # We'll intercept the curator's execution to track each agent
        # For now, just run it and track based on timing
        result = await curator.run(document)
        
        # Update statuses based on result
        if result.is_successful():
            curation_result = result.data
            
            # Scout completed
            await self.ws_handler.update_agent_status(
                "scout",
                AgentStatus.COMPLETED,
                {"message": "Document analysis complete"}
            )
            
            # Maker running
            await self.ws_handler.update_agent_status(
                "maker",
                AgentStatus.RUNNING,
                {"message": "Generating content"}
            )
            
            await asyncio.sleep(0.1)  # Small delay for UI
            
            # Maker completed
            await self.ws_handler.update_agent_status(
                "maker",
                AgentStatus.COMPLETED,
                {"message": "Content generation complete"}
            )
            
            # Checker running
            await self.ws_handler.update_agent_status(
                "checker",
                AgentStatus.RUNNING,
                {"message": "Validating output"}
            )
            
            await asyncio.sleep(0.1)  # Small delay for UI
            
            # Checker completed
            await self.ws_handler.update_agent_status(
                "checker",
                AgentStatus.COMPLETED,
                {"message": "Validation complete"}
            )
        
        return result
    
    def _format_result(self, result) -> Dict[str, Any]:
        """Format agent result for web display."""
        if not result.is_successful():
            return {
                "success": False,
                "errors": result.errors,
            }
        
        curation_result = result.data
        
        return {
            "success": True,
            "workflow_id": curation_result.workflow_id,
            "workflow_name": curation_result.workflow_name,
            "document_id": curation_result.document_id,
            "final_output": curation_result.final_output,
            "metadata": curation_result.metadata,
            "execution_summary": curation_result.execution_summary,
            "processing_time_ms": curation_result.total_processing_time_ms,
        }
