"""
Base parser class and parser registry.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from pathlib import Path

from models.document import Document, DocumentType


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    def can_parse(self, document: Document) -> bool:
        """
        Check if this parser can handle the document.
        
        Args:
            document: Document to check
        
        Returns:
            True if parser can handle this document
        """
        pass
    
    @abstractmethod
    def parse(self, document: Document) -> Document:
        """
        Parse the document and populate its content.
        
        Args:
            document: Document to parse
        
        Returns:
            Document with populated content and metadata
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list[DocumentType]:
        """
        Get list of document types this parser supports.
        
        Returns:
            List of DocumentType enums
        """
        pass


class ParserRegistry:
    """Registry for document parsers."""
    
    def __init__(self):
        self._parsers: Dict[DocumentType, Type[BaseParser]] = {}
        self._parser_instances: Dict[DocumentType, BaseParser] = {}
    
    def register(self, parser_class: Type[BaseParser]) -> None:
        """
        Register a parser class.
        
        Args:
            parser_class: Parser class to register
        """
        parser = parser_class()
        for doc_type in parser.get_supported_types():
            self._parsers[doc_type] = parser_class
            self._parser_instances[doc_type] = parser
    
    def get_parser(self, document: Document) -> Optional[BaseParser]:
        """
        Get appropriate parser for a document.
        
        Args:
            document: Document to parse
        
        Returns:
            Parser instance or None if no parser found
        """
        # Try to get parser by document type
        if document.document_type in self._parser_instances:
            parser = self._parser_instances[document.document_type]
            if parser.can_parse(document):
                return parser
        
        # Try all parsers
        for parser in self._parser_instances.values():
            if parser.can_parse(document):
                return parser
        
        return None
    
    def parse(self, document: Document) -> Document:
        """
        Parse a document using the appropriate parser.
        
        Args:
            document: Document to parse
        
        Returns:
            Parsed document
        
        Raises:
            ValueError: If no suitable parser found
        """
        parser = self.get_parser(document)
        if parser is None:
            raise ValueError(
                f"No parser found for document type: {document.document_type}"
            )
        
        return parser.parse(document)


# Global parser registry
_registry: Optional[ParserRegistry] = None


def get_parser_registry() -> ParserRegistry:
    """Get the global parser registry."""
    global _registry
    if _registry is None:
        _registry = ParserRegistry()
        # Register default parsers
        from .text_parser import TextParser
        from .pdf_parser import PDFParser
        from .docx_parser import DOCXParser
        
        _registry.register(TextParser)
        _registry.register(PDFParser)
        _registry.register(DOCXParser)
    
    return _registry
