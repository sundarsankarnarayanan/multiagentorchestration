"""
Document data models for the AI agent system.

This module defines the data structures for representing documents,
their metadata, and analysis results.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""
    
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    custom_properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Document(BaseModel):
    """Represents a document to be processed."""
    
    id: str = Field(description="Unique identifier for the document")
    file_path: Path = Field(description="Path to the document file")
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    content: Optional[str] = None
    raw_content: Optional[bytes] = None
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    size_bytes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Path: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_file(cls, file_path: str | Path) -> "Document":
        """
        Create a Document instance from a file path.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            Document instance
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Determine document type from extension
        extension = path.suffix.lower().lstrip('.')
        try:
            doc_type = DocumentType(extension)
        except ValueError:
            doc_type = DocumentType.UNKNOWN
        
        # Get file size
        size = path.stat().st_size
        
        # Generate ID from file path and timestamp
        doc_id = f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return cls(
            id=doc_id,
            file_path=path,
            document_type=doc_type,
            size_bytes=size
        )
    
    def get_extension(self) -> str:
        """Get the file extension."""
        return self.file_path.suffix.lower()
    
    def get_filename(self) -> str:
        """Get the filename without path."""
        return self.file_path.name
    
    def is_text_based(self) -> bool:
        """Check if document is text-based."""
        return self.document_type in [
            DocumentType.TXT,
            DocumentType.MARKDOWN,
            DocumentType.HTML,
            DocumentType.JSON,
            DocumentType.XML
        ]


class DocumentProfile(BaseModel):
    """
    Profile of a document created by the Scout agent.
    
    Contains analysis results including structure, content preview,
    and extracted metadata.
    """
    
    document_id: str
    document_type: DocumentType
    metadata: DocumentMetadata
    structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document structure information (sections, headings, etc.)"
    )
    content_preview: str = Field(
        default="",
        description="Preview of document content (first N characters)"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical information about the document"
    )
    detected_language: Optional[str] = None
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quality score from 0 to 1"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Auto-generated tags for the document"
    )
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_summary(self) -> str:
        """Generate a human-readable summary of the profile."""
        lines = [
            f"Document Profile: {self.document_id}",
            f"Type: {self.document_type.value}",
            f"Language: {self.detected_language or 'Unknown'}",
            f"Quality Score: {self.quality_score:.2f}",
        ]
        
        if self.metadata.title:
            lines.append(f"Title: {self.metadata.title}")
        
        if self.metadata.author:
            lines.append(f"Author: {self.metadata.author}")
        
        if self.metadata.page_count:
            lines.append(f"Pages: {self.metadata.page_count}")
        
        if self.metadata.word_count:
            lines.append(f"Words: {self.metadata.word_count}")
        
        if self.tags:
            lines.append(f"Tags: {', '.join(self.tags)}")
        
        return "\n".join(lines)
