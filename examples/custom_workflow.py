"""
Custom workflow example using the WorkflowEngine.

This example demonstrates:
1. Loading a workflow from a YAML file
2. Executing it with the WorkflowEngine
3. Creating custom workflow definitions programmatically
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.document import Document
from workflows import WorkflowEngine, WorkflowDefinition, WorkflowStep


async def example_1_load_from_file():
    """Example 1: Load and execute a workflow from a YAML file."""
    
    print("\n" + "=" * 60)
    print("Example 1: Loading Workflow from File")
    print("=" * 60)
    
    # Create sample document
    sample_text = """
    Cloud Computing Best Practices
    
    This document outlines best practices for cloud infrastructure management.
    Topics include security, scalability, cost optimization, and monitoring.
    """
    
    temp_file = Path("cloud_doc.txt")
    temp_file.write_text(sample_text.strip())
    
    try:
        document = Document.from_file(temp_file)
        
        # Initialize workflow engine
        engine = WorkflowEngine()
        
        # Load and execute workflow from file
        workflow_file = Path("workflows/templates/document_summarization.yaml")
        
        if workflow_file.exists():
            print(f"\nExecuting workflow from: {workflow_file}")
            result = await engine.execute_workflow_from_file(workflow_file, document)
            
            print(f"\nWorkflow: {result.workflow_name}")
            print(f"Status: {result.state.value}")
            print(f"Success: {result.success}")
            print(f"Duration: {result.duration_ms:.2f}ms")
            
            if result.success:
                print(f"\nFinal Output:")
                print("-" * 60)
                print(result.final_output)
        else:
            print(f"Workflow file not found: {workflow_file}")
    
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def example_2_programmatic_workflow():
    """Example 2: Create a workflow programmatically."""
    
    print("\n" + "=" * 60)
    print("Example 2: Programmatic Workflow Definition")
    print("=" * 60)
    
    # Create sample document
    sample_text = """
    Machine Learning Model Deployment
    
    This guide covers deploying ML models to production environments.
    Key considerations include model versioning, monitoring, and A/B testing.
    """
    
    temp_file = Path("ml_doc.txt")
    temp_file.write_text(sample_text.strip())
    
    try:
        document = Document.from_file(temp_file)
        
        # Create custom workflow definition
        workflow_def = WorkflowDefinition(
            name="custom_analysis",
            description="Custom document analysis workflow",
            version="1.0",
            steps=[
                WorkflowStep(
                    name="scout_step",
                    agent_type="scout",
                    config={
                        "preview_length": 1000,
                        "extract_metadata": True,
                    },
                    input_from="document"
                ),
                WorkflowStep(
                    name="classify_step",
                    agent_type="maker",
                    config={
                        "transformation_type": "classification",
                    },
                    input_from="scout"
                ),
                WorkflowStep(
                    name="validation_step",
                    agent_type="checker",
                    config={
                        "min_quality_score": 0.6,
                    },
                    input_from="maker"
                ),
            ]
        )
        
        # Validate workflow
        errors = workflow_def.validate_workflow()
        if errors:
            print("Workflow validation errors:")
            for error in errors:
                print(f"  - {error}")
            return
        
        print("\n✓ Workflow definition validated")
        print(f"  Name: {workflow_def.name}")
        print(f"  Steps: {len(workflow_def.steps)}")
        
        # Execute workflow
        engine = WorkflowEngine()
        result = await engine.execute_workflow(workflow_def, document)
        
        print(f"\nWorkflow execution complete:")
        print(f"  Success: {result.success}")
        print(f"  Duration: {result.duration_ms:.2f}ms")
        print(f"  Steps completed: {result.context.current_step}/{result.context.total_steps}")
        
        if result.success:
            print(f"\nFinal Output:")
            print("-" * 60)
            print(result.final_output)
    
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def example_3_multiple_workflows():
    """Example 3: Run multiple workflows on the same document."""
    
    print("\n" + "=" * 60)
    print("Example 3: Multiple Workflows on Same Document")
    print("=" * 60)
    
    # Create sample document
    sample_text = """
    Quarterly Financial Report
    
    Revenue: $2.5M (up 15% from Q3)
    Expenses: $1.8M
    Net Profit: $700K
    
    Key highlights include successful product launch and expansion into
    new markets. Customer acquisition cost decreased by 20%.
    """
    
    temp_file = Path("financial_report.txt")
    temp_file.write_text(sample_text.strip())
    
    try:
        document = Document.from_file(temp_file)
        engine = WorkflowEngine()
        
        # Define multiple workflows
        workflows = [
            "workflows/templates/document_summarization.yaml",
            "workflows/templates/data_extraction.yaml",
            "workflows/templates/document_classification.yaml",
        ]
        
        results = []
        
        for workflow_path in workflows:
            workflow_file = Path(workflow_path)
            if workflow_file.exists():
                print(f"\nExecuting: {workflow_file.name}")
                result = await engine.execute_workflow_from_file(workflow_file, document)
                results.append(result)
                print(f"  Status: {result.state.value}")
                print(f"  Duration: {result.duration_ms:.2f}ms")
        
        print(f"\n\nCompleted {len(results)} workflows")
        print(f"Total processing time: {sum(r.duration_ms for r in results):.2f}ms")
    
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def main():
    """Run all examples."""
    
    print("\n" + "=" * 60)
    print("AI Agent System - Custom Workflow Examples")
    print("=" * 60)
    
    await example_1_load_from_file()
    await example_2_programmatic_workflow()
    await example_3_multiple_workflows()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
