"""
Text document parser for plain text and markdown files.
"""

from pathlib import Path
from typing import List

from .base_parser import BaseParser
from models.document import Document, DocumentType, DocumentMetadata


class TextParser(BaseParser):
    """Parser for plain text and markdown documents."""
    
    def can_parse(self, document: Document) -> bool:
        """Check if document is a text-based file."""
        return document.document_type in [
            DocumentType.TXT,
            DocumentType.MARKDOWN,
            DocumentType.HTML,
            DocumentType.JSON,
            DocumentType.XML,
        ]
    
    def get_supported_types(self) -> List[DocumentType]:
        """Get supported document types."""
        return [
            DocumentType.TXT,
            DocumentType.MARKDOWN,
            DocumentType.HTML,
            DocumentType.JSON,
            DocumentType.XML,
        ]
    
    def parse(self, document: Document) -> Document:
        """
        Parse text document.
        
        Args:
            document: Document to parse
        
        Returns:
            Document with populated content
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    content = document.file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("Could not decode file with any supported encoding")
            
            # Update document
            document.content = content
            
            # Update metadata
            document.metadata.character_count = len(content)
            document.metadata.word_count = len(content.split())
            
            # Extract title from first line if markdown
            if document.document_type == DocumentType.MARKDOWN:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        document.metadata.title = line[2:].strip()
                        break
            
            return document
            
        except Exception as e:
            raise ValueError(f"Failed to parse text document: {str(e)}")
