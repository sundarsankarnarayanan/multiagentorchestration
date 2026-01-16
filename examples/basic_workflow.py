"""
Basic workflow example demonstrating the Scout-Maker-Checker-Curator pattern.

This example shows how to:
1. Create a document
2. Set up a curator agent
3. Execute a complete workflow
4. Access the results
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.document import Document
from agents.curator import CuratorAgent


async def main():
    """Run the basic workflow example."""
    
    print("=" * 60)
    print("AI Agent System - Basic Workflow Example")
    print("Scout-Maker-Checker-Curator Pattern")
    print("=" * 60)
    print()
    
    # Create a sample text document
    sample_text = """
    Artificial Intelligence in Modern Healthcare
    
    Artificial intelligence (AI) is revolutionizing the healthcare industry.
    From diagnostic imaging to drug discovery, AI systems are helping medical
    professionals make better decisions and improve patient outcomes.
    
    Machine learning algorithms can analyze medical images with remarkable
    accuracy, often detecting patterns that human eyes might miss. Natural
    language processing helps extract insights from medical records and
    research papers.
    
    The future of healthcare will likely see even greater integration of AI
    technologies, leading to more personalized and effective treatments.
    """
    
    # Create a temporary file
    temp_file = Path("sample_document.txt")
    temp_file.write_text(sample_text.strip())
    
    try:
        # Step 1: Create a Document object
        print("Step 1: Creating document...")
        document = Document.from_file(temp_file)
        print(f"  ✓ Document created: {document.get_filename()}")
        print(f"  ✓ Document type: {document.document_type.value}")
        print(f"  ✓ Size: {document.size_bytes} bytes")
        print()
        
        # Step 2: Set up the Curator agent
        print("Step 2: Initializing Curator agent...")
        curator = CuratorAgent(
            name="example_curator",
            config={
                "workflow_name": "document_summarization",
                "scout_config": {
                    "preview_length": 500,
                    "extract_metadata": True,
                },
                "maker_config": {
                    "transformation_type": "summarization",
                    "max_output_length": 200,
                },
                "checker_config": {
                    "min_quality_score": 0.5,
                },
            }
        )
        print("  ✓ Curator agent initialized")
        print()
        
        # Step 3: Execute the workflow
        print("Step 3: Executing workflow...")
        print("  → Scout: Analyzing document...")
        print("  → Maker: Generating summary...")
        print("  → Checker: Validating output...")
        print()
        
        result = await curator.run(document)
        
        # Step 4: Display results
        print("Step 4: Results")
        print("=" * 60)
        
        if result.is_successful():
            print("✓ Workflow completed successfully!")
            print()
            
            curation_result = result.data
            
            print("Summary:")
            print("-" * 60)
            print(curation_result.get_summary())
            print()
            
            print("Generated Content:")
            print("-" * 60)
            print(curation_result.final_output)
            print()
            
            print("Metadata:")
            print("-" * 60)
            for key, value in curation_result.metadata.items():
                print(f"  {key}: {value}")
            print()
            
            print("Execution Summary:")
            print("-" * 60)
            for key, value in curation_result.execution_summary.items():
                print(f"  {key}: {value}")
            print()
            
            print(f"Total processing time: {curation_result.total_processing_time_ms:.2f}ms")
            
        else:
            print("✗ Workflow failed!")
            print()
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        print()
        print("=" * 60)
        
    finally:
        # Clean up
        if temp_file.exists():
            temp_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())
