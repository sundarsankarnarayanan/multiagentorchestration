"""
Scout Agent - Document discovery and initial analysis.

The Scout agent is responsible for:
- Analyzing document structure and content
- Extracting metadata
- Creating document profiles
- Identifying document characteristics
"""

from typing import Any, Dict, List, Optional
import asyncio
from pathlib import Path
import logging

from .base import Agent, AgentOutput, AgentStatus, AgentCapability
from models.document import Document, DocumentProfile, DocumentMetadata, DocumentType

# Image processing imports (optional)
try:
    from PIL import Image
    import cv2
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    logging.warning("Image processing libraries not available. Install Pillow and opencv-python for image analysis.")


class ScoutAgent(Agent):
    """
    Scout agent for document discovery and analysis.
    
    This agent examines documents and creates comprehensive profiles
    including metadata, structure, and content characteristics.
    """
    
    def __init__(self, name: str = "scout", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Scout agent.
        
        Args:
            name: Name of this agent instance
            config: Configuration options:
                - preview_length: Number of characters for content preview (default: 500)
                - extract_metadata: Whether to extract document metadata (default: True)
                - analyze_structure: Whether to analyze document structure (default: True)
        """
        super().__init__(name, config)
        self.preview_length = self.config.get("preview_length", 500)
        self.extract_metadata = self.config.get("extract_metadata", True)
        self.analyze_structure = self.config.get("analyze_structure", True)
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate that input is a Document object.
        
        Args:
            input_data: Input to validate
        
        Returns:
            True if valid Document, False otherwise
        """
        if not isinstance(input_data, Document):
            self.logger.error(f"Invalid input type: {type(input_data)}. Expected Document.")
            return False
        
        if not input_data.file_path.exists():
            self.logger.error(f"Document file does not exist: {input_data.file_path}")
            return False
        
        return True
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Scout agent capabilities."""
        return [
            AgentCapability.DOCUMENT_ANALYSIS,
            AgentCapability.TEXT_EXTRACTION,
        ]
    
    async def execute(self, input_data: Document, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """
        Execute document analysis.
        
        Args:
            input_data: Document to analyze
            context: Optional context from workflow
        
        Returns:
            AgentOutput containing DocumentProfile
        """
        self.logger.info(f"Analyzing document: {input_data.get_filename()}")
        
        try:
            # Create document profile
            profile = await self._analyze_document(input_data)
            
            self.logger.info(f"Analysis complete. Quality score: {profile.quality_score:.2f}")
            
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=profile,
                metadata={
                    "document_type": input_data.document_type.value,
                    "file_size": input_data.size_bytes,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                errors=[f"Analysis error: {str(e)}"]
            )
    
    async def _analyze_document(self, document: Document) -> DocumentProfile:
        """
        Perform comprehensive document analysis.
        
        Args:
            document: Document to analyze
        
        Returns:
            DocumentProfile with analysis results
        """
        # Extract metadata if enabled
        metadata = DocumentMetadata()
        if self.extract_metadata:
            metadata = await self._extract_metadata(document)
        
        # Get content preview
        content_preview = await self._get_content_preview(document)
        
        # Analyze structure if enabled
        structure = {}
        if self.analyze_structure:
            structure = await self._analyze_structure(document)
        
        # Calculate statistics
        statistics = await self._calculate_statistics(document)
        
        # Detect language (simplified - in production use langdetect or similar)
        detected_language = self._detect_language(content_preview)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(document, metadata, statistics)
        
        # Generate tags
        tags = self._generate_tags(document, metadata, content_preview)
        
        return DocumentProfile(
            document_id=document.id,
            document_type=document.document_type,
            metadata=metadata,
            structure=structure,
            content_preview=content_preview,
            statistics=statistics,
            detected_language=detected_language,
            quality_score=quality_score,
            tags=tags
        )
    
    async def _extract_metadata(self, document: Document) -> DocumentMetadata:
        """Extract metadata from document."""
        metadata = DocumentMetadata()
        
        # For text-based documents, try to extract basic metadata
        if document.is_text_based() and document.content:
            # Simple heuristics - in production, use proper parsers
            lines = document.content.split('\n')
            if lines:
                # First non-empty line might be title
                for line in lines:
                    if line.strip():
                        metadata.title = line.strip()[:100]
                        break
        
        # File-based metadata
        stat = document.file_path.stat()
        metadata.created_date = None  # Would need platform-specific code
        metadata.modified_date = None  # Would use stat.st_mtime
        
        return metadata
    
    async def _get_content_preview(self, document: Document) -> str:
        """Get a preview of document content."""
        if document.content:
            return document.content[:self.preview_length]
        
        # Try to read text content
        if document.is_text_based():
            try:
                content = document.file_path.read_text(encoding='utf-8')
                return content[:self.preview_length]
            except Exception as e:
                self.logger.warning(f"Could not read text content: {e}")
                return ""
        
        return f"[Binary content - {document.document_type.value}]"
    
    async def _analyze_structure(self, document: Document) -> Dict[str, Any]:
        """Analyze document structure."""
        structure = {
            "type": document.document_type.value,
            "sections": [],
            "has_headings": False,
            "has_lists": False,
            "has_tables": False,
        }
        
        # Basic structure analysis for text documents
        if document.content or document.is_text_based():
            content = document.content
            if not content and document.is_text_based():
                try:
                    content = document.file_path.read_text(encoding='utf-8')
                except:
                    content = ""
            
            if content:
                # Simple heuristics
                structure["has_headings"] = any(
                    line.startswith('#') for line in content.split('\n')
                )
                structure["has_lists"] = any(
                    line.strip().startswith(('-', '*', '1.')) 
                    for line in content.split('\n')
                )
        
        return structure
    
    async def _calculate_statistics(self, document: Document) -> Dict[str, Any]:
        """Calculate document statistics."""
        stats = {
            "file_size_bytes": document.size_bytes,
            "file_size_kb": round(document.size_bytes / 1024, 2),
        }

        # Get content for analysis
        content = document.content
        if not content and document.is_text_based():
            try:
                content = document.file_path.read_text(encoding='utf-8')
            except:
                content = ""

        if content:
            stats["character_count"] = len(content)
            stats["word_count"] = len(content.split())
            stats["line_count"] = len(content.split('\n'))
            stats["avg_word_length"] = (
                sum(len(word) for word in content.split()) / len(content.split())
                if content.split() else 0
            )

        # Add image statistics if it's an image document
        if self._is_image_document(document):
            image_stats = await self._analyze_image_properties(document)
            stats.update(image_stats)

        return stats

    def _is_image_document(self, document: Document) -> bool:
        """Check if document is an image or PDF."""
        return document.document_type in [
            DocumentType.PDF,
        ] or document.file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']

    async def _analyze_image_properties(self, document: Document) -> Dict[str, Any]:
        """
        Analyze image properties for OCR suitability.

        Checks:
        - Image dimensions
        - Resolution (DPI if available)
        - Image quality (blur detection, brightness, contrast)
        - Orientation
        """
        if not IMAGE_PROCESSING_AVAILABLE:
            return {"image_analysis": "unavailable"}

        try:
            # For PDFs, analyze first page
            if document.document_type == DocumentType.PDF:
                try:
                    import pdf2image
                    images = pdf2image.convert_from_path(str(document.file_path), first_page=1, last_page=1)
                    if images:
                        image = images[0]
                    else:
                        return {"image_analysis": "pdf_conversion_failed"}
                except:
                    return {"image_analysis": "pdf_conversion_unavailable"}
            else:
                image = Image.open(document.file_path)

            # Get basic properties
            width, height = image.size
            stats = {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                "megapixels": round(width * height / 1000000, 2),
            }

            # Get DPI if available
            if hasattr(image, 'info') and 'dpi' in image.info:
                stats["dpi"] = image.info['dpi']

            # Convert to numpy for advanced analysis
            img_array = np.array(image)

            # Convert to grayscale for analysis
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Blur detection (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            stats["sharpness"] = round(laplacian_var, 2)
            stats["is_blurry"] = laplacian_var < 100  # Threshold for blur

            # Brightness and contrast
            stats["mean_brightness"] = round(float(np.mean(gray)), 2)
            stats["std_brightness"] = round(float(np.std(gray)), 2)
            stats["contrast"] = round(float(np.std(gray)) / float(np.mean(gray)) if np.mean(gray) > 0 else 0, 2)

            # OCR readiness score (simple heuristic)
            ocr_score = 1.0
            if stats["is_blurry"]:
                ocr_score -= 0.3
            if stats["mean_brightness"] < 50 or stats["mean_brightness"] > 200:
                ocr_score -= 0.2
            if stats["contrast"] < 0.3:
                ocr_score -= 0.2
            if width < 800 or height < 600:
                ocr_score -= 0.1

            stats["ocr_readiness_score"] = max(0.0, min(1.0, ocr_score))

            # Recommendations
            recommendations = []
            if stats["is_blurry"]:
                recommendations.append("Image appears blurry - may need sharpening")
            if stats["mean_brightness"] < 100:
                recommendations.append("Image is too dark - increase brightness")
            if stats["mean_brightness"] > 200:
                recommendations.append("Image is too bright - decrease brightness")
            if stats["contrast"] < 0.3:
                recommendations.append("Low contrast - increase contrast for better OCR")
            if width < 800:
                recommendations.append("Low resolution - higher resolution recommended for OCR")

            stats["preprocessing_recommendations"] = recommendations

            return stats

        except Exception as e:
            self.logger.warning(f"Image analysis failed: {e}")
            return {"image_analysis_error": str(e)}
    
    def _detect_language(self, content: str) -> str:
        """
        Detect document language.
        
        This is a simplified version. In production, use langdetect or similar.
        """
        if not content:
            return "unknown"
        
        # Very basic detection - just return English for now
        # In production, use: from langdetect import detect
        return "en"
    
    def _calculate_quality_score(
        self,
        document: Document,
        metadata: DocumentMetadata,
        statistics: Dict[str, Any]
    ) -> float:
        """
        Calculate a quality score for the document.
        
        Score is based on:
        - Presence of metadata
        - Document size
        - Content characteristics
        """
        score = 0.5  # Base score
        
        # Metadata completeness
        if metadata.title:
            score += 0.1
        if metadata.author:
            score += 0.1
        
        # Content quality indicators
        word_count = statistics.get("word_count", 0)
        if word_count > 100:
            score += 0.1
        if word_count > 500:
            score += 0.1
        
        # File size (not too small, not too large)
        size_kb = statistics.get("file_size_kb", 0)
        if 1 < size_kb < 10000:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_tags(
        self,
        document: Document,
        metadata: DocumentMetadata,
        content_preview: str
    ) -> List[str]:
        """Generate tags for the document."""
        tags = []
        
        # Add document type tag
        tags.append(document.document_type.value)
        
        # Add size-based tags
        size_kb = document.size_bytes / 1024
        if size_kb < 100:
            tags.append("small")
        elif size_kb < 1000:
            tags.append("medium")
        else:
            tags.append("large")
        
        # Add content-based tags (simplified)
        if content_preview:
            content_lower = content_preview.lower()
            if any(word in content_lower for word in ["report", "analysis"]):
                tags.append("report")
            if any(word in content_lower for word in ["summary", "overview"]):
                tags.append("summary")
        
        return tags
