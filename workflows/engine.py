"""
Workflow engine for executing agent pipelines.
"""

from typing import Any, Dict, List, Optional
import asyncio
import time
from datetime import datetime
from pathlib import Path
import yaml
import json

from agents import ScoutAgent, MakerAgent, CheckerAgent, CuratorAgent
from models.document import Document
from models.workflow import WorkflowContext, WorkflowState, WorkflowResult
from .definition import WorkflowDefinition, WorkflowStep


class WorkflowEngine:
    """
    Engine for executing workflow definitions.
    
    Supports loading workflows from YAML/JSON and executing them
    with proper state management and error handling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.active_workflows: Dict[str, WorkflowContext] = {}
    
    async def execute_workflow(
        self,
        workflow_def: WorkflowDefinition,
        document: Document
    ) -> WorkflowResult:
        """
        Execute a workflow definition.
        
        Args:
            workflow_def: Workflow definition to execute
            document: Document to process
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        workflow_id = f"{workflow_def.name}_{int(time.time())}"
        
        # Create workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            document_id=document.id,
            state=WorkflowState.RUNNING,
            total_steps=len(workflow_def.steps),
            started_at=datetime.now()
        )
        
        self.active_workflows[workflow_id] = context
        
        try:
            # Execute each step in sequence
            for step in workflow_def.steps:
                result = await self._execute_step(step, document, context)
                
                if not result:
                    context.state = WorkflowState.FAILED
                    context.add_error(f"Step '{step.name}' failed")
                    break
                
                context.advance_step()
            
            # Mark as completed if all steps succeeded
            if context.state == WorkflowState.RUNNING:
                context.state = WorkflowState.COMPLETED
            
            # Create workflow result
            duration = (time.time() - start_time) * 1000
            
            workflow_result = WorkflowResult(
                workflow_id=workflow_id,
                workflow_name=workflow_def.name,
                state=context.state,
                context=context,
                final_output=self._extract_final_output(context),
                success=context.state == WorkflowState.COMPLETED,
                started_at=context.started_at,
                completed_at=datetime.now(),
                duration_ms=duration
            )
            
            return workflow_result
            
        except Exception as e:
            context.state = WorkflowState.FAILED
            context.add_error(f"Workflow execution failed: {str(e)}")
            
            duration = (time.time() - start_time) * 1000
            
            return WorkflowResult(
                workflow_id=workflow_id,
                workflow_name=workflow_def.name,
                state=WorkflowState.FAILED,
                context=context,
                final_output=None,
                success=False,
                started_at=context.started_at,
                completed_at=datetime.now(),
                duration_ms=duration
            )
        
        finally:
            # Clean up
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        document: Document,
        context: WorkflowContext
    ) -> bool:
        """
        Execute a single workflow step.
        
        Args:
            step: Step definition
            document: Document being processed
            context: Workflow context
        
        Returns:
            True if step succeeded, False otherwise
        """
        # Create agent based on step type
        agent = self._create_agent(step)
        
        if agent is None:
            context.add_error(f"Unknown agent type: {step.agent_type}")
            return False
        
        # Get input for this step
        input_data = self._get_step_input(step, document, context)
        
        # Execute agent
        result = await agent.run(input_data, context.shared_context)
        
        # Store result in context
        if result.is_successful():
            self._store_step_result(step, result, context)
            return True
        else:
            context.add_error(f"Agent '{step.agent_type}' failed: {result.errors}")
            return False
    
    def _create_agent(self, step: WorkflowStep):
        """Create an agent instance based on step definition."""
        agent_type = step.agent_type.lower()
        config = step.config or {}
        
        if agent_type == "scout":
            return ScoutAgent(name=step.name, config=config)
        elif agent_type == "maker":
            return MakerAgent(name=step.name, config=config)
        elif agent_type == "checker":
            return CheckerAgent(name=step.name, config=config)
        elif agent_type == "curator":
            return CuratorAgent(name=step.name, config=config)
        
        return None
    
    def _get_step_input(
        self,
        step: WorkflowStep,
        document: Document,
        context: WorkflowContext
    ) -> Any:
        """Get input data for a step."""
        # If input_from is specified, get from context
        if step.input_from:
            if step.input_from == "document":
                return document
            elif step.input_from == "scout":
                return context.scout_data
            elif step.input_from == "maker":
                return context.get_latest_maker_output()
            elif step.input_from == "checker":
                return context.get_latest_checker_report()
        
        # Default: use document for scout, previous output for others
        if step.agent_type.lower() == "scout":
            return document
        elif step.agent_type.lower() == "maker":
            return context.scout_data
        elif step.agent_type.lower() == "checker":
            return context.get_latest_maker_output()
        
        return document
    
    def _store_step_result(
        self,
        step: WorkflowStep,
        result: Any,
        context: WorkflowContext
    ) -> None:
        """Store step result in context."""
        agent_type = step.agent_type.lower()
        
        result_dict = result.data.dict() if hasattr(result.data, 'dict') else result.to_dict()
        
        if agent_type == "scout":
            context.add_scout_data(result_dict)
        elif agent_type == "maker":
            context.add_maker_data(result_dict)
        elif agent_type == "checker":
            context.add_checker_data(result_dict)
    
    def _extract_final_output(self, context: WorkflowContext) -> Any:
        """Extract final output from context."""
        # Return the last maker output if available
        latest_maker = context.get_latest_maker_output()
        if latest_maker:
            return latest_maker.get("generated_content")
        
        # Otherwise return scout data
        return context.scout_data
    
    @classmethod
    def load_workflow_from_file(cls, file_path: str | Path) -> WorkflowDefinition:
        """
        Load workflow definition from a YAML or JSON file.
        
        Args:
            file_path: Path to workflow file
        
        Returns:
            WorkflowDefinition instance
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        content = path.read_text()
        
        # Parse based on extension
        if path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(content)
        elif path.suffix == '.json':
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported workflow file format: {path.suffix}")
        
        return WorkflowDefinition(**data)
    
    async def execute_workflow_from_file(
        self,
        file_path: str | Path,
        document: Document
    ) -> WorkflowResult:
        """
        Load and execute a workflow from a file.
        
        Args:
            file_path: Path to workflow definition file
            document: Document to process
        
        Returns:
            WorkflowResult
        """
        workflow_def = self.load_workflow_from_file(file_path)
        return await self.execute_workflow(workflow_def, document)
    
    def get_active_workflows(self) -> Dict[str, WorkflowContext]:
        """Get all currently active workflows."""
        return self.active_workflows.copy()
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel an active workflow.
        
        Args:
            workflow_id: ID of workflow to cancel
        
        Returns:
            True if cancelled, False if not found
        """
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            context.state = WorkflowState.CANCELLED
            del self.active_workflows[workflow_id]
            return True
        
        return False
