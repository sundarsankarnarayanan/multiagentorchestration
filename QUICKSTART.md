# AI Agent System - Quick Start Guide

## Installation

```bash
cd /Users/sundar/Projects/AIproject
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies (pydantic, pyyaml, pytest, etc.)
- Set up the project for use

## Running Examples

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Basic Workflow Example
```bash
python examples/basic_workflow.py
```

**What it does:**
- Creates a sample document about AI in healthcare
- Runs Scout agent (document analysis)
- Runs Maker agent (summarization)
- Runs Checker agent (validation)
- Curator orchestrates everything
- Shows complete results

**Expected output:**
- Processing time: <1ms
- Quality score: 0.85
- Generated summary of the document

### Custom Workflow Example
```bash
python examples/custom_workflow.py
```

**What it demonstrates:**
- Loading workflows from YAML files
- Creating workflows programmatically
- Running multiple workflows on same document
- Different transformation types (summarization, classification, extraction)

### Verification Tests
```bash
python test_system.py
```

**Tests:**
- ✓ Module imports
- ✓ Document creation
- ✓ Scout agent functionality
- ✓ Workflow definition loading

## Creating Your Own Workflow

### Option 1: Use Curator Agent (Simple)

```python
import asyncio
from models.document import Document
from agents.curator import CuratorAgent

async def main():
    # Create document
    doc = Document.from_file("your_document.txt")
    
    # Configure curator
    curator = CuratorAgent(
        name="my_workflow",
        config={
            "maker_config": {
                "transformation_type": "summarization"
            }
        }
    )
    
    # Run workflow
    result = await curator.run(doc)
    print(result.data.final_output)

asyncio.run(main())
```

### Option 2: Use Workflow Engine (Advanced)

Create `my_workflow.yaml`:
```yaml
name: my_custom_workflow
description: My workflow description
version: "1.0"

steps:
  - name: analyze
    agent_type: scout
    input_from: document
  
  - name: transform
    agent_type: maker
    config:
      transformation_type: summarization
    input_from: scout
  
  - name: validate
    agent_type: checker
    input_from: maker
```

Run it:
```python
from workflows import WorkflowEngine
from models.document import Document

async def main():
    doc = Document.from_file("document.txt")
    engine = WorkflowEngine()
    result = await engine.execute_workflow_from_file(
        "my_workflow.yaml", 
        doc
    )
    print(result.final_output)
```

## Transformation Types

The Maker agent supports:
- `summarization`: Generate summaries
- `extraction`: Extract structured data
- `classification`: Categorize documents
- `translation`: Translate content (placeholder)
- `generation`: Generate new content

## Configuration

Set via environment variables or config dict:

```bash
# .env file
AGENT_MAKER_TRANSFORMATION_TYPE=summarization
AGENT_CHECKER_MIN_QUALITY_SCORE=0.7
```

Or in code:
```python
config = {
    "maker_config": {
        "transformation_type": "classification",
        "max_output_length": 500
    },
    "checker_config": {
        "min_quality_score": 0.8,
        "strict_mode": True
    }
}
```

## Project Structure

```
AIproject/
├── agents/          # Scout, Maker, Checker, Curator
├── models/          # Data models
├── parsers/         # Document parsers
├── workflows/       # Workflow engine + templates
├── examples/        # Example scripts
└── venv/           # Virtual environment (after setup)
```

## Next Steps

1. **Try the examples** - Run basic_workflow.py and custom_workflow.py
2. **Create custom workflows** - Define your own YAML workflows
3. **Extend agents** - Add custom transformation types or validation rules
4. **Add parsers** - Support new document formats
5. **Integrate LLMs** - Connect to OpenAI, Anthropic, etc. for real AI processing

## Troubleshooting

**Import errors**: Make sure virtual environment is activated
```bash
source venv/bin/activate
```

**Module not found**: Run from project root directory
```bash
cd /Users/sundar/Projects/AIproject
```

**Dependencies missing**: Re-run setup
```bash
./setup.sh
```

## Performance

Typical processing times:
- Small documents (<1KB): <1ms
- Medium documents (1-10KB): 1-5ms
- Large documents (>10KB): 5-50ms

Times are for the simplified implementation. With real LLM integration, expect 100-1000ms per transformation.
