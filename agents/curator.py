"""
Curator Agent - Workflow orchestration and result curation.

The Curator agent is responsible for:
- Orchestrating the entire workflow
- Coordinating Scout, Maker, and Checker agents
- Managing workflow state and context
- Aggregating results and producing final output
"""

from typing import Any, Dict, List, Optional
import asyncio
import time
from datetime import datetime

from .base import Agent, AgentOutput, AgentStatus, AgentCapability
from .scout import ScoutAgent
from .maker import MakerAgent
from .checker import CheckerAgent
from models.document import Document, DocumentProfile
from models.workflow import WorkflowContext, WorkflowState, WorkflowResult
from models.agent_output import CurationResult, MakerOutput, ValidationReport


class CuratorAgent(Agent):
    """
    Curator agent for workflow orchestration.
    
    This agent coordinates the execution of Scout, Maker, and Checker agents
    in a pipeline, manages state, and produces the final curated result.
    """
    
    def __init__(self, name: str = "curator", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Curator agent.
        
        Args:
            name: Name of this agent instance
            config: Configuration options:
                - workflow_name: Name of the workflow to execute
                - scout_config: Configuration for Scout agent
                - maker_config: Configuration for Maker agent
                - checker_config: Configuration for Checker agent
                - retry_on_failure: Whether to retry failed steps (default: False)
                - max_retries: Maximum number of retries (default: 3)
        """
        super().__init__(name, config)
        self.workflow_name = self.config.get("workflow_name", "default_workflow")
        self.retry_on_failure = self.config.get("retry_on_failure", False)
        self.max_retries = self.config.get("max_retries", 3)
        
        # Initialize sub-agents
        self.scout = ScoutAgent(
            name=f"{name}_scout",
            config=self.config.get("scout_config", {})
        )
        self.maker = MakerAgent(
            name=f"{name}_maker",
            config=self.config.get("maker_config", {})
        )
        self.checker = CheckerAgent(
            name=f"{name}_checker",
            config=self.config.get("checker_config", {})
        )
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that input is a Document."""
        if not isinstance(input_data, Document):
            self.logger.error(f"Invalid input type: {type(input_data)}. Expected Document.")
            return False
        return True
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Curator agent capabilities."""
        return [AgentCapability.ORCHESTRATION]
    
    async def execute(
        self,
        input_data: Document,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute the complete workflow.
        
        Args:
            input_data: Document to process
            context: Optional initial context
        
        Returns:
            AgentOutput containing CurationResult
        """
        start_time = time.time()
        workflow_id = f"{self.workflow_name}_{int(time.time())}"
        
        self.logger.info(
            f"Starting workflow '{self.workflow_name}' (ID: {workflow_id}) "
            f"for document: {input_data.get_filename()}"
        )
        
        # Initialize workflow context
        workflow_context = WorkflowContext(
            workflow_id=workflow_id,
            document_id=input_data.id,
            state=WorkflowState.RUNNING,
            total_steps=3,  # Scout -> Maker -> Checker
            started_at=datetime.now()
        )
        
        try:
            # Step 1: Scout - Analyze document
            scout_result = await self._execute_scout(input_data, workflow_context)
            if not scout_result.is_successful():
                return self._create_failure_output(
                    workflow_id,
                    input_data.id,
                    "Scout agent failed",
                    scout_result.errors,
                    start_time
                )
            
            # Step 2: Maker - Transform content
            maker_result = await self._execute_maker(
                scout_result.data,
                workflow_context
            )
            if not maker_result.is_successful():
                return self._create_failure_output(
                    workflow_id,
                    input_data.id,
                    "Maker agent failed",
                    maker_result.errors,
                    start_time
                )
            
            # Step 3: Checker - Validate output
            checker_result = await self._execute_checker(
                maker_result.data,
                workflow_context
            )
            if not checker_result.is_successful():
                return self._create_failure_output(
                    workflow_id,
                    input_data.id,
                    "Checker agent failed",
                    checker_result.errors,
                    start_time
                )
            
            # Create final curated result
            curation_result = await self._create_curation_result(
                workflow_id,
                input_data.id,
                scout_result.data,
                maker_result.data,
                checker_result.data,
                start_time
            )
            
            workflow_context.state = WorkflowState.COMPLETED
            
            self.logger.info(
                f"Workflow completed successfully in "
                f"{curation_result.total_processing_time_ms:.2f}ms"
            )
            
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=curation_result,
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_name": self.workflow_name,
                    "success": curation_result.success,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Workflow failed with exception: {str(e)}")
            workflow_context.state = WorkflowState.FAILED
            workflow_context.add_error(str(e))
            
            return self._create_failure_output(
                workflow_id,
                input_data.id,
                "Workflow execution failed",
                [str(e)],
                start_time
            )
    
    async def _execute_scout(
        self,
        document: Document,
        context: WorkflowContext
    ) -> AgentOutput:
        """Execute the Scout agent."""
        self.logger.info("Executing Scout agent")
        context.advance_step()
        
        result = await self.scout.run(document)
        
        if result.is_successful():
            context.add_scout_data(result.data.dict() if hasattr(result.data, 'dict') else result.to_dict())
        else:
            context.add_error(f"Scout failed: {result.errors}")
        
        return result
    
    async def _execute_maker(
        self,
        scout_profile: DocumentProfile,
        context: WorkflowContext
    ) -> AgentOutput:
        """Execute the Maker agent."""
        self.logger.info("Executing Maker agent")
        context.advance_step()
        
        result = await self.maker.run(scout_profile)
        
        if result.is_successful():
            context.add_maker_data(result.data.dict() if hasattr(result.data, 'dict') else result.to_dict())
        else:
            context.add_error(f"Maker failed: {result.errors}")
        
        return result
    
    async def _execute_checker(
        self,
        maker_output: MakerOutput,
        context: WorkflowContext
    ) -> AgentOutput:
        """Execute the Checker agent."""
        self.logger.info("Executing Checker agent")
        context.advance_step()
        
        result = await self.checker.run(maker_output)
        
        if result.is_successful():
            context.add_checker_data(result.data.dict() if hasattr(result.data, 'dict') else result.to_dict())
        else:
            context.add_error(f"Checker failed: {result.errors}")
        
        return result
    
    async def _create_curation_result(
        self,
        workflow_id: str,
        document_id: str,
        scout_profile: DocumentProfile,
        maker_output: MakerOutput,
        validation_report: ValidationReport,
        start_time: float
    ) -> CurationResult:
        """Create the final curation result."""
        total_time = (time.time() - start_time) * 1000
        
        # Determine success based on validation
        success = validation_report.passed
        
        # Aggregate metadata
        metadata = {
            "document_type": scout_profile.document_type.value,
            "detected_language": scout_profile.detected_language,
            "quality_score": scout_profile.quality_score,
            "transformation_type": maker_output.transformation_type.value,
            "maker_confidence": maker_output.confidence_score,
            "validation_passed": validation_report.passed,
            "validation_quality": validation_report.quality_score,
        }
        
        # Create execution summary
        execution_summary = {
            "scout_completed": True,
            "maker_completed": True,
            "checker_completed": True,
            "total_issues": len(validation_report.issues),
            "critical_issues": len([
                issue for issue in validation_report.issues
                if issue.severity.value == "critical"
            ]),
            "error_issues": len([
                issue for issue in validation_report.issues
                if issue.severity.value == "error"
            ]),
            "warning_issues": len([
                issue for issue in validation_report.issues
                if issue.severity.value == "warning"
            ]),
        }
        
        return CurationResult(
            workflow_id=workflow_id,
            workflow_name=self.workflow_name,
            document_id=document_id,
            success=success,
            scout_profile=scout_profile.dict() if hasattr(scout_profile, 'dict') else None,
            maker_outputs=[maker_output.dict() if hasattr(maker_output, 'dict') else {}],
            validation_reports=[validation_report.dict() if hasattr(validation_report, 'dict') else {}],
            final_output=maker_output.generated_content,
            metadata=metadata,
            execution_summary=execution_summary,
            total_processing_time_ms=total_time,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.now()
        )
    
    def _create_failure_output(
        self,
        workflow_id: str,
        document_id: str,
        message: str,
        errors: List[str],
        start_time: float
    ) -> AgentOutput:
        """Create a failure output."""
        total_time = (time.time() - start_time) * 1000
        
        curation_result = CurationResult(
            workflow_id=workflow_id,
            workflow_name=self.workflow_name,
            document_id=document_id,
            success=False,
            final_output=None,
            metadata={"error": message},
            execution_summary={"failed": True, "errors": errors},
            total_processing_time_ms=total_time,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.now()
        )
        
        return AgentOutput(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            data=curation_result,
            errors=[message] + errors
        )
    
    def get_sub_agents(self) -> Dict[str, Agent]:
        """Get all sub-agents managed by this curator."""
        return {
            "scout": self.scout,
            "maker": self.maker,
            "checker": self.checker,
        }
    
    async def execute_custom_workflow(
        self,
        document: Document,
        workflow_steps: List[Dict[str, Any]]
    ) -> AgentOutput:
        """
        Execute a custom workflow with specified steps.
        
        Args:
            document: Document to process
            workflow_steps: List of workflow step definitions
        
        Returns:
            AgentOutput with results
        """
        self.logger.info(f"Executing custom workflow with {len(workflow_steps)} steps")
        
        # This is a placeholder for custom workflow execution
        # In production, this would parse and execute the workflow steps
        
        return await self.execute(document)
