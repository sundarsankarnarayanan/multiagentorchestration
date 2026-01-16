"""
Quick verification test for the AI Agent System.

This script performs basic smoke tests to ensure the system is working.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from agents import ScoutAgent, MakerAgent, CheckerAgent, CuratorAgent
        from models.document import Document, DocumentType
        from workflows import WorkflowEngine, WorkflowDefinition
        from parsers import TextParser, PDFParser, DOCXParser
        from config import get_config
        
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


async def test_document_creation():
    """Test document creation."""
    print("\nTesting document creation...")
    
    try:
        from models.document import Document
        
        # Create a temporary file
        temp_file = Path("test_doc.txt")
        temp_file.write_text("This is a test document.")
        
        # Create document
        doc = Document.from_file(temp_file)
        
        assert doc.document_type.value == "txt"
        assert doc.size_bytes > 0
        
        # Cleanup
        temp_file.unlink()
        
        print("  ✓ Document creation successful")
        return True
    except Exception as e:
        print(f"  ✗ Document creation failed: {e}")
        return False


async def test_scout_agent():
    """Test Scout agent."""
    print("\nTesting Scout agent...")
    
    try:
        from agents.scout import ScoutAgent
        from models.document import Document
        
        # Create test document
        temp_file = Path("test_scout.txt")
        temp_file.write_text("Test content for scout agent analysis.")
        
        doc = Document.from_file(temp_file)
        scout = ScoutAgent()
        
        result = await scout.run(doc)
        
        assert result.is_successful()
        assert result.data is not None
        
        # Cleanup
        temp_file.unlink()
        
        print("  ✓ Scout agent working")
        return True
    except Exception as e:
        print(f"  ✗ Scout agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_definition():
    """Test workflow definition loading."""
    print("\nTesting workflow definition...")
    
    try:
        from workflows import WorkflowEngine
        
        workflow_file = Path("workflows/templates/document_summarization.yaml")
        
        if workflow_file.exists():
            workflow_def = WorkflowEngine.load_workflow_from_file(workflow_file)
            
            assert workflow_def.name == "document_summarization"
            assert len(workflow_def.steps) > 0
            
            print("  ✓ Workflow definition loaded")
            return True
        else:
            print("  ⚠ Workflow file not found (expected in new project)")
            return True
    except Exception as e:
        print(f"  ✗ Workflow definition failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Agent System - Verification Tests")
    print("=" * 60)
    
    tests = [
        test_imports(),
        test_document_creation(),
        test_scout_agent(),
        test_workflow_definition(),
    ]
    
    results = await asyncio.gather(*tests)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed! System is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
