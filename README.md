# AI Agent System - Scout-Maker-Checker-Curator Pattern

A modular AI agent system for document parsing and workflow automation using the scout-maker-checker-curator pattern.

## Overview

This system implements a sophisticated multi-agent architecture where specialized agents work together in a pipeline:

- **Scout Agent**: Discovers and analyzes documents, extracts metadata, identifies document characteristics
- **Maker Agent**: Transforms and generates content (summarization, extraction, classification, etc.)
- **Checker Agent**: Validates outputs, ensures quality, flags issues
- **Curator Agent**: Orchestrates the entire workflow, manages state, coordinates agents

## Architecture

```
Document → Scout → Maker → Checker → Curator → Final Output
           ↓        ↓        ↓          ↓
        Analysis  Transform Validate  Curate
```

## Features

- ✅ **Modular Design**: Each agent is independent and extensible
- ✅ **Workflow Engine**: Define workflows in YAML/JSON
- ✅ **Multiple Document Types**: PDF, DOCX, TXT, Markdown, HTML, JSON, XML
- ✅ **Pre-built Workflows**: Summarization, extraction, classification
- ✅ **Async Execution**: Built on asyncio for concurrent processing
- ✅ **Type Safety**: Full type hints with Pydantic models
- ✅ **Extensible**: Easy to add custom agents and workflows

## Quick Start

### Installation

```bash
# Navigate to the project directory
cd AIproject

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Note**: This project uses Python 3.9+ and requires a virtual environment for dependency management.

### Basic Usage

```python
import asyncio
from models.document import Document
from agents.curator import CuratorAgent

async def main():
    # Create a document
    document = Document.from_file("sample.txt")
    
    # Initialize curator with configuration
    curator = CuratorAgent(
        name="my_curator",
        config={
            "workflow_name": "document_summarization",
            "maker_config": {
                "transformation_type": "summarization",
            }
        }
    )
    
    # Execute the workflow
    result = await curator.run(document)
    
    if result.is_successful():
        print(result.data.final_output)

asyncio.run(main())
```

### Using Workflow Engine

```python
from workflows import WorkflowEngine
from models.document import Document

async def main():
    document = Document.from_file("document.pdf")
    engine = WorkflowEngine()
    
    # Execute a predefined workflow
    result = await engine.execute_workflow_from_file(
        "workflows/templates/document_summarization.yaml",
        document
    )
    
    print(f"Success: {result.success}")
    print(f"Output: {result.final_output}")

asyncio.run(main())
```

## Project Structure

```
AIproject/
├── agents/              # Agent implementations
│   ├── base.py         # Abstract base agent
│   ├── scout.py        # Scout agent
│   ├── maker.py        # Maker agent
│   ├── checker.py      # Checker agent
│   └── curator.py      # Curator agent
├── models/             # Data models
│   ├── document.py     # Document models
│   ├── workflow.py     # Workflow models
│   └── agent_output.py # Agent output models
├── parsers/            # Document parsers
│   ├── base_parser.py  # Parser registry
│   ├── text_parser.py  # Text parser
│   ├── pdf_parser.py   # PDF parser
│   └── docx_parser.py  # DOCX parser
├── workflows/          # Workflow engine
│   ├── engine.py       # Workflow execution engine
│   ├── definition.py   # Workflow definitions
│   └── templates/      # Pre-built workflows
│       ├── document_summarization.yaml
│       ├── data_extraction.yaml
│       └── document_classification.yaml
├── examples/           # Example scripts
│   ├── basic_workflow.py
│   └── custom_workflow.py
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Workflow Definitions

Workflows are defined in YAML format:

```yaml
name: my_workflow
description: Custom workflow
version: "1.0"

steps:
  - name: analyze
    agent_type: scout
    config:
      preview_length: 1000
    input_from: document
  
  - name: transform
    agent_type: maker
    config:
      transformation_type: summarization
    input_from: scout
  
  - name: validate
    agent_type: checker
    config:
      min_quality_score: 0.6
    input_from: maker
```

## Configuration

Configure agents via environment variables or config dictionaries:

```python
# Environment variables
export AGENT_SCOUT_PREVIEW_LENGTH=1000
export AGENT_MAKER_MAX_OUTPUT_LENGTH=500
export AGENT_CHECKER_MIN_QUALITY_SCORE=0.7

# Or via config dict
config = {
    "scout_config": {
        "preview_length": 1000,
        "extract_metadata": True,
    },
    "maker_config": {
        "transformation_type": "summarization",
        "max_output_length": 500,
    },
    "checker_config": {
        "min_quality_score": 0.7,
    }
}
```

## Extending the System

### Creating a Custom Agent

```python
from agents.base import Agent, AgentOutput, AgentStatus

class MyCustomAgent(Agent):
    def validate_input(self, input_data):
        return True
    
    def get_capabilities(self):
        return [AgentCapability.CUSTOM]
    
    async def execute(self, input_data, context=None):
        # Your custom logic here
        return AgentOutput(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            data=result
        )
```

### Adding a Custom Parser

```python
from parsers.base_parser import BaseParser

class MyParser(BaseParser):
    def can_parse(self, document):
        return document.document_type == DocumentType.CUSTOM
    
    def get_supported_types(self):
        return [DocumentType.CUSTOM]
    
    def parse(self, document):
        # Parse logic
        return document
```

## Examples

Run the included examples:

```bash
# Basic workflow example
python examples/basic_workflow.py

# Custom workflow example
python examples/custom_workflow.py
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Type checking
mypy agents/ models/ workflows/

# Linting
flake8 agents/ models/ workflows/
```

## Use Cases

- **Document Summarization**: Automatically generate summaries of long documents
- **Data Extraction**: Extract structured data from unstructured documents
- **Document Classification**: Categorize documents into predefined categories
- **Content Transformation**: Convert documents between formats
- **Quality Assurance**: Validate document content and structure
- **Workflow Automation**: Chain multiple processing steps together

## Future Enhancements

- [ ] Integration with LLM APIs (OpenAI, Anthropic, etc.)
- [ ] Advanced PDF parsing with layout preservation
- [ ] OCR support for scanned documents
- [ ] Parallel workflow execution
- [ ] Workflow visualization
- [ ] REST API interface
- [ ] Web UI for workflow management
- [ ] Database integration for result storage
- [ ] Monitoring and metrics dashboard

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions or issues, please open an issue on GitHub.
