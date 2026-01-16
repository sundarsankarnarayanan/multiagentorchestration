"""
Specialized output models for different agent types.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TransformationType(str, Enum):
    """Types of transformations that Maker can perform."""
    OCR = "ocr"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    CONVERSION = "conversion"


class MakerOutput(BaseModel):
    """Output from the Maker agent."""
    
    transformation_type: TransformationType
    input_document_id: str
    generated_content: Any = Field(description="The generated/transformed content")
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the transformation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the transformation"
    )
    processing_time_ms: float = 0.0
    model_info: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""
    
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    rule: Optional[str] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}]"]
        if self.field:
            parts.append(f"{self.field}:")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"(Suggestion: {self.suggestion})")
        return " ".join(parts)


class ValidationReport(BaseModel):
    """Output from the Checker agent."""
    
    input_id: str = Field(description="ID of the input being validated")
    passed: bool = Field(description="Whether validation passed")
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall quality score"
    )
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues found"
    )
    rules_checked: List[str] = Field(
        default_factory=list,
        description="List of validation rules that were checked"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical information about the validation"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)
    
    def has_errors(self) -> bool:
        """Check if there are any errors or critical issues."""
        return any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in self.issues
        )
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the validation report."""
        lines = [
            f"Validation Report for: {self.input_id}",
            f"Status: {'PASSED' if self.passed else 'FAILED'}",
            f"Quality Score: {self.quality_score:.2f}",
            f"Total Issues: {len(self.issues)}",
        ]
        
        # Count by severity
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        if severity_counts:
            lines.append("\nIssues by Severity:")
            for severity in ValidationSeverity:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    lines.append(f"  {severity.value.upper()}: {count}")
        
        return "\n".join(lines)


class CurationResult(BaseModel):
    """Output from the Curator agent - final workflow result."""
    
    workflow_id: str
    workflow_name: str
    document_id: str
    success: bool
    scout_profile: Optional[Dict[str, Any]] = None
    maker_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    validation_reports: List[Dict[str, Any]] = Field(default_factory=list)
    final_output: Any = Field(description="The final curated output")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated metadata from all agents"
    )
    execution_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of workflow execution"
    )
    total_processing_time_ms: float = 0.0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the curation result."""
        lines = [
            f"Workflow: {self.workflow_name} (ID: {self.workflow_id})",
            f"Document: {self.document_id}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Processing Time: {self.total_processing_time_ms:.2f}ms",
        ]
        
        if self.execution_summary:
            lines.append("\nExecution Summary:")
            for key, value in self.execution_summary.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
