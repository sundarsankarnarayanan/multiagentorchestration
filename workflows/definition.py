"""
Workflow definition models.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """Represents a single step in a workflow."""
    
    name: str = Field(description="Name of this step")
    agent_type: str = Field(description="Type of agent (scout, maker, checker, curator)")
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for this agent"
    )
    input_from: Optional[str] = Field(
        default=None,
        description="Where to get input from (document, scout, maker, checker)"
    )
    condition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Conditional execution criteria"
    )
    
    class Config:
        extra = "allow"


class WorkflowDefinition(BaseModel):
    """
    Definition of a complete workflow.
    
    This can be loaded from YAML/JSON files and executed by the WorkflowEngine.
    """
    
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(
        default=None,
        description="Workflow description"
    )
    version: str = Field(default="1.0", description="Workflow version")
    steps: List[WorkflowStep] = Field(description="List of workflow steps")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        extra = "allow"
    
    def validate_workflow(self) -> List[str]:
        """
        Validate the workflow definition.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.steps:
            errors.append("Workflow must have at least one step")
        
        # Check agent types
        valid_types = ["scout", "maker", "checker", "curator"]
        for i, step in enumerate(self.steps):
            if step.agent_type.lower() not in valid_types:
                errors.append(
                    f"Step {i} has invalid agent type: {step.agent_type}"
                )
        
        # Check input dependencies
        available_outputs = ["document"]
        for i, step in enumerate(self.steps):
            if step.input_from and step.input_from not in available_outputs:
                errors.append(
                    f"Step {i} references unavailable input: {step.input_from}"
                )
            
            # Add this step's output to available outputs
            available_outputs.append(step.agent_type.lower())
        
        return errors
    
    def get_step_by_name(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.dict()
