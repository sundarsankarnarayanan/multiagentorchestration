"""
Base agent class and common utilities for the AI agent system.

This module defines the abstract base class that all agents (Scout, Maker, Checker, Curator)
must inherit from, ensuring a consistent interface across the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging


class AgentStatus(Enum):
    """Status of agent execution."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """Capabilities that agents can declare."""
    DOCUMENT_ANALYSIS = "document_analysis"
    CONTENT_GENERATION = "content_generation"
    VALIDATION = "validation"
    ORCHESTRATION = "orchestration"
    PDF_PARSING = "pdf_parsing"
    TEXT_EXTRACTION = "text_extraction"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"


class AgentOutput:
    """Base class for all agent outputs."""
    
    def __init__(
        self,
        agent_name: str,
        status: AgentStatus,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None
    ):
        self.agent_name = agent_name
        self.status = status
        self.data = data
        self.metadata = metadata or {}
        self.errors = errors or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert output to dictionary format."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }
    
    def is_successful(self) -> bool:
        """Check if agent execution was successful."""
        return self.status == AgentStatus.COMPLETED and len(self.errors) == 0


class Agent(ABC):
    """
    Abstract base class for all agents in the system.
    
    All agents (Scout, Maker, Checker, Curator) must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            name: Unique name for this agent instance
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.logger = self._setup_logger()
        self._execution_history: List[AgentOutput] = []
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for this agent."""
        logger = logging.getLogger(f"agent.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Input data for the agent to process
            context: Optional context from previous agents in the workflow
        
        Returns:
            AgentOutput containing the results of execution
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate that the input data is appropriate for this agent.
        
        Args:
            input_data: Input data to validate
        
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get the list of capabilities this agent provides.
        
        Returns:
            List of AgentCapability enums
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """Get the current status of the agent."""
        return self.status
    
    def get_execution_history(self) -> List[AgentOutput]:
        """Get the history of all executions."""
        return self._execution_history.copy()
    
    def _record_execution(self, output: AgentOutput) -> None:
        """Record an execution in the history."""
        self._execution_history.append(output)
    
    async def run(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """
        Run the agent with input validation and error handling.
        
        This is the main entry point for executing an agent. It handles
        validation, status updates, and error handling.
        
        Args:
            input_data: Input data for the agent
            context: Optional context dictionary
        
        Returns:
            AgentOutput with execution results
        """
        self.logger.info(f"Starting execution with input type: {type(input_data).__name__}")
        self.status = AgentStatus.RUNNING
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                self.status = AgentStatus.FAILED
                output = AgentOutput(
                    agent_name=self.name,
                    status=AgentStatus.FAILED,
                    data=None,
                    errors=["Input validation failed"]
                )
                self._record_execution(output)
                self.logger.error("Input validation failed")
                return output
            
            # Execute the agent
            output = await self.execute(input_data, context)
            self.status = output.status
            self._record_execution(output)
            
            if output.is_successful():
                self.logger.info("Execution completed successfully")
            else:
                self.logger.warning(f"Execution completed with errors: {output.errors}")
            
            return output
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Execution failed with exception: {str(e)}", exc_info=True)
            output = AgentOutput(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                errors=[f"Exception during execution: {str(e)}"]
            )
            self._record_execution(output)
            return output
    
    def reset(self) -> None:
        """Reset the agent to idle state."""
        self.status = AgentStatus.IDLE
        self.logger.info("Agent reset to idle state")
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', status={self.status.value})"
