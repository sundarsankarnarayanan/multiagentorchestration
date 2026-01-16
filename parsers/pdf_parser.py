"""
PDF document parser with OCR detection support.

Handles both text-based and image-based PDFs.
"""

from typing import List
from pathlib import Path
import logging

from .base_parser import BaseParser
from models.document import Document, DocumentType, DocumentMetadata

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF documents."""
    
    def can_parse(self, document: Document) -> bool:
        """Check if document is a PDF."""
        return document.document_type == DocumentType.PDF
    
    def get_supported_types(self) -> List[DocumentType]:
        """Get supported document types."""
        return [DocumentType.PDF]
    
    def parse(self, document: Document) -> Document:
        """
        Parse PDF document.

        Attempts to extract text directly from PDF. If no text is found,
        marks the PDF as requiring OCR processing.

        Args:
            document: Document to parse

        Returns:
            Document with populated content
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(document.file_path))
            text = []
            total_chars = 0

            # Try to extract text from each page
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
                        total_chars += len(page_text.strip())
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i+1}: {e}")

            # Join text and clean up
            content = "\n".join(text)

            # Determine if this is a text-based or image-based PDF
            page_count = len(reader.pages)
            avg_chars_per_page = total_chars / page_count if page_count > 0 else 0

            # Heuristic: if very few characters per page, likely image-based
            is_likely_scanned = avg_chars_per_page < 50

            if not content.strip() or is_likely_scanned:
                # Image-based PDF or very little text - mark for OCR
                document.content = ""
                document.metadata.custom_properties["requires_ocr"] = True
                document.metadata.custom_properties["pdf_type"] = "image_based"
                logger.info(
                    f"PDF appears to be image-based ({avg_chars_per_page:.1f} chars/page). "
                    "OCR processing recommended."
                )
            else:
                document.content = content
                document.metadata.custom_properties["requires_ocr"] = False
                document.metadata.custom_properties["pdf_type"] = "text_based"
                document.metadata.word_count = len(content.split())
                document.metadata.character_count = len(content)

            # Extract metadata
            document.metadata.page_count = page_count
            if reader.metadata:
                if reader.metadata.title:
                    document.metadata.title = str(reader.metadata.title)
                if reader.metadata.author:
                    document.metadata.author = str(reader.metadata.author)
                if reader.metadata.subject:
                    document.metadata.subject = str(reader.metadata.subject)
                if reader.metadata.creator:
                    document.metadata.custom_properties["creator"] = str(reader.metadata.creator)

            # Use filename as title if missing
            if not document.metadata.title:
                document.metadata.title = document.file_path.stem

            return document

        except ImportError:
            logger.error("pypdf library not installed. Install with: pip install pypdf")
            document.content = ""
            document.metadata.custom_properties["parse_error"] = "pypdf not installed"
            return document

        except Exception as e:
            logger.error(f"Failed to parse PDF document: {e}")
            raise ValueError(f"Failed to parse PDF document: {str(e)}")
