"""
Example script demonstrating OCR agent usage.

This script shows how to:
1. Process a PDF or image file with OCR
2. Use the Scout-Maker-Checker-Curator pattern
3. Configure OCR settings
4. Enable AI post-processing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agents import ScoutAgent, MakerAgent, CheckerAgent, CuratorAgent
from models.document import Document
from models.agent_output import TransformationType


async def simple_ocr_example():
    """
    Simple example: Direct OCR without workflow.
    """
    print("=" * 60)
    print("Simple OCR Example")
    print("=" * 60)

    # Create a test image or PDF path (you need to provide this)
    test_file = Path("test_document.pdf")  # Replace with your test file

    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        print("Please create a test file or update the path.")
        return

    # Create document
    document = Document.from_file(test_file)
    print(f"\nDocument: {document.get_filename()}")
    print(f"Type: {document.document_type.value}")
    print(f"Size: {document.size_bytes / 1024:.2f} KB")

    # Configure OCR
    ocr_config = {
        "transformation_type": "ocr",
        "ocr_config": {
            "language": "eng",  # English
            "preprocess": True,  # Enable image preprocessing
            "deskew": True,      # Auto-deskew images
            "ai_postprocess": False,  # Set to True to use AI (requires API key)
            "ai_provider": "anthropic",  # or "openai"
            # Note: API keys are now automatically loaded from environment variables
            # Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file or shell environment
        }
    }

    # Create Maker agent for OCR
    maker = MakerAgent(name="ocr_extractor", config=ocr_config)

    # Run OCR
    print("\nRunning OCR...")
    result = await maker.run(document)

    if result.is_successful():
        print("\nOCR successful!")
        maker_output = result.data
        print(f"Confidence: {maker_output.confidence_score:.2%}")
        print(f"Processing time: {maker_output.processing_time_ms:.2f}ms")
        print(f"\nExtracted text ({len(maker_output.generated_content)} chars):")
        print("-" * 60)
        print(maker_output.generated_content[:500])  # First 500 chars
        if len(maker_output.generated_content) > 500:
            print(f"... ({len(maker_output.generated_content) - 500} more characters)")
    else:
        print("\nOCR failed!")
        print(f"Errors: {result.errors}")


async def full_workflow_example():
    """
    Full workflow example using Scout-Maker-Checker-Curator pattern.
    """
    print("\n\n" + "=" * 60)
    print("Full Workflow Example")
    print("=" * 60)

    # Create a test file
    test_file = Path("test_document.pdf")  # Replace with your test file

    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return

    # Create document
    document = Document.from_file(test_file)

    # Configure the full workflow
    workflow_config = {
        "workflow_name": "ocr_workflow",
        "scout_config": {
            "preview_length": 500,
            "extract_metadata": True,
            "analyze_structure": True,
        },
        "maker_config": {
            "transformation_type": "ocr",
            "ocr_config": {
                "language": "eng",
                "preprocess": True,
                "deskew": True,
                "ai_postprocess": False,  # Enable for AI post-processing
                "ai_provider": "anthropic",
            }
        },
        "checker_config": {
            "min_quality_score": 0.5,
            "strict_mode": False,
        }
    }

    # Create Curator (orchestrates Scout-Maker-Checker)
    curator = CuratorAgent(name="ocr_curator", config=workflow_config)

    print(f"\nProcessing: {document.get_filename()}")
    print("Running full OCR workflow...")
    print("Steps: Scout -> Maker (OCR) -> Checker")

    # Execute workflow
    result = await curator.run(document)

    if result.is_successful():
        print("\nWorkflow completed successfully!")
        curation_result = result.data

        print(f"\nWorkflow Summary:")
        print(f"  Success: {curation_result.success}")
        print(f"  Total time: {curation_result.total_processing_time_ms:.2f}ms")

        # Scout results
        if curation_result.scout_profile:
            scout_profile = curation_result.scout_profile
            print(f"\n  Scout Analysis:")
            print(f"    Quality score: {scout_profile.get('quality_score', 0):.2f}")
            print(f"    Language: {scout_profile.get('detected_language', 'unknown')}")
            stats = scout_profile.get('statistics', {})
            if 'ocr_readiness_score' in stats:
                print(f"    OCR readiness: {stats['ocr_readiness_score']:.2f}")
            if 'preprocessing_recommendations' in stats:
                recs = stats['preprocessing_recommendations']
                if recs:
                    print(f"    Recommendations:")
                    for rec in recs[:3]:  # Show first 3
                        print(f"      - {rec}")

        # Maker (OCR) results
        if curation_result.maker_outputs:
            maker_output = curation_result.maker_outputs[0]
            print(f"\n  OCR Extraction:")
            print(f"    Confidence: {maker_output.get('confidence_score', 0):.2%}")
            print(f"    Processing time: {maker_output.get('processing_time_ms', 0):.2f}ms")
            metadata = maker_output.get('metadata', {})
            print(f"    Pages processed: {metadata.get('pages_processed', 0)}")
            if metadata.get('ai_postprocessed'):
                print(f"    AI post-processed: Yes ({metadata.get('ai_model', 'unknown')})")

        # Checker results
        if curation_result.validation_reports:
            validation = curation_result.validation_reports[0]
            print(f"\n  Quality Check:")
            print(f"    Passed: {validation.get('passed', False)}")
            print(f"    Quality score: {validation.get('quality_score', 0):.2f}")
            print(f"    Issues found: {len(validation.get('issues', []))}")

        # Final output
        print(f"\n  Extracted Text ({len(curation_result.final_output or '')} chars):")
        print("  " + "-" * 58)
        text = str(curation_result.final_output or "")
        print("  " + text[:500].replace("\n", "\n  "))
        if len(text) > 500:
            print(f"  ... ({len(text) - 500} more characters)")

    else:
        print("\nWorkflow failed!")
        print(f"Errors: {result.errors}")


async def batch_ocr_example():
    """
    Example of processing multiple files in batch.
    """
    print("\n\n" + "=" * 60)
    print("Batch OCR Example")
    print("=" * 60)

    # Define files to process
    files = [
        "document1.pdf",
        "document2.pdf",
        "scan1.jpg",
    ]

    # Filter existing files
    files = [Path(f) for f in files if Path(f).exists()]

    if not files:
        print("No test files found for batch processing.")
        return

    print(f"\nProcessing {len(files)} files...")

    # Create OCR agent
    ocr_config = {
        "transformation_type": "ocr",
        "ocr_config": {
            "language": "eng",
            "preprocess": True,
            "deskew": True,
        }
    }
    maker = MakerAgent(name="batch_ocr", config=ocr_config)

    results = []
    for file_path in files:
        print(f"\nProcessing: {file_path.name}")
        document = Document.from_file(file_path)
        result = await maker.run(document)

        if result.is_successful():
            maker_output = result.data
            results.append({
                "file": file_path.name,
                "success": True,
                "confidence": maker_output.confidence_score,
                "text_length": len(maker_output.generated_content),
                "time_ms": maker_output.processing_time_ms,
            })
            print(f"  Success! Confidence: {maker_output.confidence_score:.2%}")
        else:
            results.append({
                "file": file_path.name,
                "success": False,
                "error": result.errors[0] if result.errors else "Unknown error"
            })
            print(f"  Failed: {result.errors}")

    # Summary
    print(f"\n{'=' * 60}")
    print("Batch Processing Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    if successful > 0:
        avg_conf = sum(r["confidence"] for r in results if r["success"]) / successful
        avg_time = sum(r["time_ms"] for r in results if r["success"]) / successful
        print(f"Average confidence: {avg_conf:.2%}")
        print(f"Average time: {avg_time:.2f}ms")


def config_check_example():
    """
    Example showing how to check if API keys are configured.
    """
    print("\n" + "=" * 60)
    print("Configuration Check Example")
    print("=" * 60)

    from config import get_config

    config = get_config()
    credentials = config.credentials.get_redacted_dict()

    print("\nAPI Key Status:")
    print(f"  Anthropic: {credentials['anthropic_api_key']}")
    print(f"  OpenAI: {credentials['openai_api_key']}")

    print("\nTo configure:")
    print("  1. Create .env file: cp .env.example .env")
    print("  2. Edit .env and set: ANTHROPIC_API_KEY=sk-ant-...")
    print("  3. Or export in shell: export ANTHROPIC_API_KEY='sk-ant-...'")

    # Test validation
    test_config = {"ai_postprocess": True, "ai_provider": "anthropic"}
    from config import validate_ocr_config
    warnings = validate_ocr_config(test_config)

    if warnings:
        print("\n⚠ Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✓ API keys configured correctly!")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("OCR Agent System Examples")
    print("=" * 60)

    # Run examples
    try:
        # First check configuration
        config_check_example()

        await simple_ocr_example()
        await full_workflow_example()
        # await batch_ocr_example()  # Uncomment if you have multiple files
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: Before running, ensure you have:
    # 1. Installed dependencies: pip install -r requirements.txt
    # 2. Installed Tesseract OCR: https://github.com/tesseract-ocr/tesseract
    # 3. Created test files (PDFs or images)
    # 4. (Optional) Set API keys for AI post-processing

    asyncio.run(main())
