"""
Maker Agent - Content generation and transformation.

The Maker agent is responsible for:
- Transforming document content
- Generating summaries
- Extracting specific information
- Converting between formats
"""

from typing import Any, Dict, List, Optional
import asyncio
import time
from pathlib import Path
import logging

from .base import Agent, AgentOutput, AgentStatus, AgentCapability
from models.document import Document, DocumentProfile, DocumentType
from models.agent_output import MakerOutput, TransformationType
from config import get_config, validate_ocr_config

# OCR imports (will be optional - gracefully handle if not installed)
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR libraries not available. Install pytesseract, pdf2image, opencv-python, and Pillow for OCR support.")

# AI API imports (optional)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class MakerAgent(Agent):
    """
    Maker agent for content generation and transformation.
    
    This agent takes input from Scout and performs various transformations
    such as summarization, extraction, classification, etc.
    """
    
    def __init__(self, name: str = "maker", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Maker agent.
        
        Args:
            name: Name of this agent instance
            config: Configuration options:
                - transformation_type: Type of transformation to perform
                - max_output_length: Maximum length of generated content
                - model: Model to use for generation (if applicable)
        """
        super().__init__(name, config)
        self.transformation_type = TransformationType(
            self.config.get("transformation_type", "summarization")
        )
        self.max_output_length = self.config.get("max_output_length", 1000)
        self.model = self.config.get("model", "default")
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data.
        
        Accepts either Document or DocumentProfile.
        """
        if not isinstance(input_data, (Document, DocumentProfile, dict)):
            self.logger.error(f"Invalid input type: {type(input_data)}")
            return False
        return True
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Maker agent capabilities."""
        return [
            AgentCapability.CONTENT_GENERATION,
            AgentCapability.SUMMARIZATION,
            AgentCapability.CLASSIFICATION,
        ]
    
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute content transformation.
        
        Args:
            input_data: Document, DocumentProfile, or dict to transform
            context: Optional workflow context
        
        Returns:
            AgentOutput containing MakerOutput
        """
        start_time = time.time()
        
        self.logger.info(
            f"Starting {self.transformation_type.value} transformation"
        )
        
        try:
            # Extract document ID
            doc_id = self._extract_document_id(input_data)
            
            # Perform transformation based on type
            result = await self._perform_transformation(input_data, context)
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Create MakerOutput
            maker_output = MakerOutput(
                transformation_type=self.transformation_type,
                input_document_id=doc_id,
                generated_content=result["content"],
                confidence_score=result.get("confidence", 0.8),
                metadata=result.get("metadata", {}),
                processing_time_ms=processing_time,
                model_info={"model": self.model}
            )
            
            self.logger.info(
                f"Transformation complete in {processing_time:.2f}ms"
            )
            
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=maker_output,
                metadata={
                    "transformation_type": self.transformation_type.value,
                    "processing_time_ms": processing_time,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Transformation failed: {str(e)}")
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                errors=[f"Transformation error: {str(e)}"]
            )
    
    def _extract_document_id(self, input_data: Any) -> str:
        """Extract document ID from input."""
        if isinstance(input_data, Document):
            return input_data.id
        elif isinstance(input_data, DocumentProfile):
            return input_data.document_id
        elif isinstance(input_data, dict):
            return input_data.get("document_id", "unknown")
        return "unknown"
    
    async def _perform_transformation(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform the actual transformation based on type.

        Returns:
            Dict with 'content', 'confidence', and 'metadata'
        """
        self.logger.info(f"Performing transformation type: {self.transformation_type}")
        if self.transformation_type == TransformationType.OCR:
            return await self._perform_ocr(input_data, context)
        elif self.transformation_type == TransformationType.SUMMARIZATION:
            return await self._summarize(input_data, context)
        elif self.transformation_type == TransformationType.EXTRACTION:
            return await self._extract(input_data, context)
        elif self.transformation_type == TransformationType.CLASSIFICATION:
            return await self._classify(input_data, context)
        elif self.transformation_type == TransformationType.TRANSLATION:
            return await self._translate(input_data, context)
        else:
            return await self._generate(input_data, context)
    
    async def _perform_ocr(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform OCR on document images.

        Supports:
        - PDF files (converted to images)
        - Image files (PNG, JPG, TIFF)
        - Preprocesses images for better OCR accuracy
        """
        if not OCR_AVAILABLE:
            return {
                "content": "OCR libraries not installed. Install pytesseract, pdf2image, opencv-python, and Pillow.",
                "confidence": 0.0,
                "metadata": {"error": "OCR libraries missing"}
            }

        try:
            # Get document path
            doc_path = self._get_document_path(input_data)
            if not doc_path or not doc_path.exists():
                return {
                    "content": "",
                    "confidence": 0.0,
                    "metadata": {"error": "Document path not found"}
                }

            # Get OCR configuration
            ocr_config = self.config.get("ocr_config", {})
            language = ocr_config.get("language", "eng")
            preprocess = ocr_config.get("preprocess", True)
            deskew = ocr_config.get("deskew", True)

            # Validate configuration and warn if API keys are missing
            validation_warnings = validate_ocr_config(ocr_config)
            for warning in validation_warnings:
                self.logger.warning(warning)

            # Determine if PDF or image
            doc_type = self._get_document_type(input_data)

            extracted_text_parts = []
            page_confidences = []
            metadata = {
                "language": language,
                "preprocessed": preprocess,
                "deskewed": deskew,
                "pages_processed": 0,
                "method": "tesseract"
            }

            if doc_type == DocumentType.PDF:
                # Convert PDF to images
                self.logger.info(f"Converting PDF to images: {doc_path}")
                try:
                    images = pdf2image.convert_from_path(str(doc_path))
                    metadata["pages_processed"] = len(images)

                    for i, image in enumerate(images):
                        self.logger.info(f"Processing page {i+1}/{len(images)}")
                        page_text, page_conf = await self._ocr_image(
                            image, language, preprocess, deskew
                        )
                        extracted_text_parts.append(f"\n--- Page {i+1} ---\n{page_text}")
                        page_confidences.append(page_conf)

                except Exception as e:
                    self.logger.error(f"PDF conversion failed: {e}")
                    return {
                        "content": "",
                        "confidence": 0.0,
                        "metadata": {"error": f"PDF conversion failed: {str(e)}"}
                    }

            else:
                # Process as image
                self.logger.info(f"Processing image: {doc_path}")
                try:
                    image = Image.open(doc_path)
                    metadata["pages_processed"] = 1

                    page_text, page_conf = await self._ocr_image(
                        image, language, preprocess, deskew
                    )
                    extracted_text_parts.append(page_text)
                    page_confidences.append(page_conf)

                except Exception as e:
                    self.logger.error(f"Image loading failed: {e}")
                    return {
                        "content": "",
                        "confidence": 0.0,
                        "metadata": {"error": f"Image loading failed: {str(e)}"}
                    }

            # Combine results
            full_text = "\n".join(extracted_text_parts)
            avg_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0

            metadata["average_confidence"] = avg_confidence
            metadata["total_characters"] = len(full_text)
            metadata["total_words"] = len(full_text.split())

            # Apply AI post-processing if enabled and available
            ai_postprocess = ocr_config.get("ai_postprocess", False)
            if ai_postprocess and full_text:
                self.logger.info("Applying AI post-processing to OCR output")
                processed_result = await self._ai_postprocess_ocr(full_text, metadata)
                if processed_result["success"]:
                    full_text = processed_result["content"]
                    metadata["ai_postprocessed"] = True
                    metadata["ai_model"] = processed_result.get("model", "unknown")
                    # Increase confidence if AI processing succeeded
                    avg_confidence = min(1.0, avg_confidence + 0.1)

            return {
                "content": full_text,
                "confidence": avg_confidence,
                "metadata": metadata
            }

        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return {
                "content": "",
                "confidence": 0.0,
                "metadata": {"error": f"OCR processing failed: {str(e)}"}
            }

    async def _ocr_image(
        self,
        image: Image.Image,
        language: str = "eng",
        preprocess: bool = True,
        deskew: bool = True
    ) -> tuple[str, float]:
        """
        Perform OCR on a single image with preprocessing.

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Convert PIL image to numpy array for OpenCV processing
            if preprocess:
                img_array = np.array(image)

                # Convert to grayscale if needed
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

                # Apply preprocessing
                # 1. Noise removal
                img_array = cv2.fastNlMeansDenoising(img_array, h=10)

                # 2. Thresholding (adaptive)
                img_array = cv2.adaptiveThreshold(
                    img_array, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )

                # 3. Deskew if enabled
                if deskew:
                    img_array = self._deskew_image(img_array)

                # Convert back to PIL Image
                image = Image.fromarray(img_array)

            # Perform OCR with detailed output
            ocr_data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(image, lang=language)

            # Calculate average confidence
            confidences = [
                int(conf) for conf in ocr_data['conf']
                if conf != '-1' and str(conf).isdigit()
            ]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            avg_conf = avg_conf / 100.0  # Normalize to 0-1

            return text.strip(), avg_conf

        except Exception as e:
            self.logger.error(f"Image OCR failed: {e}")
            return "", 0.0

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew an image by detecting and correcting rotation.
        """
        try:
            # Calculate skew angle
            coords = np.column_stack(np.where(image > 0))
            angle = cv2.minAreaRect(coords)[-1]

            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            # Rotate image to deskew
            if abs(angle) > 0.5:  # Only deskew if angle is significant
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                image = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

            return image
        except:
            return image

    def _get_document_path(self, input_data: Any) -> Optional[Path]:
        """Extract document file path from input."""
        if isinstance(input_data, Document):
            return input_data.file_path
        elif isinstance(input_data, DocumentProfile):
            # Need to get path from context or original document
            return None
        elif isinstance(input_data, dict):
            path_str = input_data.get("file_path")
            if path_str:
                return Path(path_str)
        return None

    def _get_document_type(self, input_data: Any) -> DocumentType:
        """Extract document type from input."""
        if isinstance(input_data, Document):
            return input_data.document_type
        elif isinstance(input_data, DocumentProfile):
            return input_data.document_type
        elif isinstance(input_data, dict):
            type_str = input_data.get("document_type", "unknown")
            try:
                return DocumentType(type_str)
            except:
                return DocumentType.UNKNOWN
        return DocumentType.UNKNOWN

    async def _summarize(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary of the document.
        
        This is a simplified implementation. In production, you would use
        an LLM or specialized summarization model.
        """
        # Get content
        content = self._get_content(input_data)
        
        if not content:
            return {
                "content": "No content available to summarize.",
                "confidence": 0.0,
                "metadata": {"method": "none"}
            }
        
        # If content is short enough, return it as is (or truncated to max length)
        # This fixes issues with very short documents or single-sentence inputs
        if len(content) <= self.max_output_length:
             return {
                "content": content,
                "confidence": 1.0,
                "metadata": {
                    "method": "identity",
                    "original_length": len(content),
                    "summary_length": len(content),
                    "compression_ratio": 1.0
                }
            }

        # Simple extractive summary
        # In production, use proper summarization
        summary_length = self.max_output_length
        
        # Try to split by sentences
        sentences = content.split('. ')
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            # If a single sentence is too long, we might need to truncate it
            if current_length + len(sentence) > summary_length:
                # If we haven't added any sentences yet, we must truncate this one
                if not summary_sentences:
                    summary_sentences.append(sentence[:summary_length])
                    current_length += summary_length
                break
            
            summary_sentences.append(sentence)
            current_length += len(sentence)
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.') and len(summary) < len(content):
            summary += '.'
            
        return {
            "content": summary,
            "confidence": 0.7,
            "metadata": {
                "method": "extractive",
                "original_length": len(content),
                "summary_length": len(summary),
                "compression_ratio": len(summary) / len(content) if content else 0
            }
        }
    
    async def _extract(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract specific information from the document.
        
        This could extract entities, key phrases, dates, etc.
        """
        content = self._get_content(input_data)
        
        # Simple extraction - in production use NER or similar
        extracted = {
            "key_phrases": [],
            "entities": [],
            "dates": [],
        }
        
        if content:
            # Extract capitalized phrases as potential entities
            words = content.split()
            entities = [word for word in words if word and word[0].isupper()]
            extracted["entities"] = list(set(entities))[:10]
        
        return {
            "content": extracted,
            "confidence": 0.6,
            "metadata": {"method": "simple_extraction"}
        }
    
    async def _classify(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify the document into categories.
        """
        content = self._get_content(input_data)
        
        # Simple keyword-based classification
        categories = []
        confidence_scores = {}
        
        if content:
            content_lower = content.lower()
            
            # Define simple rules
            if any(word in content_lower for word in ["report", "analysis", "findings"]):
                categories.append("report")
                confidence_scores["report"] = 0.8
            
            if any(word in content_lower for word in ["invoice", "payment", "total"]):
                categories.append("financial")
                confidence_scores["financial"] = 0.7
            
            if any(word in content_lower for word in ["contract", "agreement", "terms"]):
                categories.append("legal")
                confidence_scores["legal"] = 0.75
        
        if not categories:
            categories = ["general"]
            confidence_scores["general"] = 0.5
        
        return {
            "content": {
                "categories": categories,
                "confidence_scores": confidence_scores,
                "primary_category": categories[0] if categories else "unknown"
            },
            "confidence": max(confidence_scores.values()) if confidence_scores else 0.5,
            "metadata": {"method": "keyword_based"}
        }
    
    async def _translate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Translate document content.
        
        This is a placeholder. In production, use a translation API.
        """
        content = self._get_content(input_data)
        
        return {
            "content": f"[Translation placeholder for: {content[:100]}...]",
            "confidence": 0.0,
            "metadata": {
                "method": "placeholder",
                "note": "Translation not implemented"
            }
        }
    
    async def _generate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate new content based on input.
        """
        content = self._get_content(input_data)
        
        return {
            "content": f"Generated content based on input of length {len(content)}",
            "confidence": 0.5,
            "metadata": {"method": "generation"}
        }
    
    async def _ai_postprocess_ocr(self, ocr_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to post-process and clean up OCR output.

        This can:
        - Fix common OCR errors
        - Correct spelling and grammar
        - Improve formatting
        - Restore proper punctuation

        Returns:
            Dict with 'success', 'content', and 'model' keys
        """
        ai_provider = self.config.get("ocr_config", {}).get("ai_provider", "anthropic")

        try:
            if ai_provider == "anthropic" and ANTHROPIC_AVAILABLE:
                return await self._anthropic_postprocess(ocr_text)
            elif ai_provider == "openai" and OPENAI_AVAILABLE:
                return await self._openai_postprocess(ocr_text)
            else:
                self.logger.warning(f"AI provider '{ai_provider}' not available")
                return {"success": False, "content": ocr_text}
        except Exception as e:
            self.logger.error(f"AI post-processing failed: {e}")
            return {"success": False, "content": ocr_text}

    async def _anthropic_postprocess(self, ocr_text: str) -> Dict[str, Any]:
        """Post-process OCR text using Anthropic Claude."""
        try:
            # Get API key from global config (loaded from environment)
            api_key = get_config().credentials.anthropic_api_key
            if not api_key:
                self.logger.warning("Anthropic API key not configured")
                return {"success": False, "content": ocr_text}

            client = anthropic.Anthropic(api_key=api_key)

            prompt = f"""You are an OCR post-processing assistant. The following text was extracted from a document using OCR and may contain errors. Please:

1. Fix obvious OCR errors (character confusion like 'l' vs '1', 'O' vs '0')
2. Correct spelling mistakes
3. Fix punctuation and spacing issues
4. Preserve the original formatting and structure
5. Do NOT add any commentary or explanations
6. Return ONLY the corrected text

OCR Text:
{ocr_text}

Corrected Text:"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            corrected_text = message.content[0].text.strip()

            return {
                "success": True,
                "content": corrected_text,
                "model": "claude-3-5-sonnet-20241022"
            }

        except Exception as e:
            self.logger.error(f"Anthropic post-processing failed: {e}")
            return {"success": False, "content": ocr_text}

    async def _openai_postprocess(self, ocr_text: str) -> Dict[str, Any]:
        """Post-process OCR text using OpenAI."""
        try:
            # Get API key from global config (loaded from environment)
            api_key = get_config().credentials.openai_api_key
            if not api_key:
                self.logger.warning("OpenAI API key not configured")
                return {"success": False, "content": ocr_text}

            client = openai.OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an OCR post-processing assistant. Fix OCR errors, spelling mistakes, and formatting issues while preserving the original structure. Return only the corrected text without commentary."
                    },
                    {
                        "role": "user",
                        "content": f"Correct the following OCR text:\n\n{ocr_text}"
                    }
                ],
                max_tokens=4096,
                temperature=0.3
            )

            corrected_text = response.choices[0].message.content.strip()

            return {
                "success": True,
                "content": corrected_text,
                "model": "gpt-4o-mini"
            }

        except Exception as e:
            self.logger.error(f"OpenAI post-processing failed: {e}")
            return {"success": False, "content": ocr_text}

    def _get_content(self, input_data: Any) -> str:
        """Extract text content from various input types."""
        if isinstance(input_data, Document):
            if input_data.content:
                return input_data.content
            elif input_data.is_text_based():
                try:
                    return input_data.file_path.read_text(encoding='utf-8')
                except:
                    return ""
        
        elif isinstance(input_data, DocumentProfile):
            return input_data.content_preview
        
        elif isinstance(input_data, dict):
            # Try to get content from dict
            return input_data.get("content", input_data.get("content_preview", ""))
        
        return ""
