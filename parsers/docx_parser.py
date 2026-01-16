"""
Microsoft Word (DOCX) document parser.

Note: This is a simplified implementation. For production use,
consider using the python-docx library.
"""

from typing import List
from pathlib import Path

from .base_parser import BaseParser
from models.document import Document, DocumentType, DocumentMetadata


class DOCXParser(BaseParser):
    """Parser for Microsoft Word documents."""
    
    def can_parse(self, document: Document) -> bool:
        """Check if document is a DOCX file."""
        return document.document_type == DocumentType.DOCX
    
    def get_supported_types(self) -> List[DocumentType]:
        """Get supported document types."""
        return [DocumentType.DOCX]
    
    def parse(self, document: Document) -> Document:
        """
        Parse DOCX document.
        
        This is a placeholder implementation. In production, you would use
        the python-docx library to extract text and metadata.
        
        Args:
            document: Document to parse
        
        Returns:
            Document with populated content
        """
        try:
            # Placeholder: In production, use python-docx
            # Example with python-docx:
            # from docx import Document as DocxDocument
            # docx = DocxDocument(document.file_path)
            # text = "\n".join([paragraph.text for paragraph in docx.paragraphs])
            # document.content = text
            # document.metadata.title = docx.core_properties.title
            # document.metadata.author = docx.core_properties.author
            
            # For now, just mark as DOCX and add placeholder
            document.content = f"[DOCX content from {document.get_filename()}]"
            document.metadata.title = document.file_path.stem
            
            return document
            
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX document: {str(e)}")
