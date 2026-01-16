# OCR Agent System - Improvements Documentation

## Overview

This document outlines the improvements made to the Scout-Checker-Curator-Maker agent system to transform it into a fully functional OCR processing pipeline.

## What Was Improved

### 1. **OCR Engine Integration** ✅

**Previous State:**
- No actual OCR functionality
- Maker agent only had placeholder text transformations
- Could not process images or scanned documents

**Improvements:**
- Added **Tesseract OCR** integration with pytesseract
- Support for PDF to image conversion using pdf2image
- Image preprocessing with OpenCV:
  - Noise removal
  - Adaptive thresholding
  - Automatic deskewing
  - Grayscale conversion
- Multi-page PDF support with page-by-page processing
- Confidence scoring for OCR quality assessment

**Files Modified:**
- `agents/maker.py` - Added `_perform_ocr()` method with full OCR pipeline
- `models/agent_output.py` - Added `OCR` transformation type
- `requirements.txt` - Added OCR dependencies

---

### 2. **Image Analysis & Preprocessing** ✅

**Previous State:**
- Scout agent only analyzed text documents
- No image quality assessment
- No OCR readiness evaluation

**Improvements:**
- Added comprehensive image analysis in Scout agent:
  - Image dimensions and resolution
  - DPI detection
  - Sharpness/blur detection using Laplacian variance
  - Brightness and contrast analysis
  - OCR readiness scoring
  - Preprocessing recommendations
- Automatic detection of image-based vs text-based PDFs

**Files Modified:**
- `agents/scout.py` - Added `_analyze_image_properties()` method
- Image quality metrics help determine if preprocessing is needed

---

### 3. **AI Post-Processing** ✅

**Previous State:**
- No AI-powered correction of OCR errors
- OCR output was raw and often contained errors

**Improvements:**
- Integration with **Anthropic Claude** and **OpenAI GPT** for OCR correction
- AI post-processing can:
  - Fix common OCR errors (l vs 1, O vs 0)
  - Correct spelling mistakes
  - Fix punctuation and spacing
  - Improve formatting while preserving structure
- Configurable AI provider (Anthropic or OpenAI)
- Graceful fallback if AI is unavailable

**Files Modified:**
- `agents/maker.py` - Added `_ai_postprocess_ocr()`, `_anthropic_postprocess()`, `_openai_postprocess()`

---

### 4. **Enhanced PDF Parser** ✅

**Previous State:**
- Basic PDF parsing
- No detection of image-based PDFs
- Limited metadata extraction

**Improvements:**
- Automatic detection of text-based vs image-based PDFs
- Heuristic analysis (characters per page) to determine OCR needs
- Enhanced metadata extraction
- Sets `requires_ocr` flag for image-based PDFs
- Better error handling and logging

**Files Modified:**
- `parsers/pdf_parser.py` - Enhanced with OCR detection

---

### 5. **Bug Fixes** ✅

**Issues Fixed:**
1. **Curator agent line 277** - Fixed index out of bounds error when accessing validation issues
2. **Import handling** - Added graceful handling of optional dependencies
3. **Error handling** - Improved error messages and exception handling throughout

**Files Modified:**
- `agents/curator.py` - Fixed critical bug in execution summary

---

### 6. **Configuration & Workflow** ✅

**Previous State:**
- No OCR-specific workflow examples
- Limited configuration options

**Improvements:**
- Created `ocr_extraction.yaml` workflow template
- Comprehensive OCR configuration options:
  - Language selection (eng, fra, deu, etc.)
  - Preprocessing toggles
  - Deskewing options
  - AI post-processing configuration
  - API key configuration
- Example usage script with multiple scenarios

**Files Created:**
- `workflows/templates/ocr_extraction.yaml` - Complete OCR workflow
- `example_ocr.py` - Comprehensive usage examples

---

## Architecture: Scout-Maker-Checker-Curator Pattern

### How It Works for OCR

```
┌─────────────────────────────────────────────────────────────┐
│                        CURATOR                              │
│                   (Orchestrator Agent)                      │
│                                                             │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐      │
│  │  SCOUT    │ ───> │  MAKER    │ ───> │  CHECKER  │      │
│  │ (Analyze) │      │   (OCR)   │      │ (Validate)│      │
│  └───────────┘      └───────────┘      └───────────┘      │
│                                                             │
│  Scout:              Maker:              Checker:          │
│  • Detect doc type   • Extract text     • Validate output │
│  • Analyze quality   • Preprocess imgs  • Check confidence│
│  • OCR readiness     • Run Tesseract    • Quality scoring │
│  • Metadata          • AI correction    • Error detection │
└─────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

1. **Scout Agent** (Document Analyzer)
   - Examines document properties
   - Analyzes image quality for OCR suitability
   - Provides preprocessing recommendations
   - Creates document profile

2. **Maker Agent** (OCR Processor)
   - Converts PDFs to images
   - Preprocesses images (denoise, threshold, deskew)
   - Runs Tesseract OCR
   - Optionally applies AI post-processing
   - Generates structured output with confidence scores

3. **Checker Agent** (Quality Validator)
   - Validates OCR output quality
   - Runs validation rules
   - Checks confidence thresholds
   - Generates validation report

4. **Curator Agent** (Orchestrator)
   - Coordinates the entire workflow
   - Manages agent execution order
   - Aggregates results
   - Provides final curated output

---

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Install Poppler (for PDF to Image conversion)

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download from: https://blog.alivate.com.au/poppler-windows/

### 4. (Optional) Set API Keys for AI Post-Processing

**Method 1: Using .env file (Recommended)**

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and set your API keys:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
OPENAI_API_KEY=sk-your-actual-key-here
```

**Method 2: Shell environment variables**

