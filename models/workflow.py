"""
Workflow-related data models.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    """States of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowContext(BaseModel):
    """
    Context object passed between agents in a workflow.
    
    This accumulates data as it flows through the pipeline.
    """
    
    workflow_id: str
    document_id: str
    state: WorkflowState = WorkflowState.PENDING
    current_step: int = 0
    total_steps: int = 0
    
    # Data from each agent
    scout_data: Optional[Dict[str, Any]] = None
    maker_data: List[Dict[str, Any]] = Field(default_factory=list)
    checker_data: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Shared context that agents can read/write
    shared_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared data that any agent can access"
    )
    
    # Execution metadata
    started_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def add_scout_data(self, data: Dict[str, Any]) -> None:
        """Add data from scout agent."""
        self.scout_data = data
        self.updated_at = datetime.now()
    
    def add_maker_data(self, data: Dict[str, Any]) -> None:
        """Add data from maker agent."""
        self.maker_data.append(data)
        self.updated_at = datetime.now()
    
    def add_checker_data(self, data: Dict[str, Any]) -> None:
        """Add data from checker agent."""
        self.checker_data.append(data)
        self.updated_at = datetime.now()
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.updated_at = datetime.now()
    
    def advance_step(self) -> None:
        """Advance to the next step."""
        self.current_step += 1
        self.updated_at = datetime.now()
    
    def get_latest_maker_output(self) -> Optional[Dict[str, Any]]:
        """Get the most recent maker output."""
        return self.maker_data[-1] if self.maker_data else None
    
    def get_latest_checker_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent checker report."""
        return self.checker_data[-1] if self.checker_data else None


class WorkflowResult(BaseModel):
    """Final result of a workflow execution."""
    
    workflow_id: str
    workflow_name: str
    state: WorkflowState
    context: WorkflowContext
    final_output: Any
    success: bool
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow result."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "state": self.state.value,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "steps_completed": self.context.current_step,
            "total_steps": self.context.total_steps,
            "errors": self.context.errors,
        }