```bash
export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"
export OPENAI_API_KEY="sk-your-actual-key-here"
```

**Security Note:** The `.env` file is automatically ignored by git. Never commit API keys!

---

## Usage

### Basic OCR Example

```python
import asyncio
from pathlib import Path
from agents import MakerAgent
from models.document import Document

async def run_ocr():
    # Create document
    document = Document.from_file("document.pdf")

    # Configure OCR
    config = {
        "transformation_type": "ocr",
        "ocr_config": {
            "language": "eng",
            "preprocess": True,
            "deskew": True,
        }
    }

    # Create and run OCR agent
    maker = MakerAgent(config=config)
    result = await maker.run(document)

    if result.is_successful():
        print(result.data.generated_content)

asyncio.run(run_ocr())
```

### Full Workflow with AI Post-Processing

```python
from agents import CuratorAgent
from models.document import Document

async def run_full_workflow():
    document = Document.from_file("scanned_document.pdf")

    config = {
        "workflow_name": "ocr_workflow",
        "maker_config": {
            "transformation_type": "ocr",
            "ocr_config": {
                "language": "eng",
                "preprocess": True,
                "deskew": True,
                "ai_postprocess": True,
                "ai_provider": "anthropic",
                "anthropic_api_key": "your-api-key"
            }
        }
    }

    curator = CuratorAgent(config=config)
    result = await curator.run(document)

    return result.data.final_output

asyncio.run(run_full_workflow())
```

### Using Workflow YAML

```python
from workflows import WorkflowEngine
from models.document import Document

async def run_yaml_workflow():
    engine = WorkflowEngine()
    document = Document.from_file("document.pdf")

    result = await engine.execute_workflow_from_file(
        "workflows/templates/ocr_extraction.yaml",
        document
    )

    return result

asyncio.run(run_yaml_workflow())
```

---

## Configuration Options

### OCR Configuration

```python
ocr_config = {
    # Tesseract language (see: tesseract --list-langs)
    "language": "eng",              # eng, fra, deu, spa, etc.

    # Image preprocessing
    "preprocess": True,             # Enable preprocessing
    "deskew": True,                 # Auto-deskew images

    # AI post-processing
    "ai_postprocess": False,        # Enable AI correction
    "ai_provider": "anthropic",     # or "openai"
    # API keys are automatically loaded from environment variables
    # No need to pass them in config
}
```

### Scout Configuration

```python
scout_config = {
    "preview_length": 500,          # Content preview length
    "extract_metadata": True,       # Extract document metadata
    "analyze_structure": True,      # Analyze document structure
}
```

### Checker Configuration

```python
checker_config = {
    "min_quality_score": 0.6,       # Minimum quality threshold
    "strict_mode": False,           # Fail on warnings
}
```

---

## Supported Formats

- **PDF** (both text-based and image-based)
- **Images**: JPG, JPEG, PNG, TIFF, TIF, BMP
- **Multi-page documents** supported

---

## Performance Tips

1. **Use high-resolution scans** (300 DPI minimum)
2. **Enable preprocessing** for better OCR accuracy
3. **Use AI post-processing** for critical documents
4. **Batch processing** for multiple files (see `example_ocr.py`)
5. **Language selection** - specify correct language for better results

---

## Troubleshooting

### OCR Returns Empty Text

**Possible causes:**
1. Image quality too low
2. Wrong language selected
3. Image needs preprocessing

**Solutions:**
- Check Scout agent's `ocr_readiness_score`
- Enable preprocessing with `preprocess: true`
- Try different Tesseract language
- Increase image resolution

### AI Post-Processing Fails

**Possible causes:**
1. API key not set
2. Rate limits exceeded
3. Network issues

**Solutions:**
- Verify API key is correctly set
- Check API usage limits
- Add retry logic
- Fall back to raw OCR output

### Low Confidence Scores

**Possible causes:**
1. Poor image quality
2. Complex layouts
3. Multiple languages

**Solutions:**
- Improve scan quality
- Use preprocessing
- Enable AI post-processing
- Adjust validation thresholds

---

## Architecture Decisions

### Why This Pattern?

The **Scout-Maker-Checker-Curator** pattern provides:

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Flexibility**: Easy to swap or configure individual agents
3. **Observability**: Clear visibility into each processing stage
4. **Quality Control**: Built-in validation and error detection
5. **Extensibility**: Easy to add new agents or transformations

### Why Tesseract?

- Open source and free
- Supports 100+ languages
- Active development
- Good accuracy with preprocessing
- Can be enhanced with AI post-processing

### Why Optional AI Post-Processing?

- Significantly improves accuracy
- Corrects common OCR errors
- Optional to avoid API costs
- Falls back gracefully if unavailable

---

## Future Improvements

Potential enhancements:

1. **Multiple OCR Engine Support**
   - EasyOCR
   - PaddleOCR
   - Azure Computer Vision
   - Google Cloud Vision

2. **Advanced Preprocessing**
   - Page segmentation
   - Layout analysis
   - Table detection
   - Handwriting recognition

3. **Post-Processing Options**
   - Spell checking
   - Entity recognition
   - Format conversion (Markdown, HTML)
   - Translation

4. **Performance Optimizations**
   - Parallel page processing
   - Caching
   - GPU acceleration

---

## Summary

The improved OCR agent system now provides:

✅ **Full OCR functionality** with Tesseract
✅ **Image preprocessing** for better accuracy
✅ **AI-powered post-processing** to fix errors
✅ **Quality assessment** and validation
✅ **Multi-page PDF support**
✅ **Flexible configuration** options
✅ **Production-ready** error handling
✅ **Comprehensive examples** and documentation

The Scout-Checker-Curator-Maker pattern creates a robust, maintainable, and extensible OCR processing pipeline suitable for production use.
