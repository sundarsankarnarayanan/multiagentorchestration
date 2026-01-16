"""
Checker Agent - Validation and quality control.

The Checker agent is responsible for:
- Validating Maker outputs
- Checking quality and correctness
- Identifying issues and errors
- Providing validation reports
"""

from typing import Any, Dict, List, Optional, Callable
import asyncio

from .base import Agent, AgentOutput, AgentStatus, AgentCapability
from models.agent_output import (
    MakerOutput,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity
)


class ValidationRule:
    """Represents a validation rule."""
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[Any], bool],
        severity: ValidationSeverity,
        message: str,
        suggestion: Optional[str] = None
    ):
        self.name = name
        self.check_func = check_func
        self.severity = severity
        self.message = message
        self.suggestion = suggestion
    
    def validate(self, data: Any) -> Optional[ValidationIssue]:
        """
        Run the validation rule.
        
        Returns:
            ValidationIssue if rule fails, None if passes
        """
        try:
            if not self.check_func(data):
                return ValidationIssue(
                    severity=self.severity,
                    message=self.message,
                    rule=self.name,
                    suggestion=self.suggestion
                )
        except Exception as e:
            return ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Rule '{self.name}' failed with error: {str(e)}",
                rule=self.name
            )
        
        return None


class CheckerAgent(Agent):
    """
    Checker agent for validation and quality control.
    
    This agent validates outputs from Maker agents and ensures
    quality standards are met.
    """
    
    def __init__(self, name: str = "checker", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Checker agent.
        
        Args:
            name: Name of this agent instance
            config: Configuration options:
                - min_quality_score: Minimum acceptable quality score (0-1)
                - strict_mode: Whether to fail on warnings (default: False)
                - custom_rules: List of custom validation rules
        """
        super().__init__(name, config)
        self.min_quality_score = self.config.get("min_quality_score", 0.5)
        self.strict_mode = self.config.get("strict_mode", False)
        self.rules = self._initialize_rules()
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        # Checker can accept various input types
        if input_data is None:
            self.logger.error("Input data is None")
            return False
        return True
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Checker agent capabilities."""
        return [AgentCapability.VALIDATION]
    
    def _initialize_rules(self) -> List[ValidationRule]:
        """Initialize default validation rules."""
        rules = []
        
        # Rule: Content should not be empty
        rules.append(ValidationRule(
            name="non_empty_content",
            check_func=lambda data: self._has_content(data),
            severity=ValidationSeverity.ERROR,
            message="Content is empty or missing",
            suggestion="Ensure the maker agent generates non-empty content"
        ))
        
        # Rule: Content should not be too short
        rules.append(ValidationRule(
            name="minimum_length",
            check_func=lambda data: self._check_minimum_length(data, 10),
            severity=ValidationSeverity.WARNING,
            message="Content is very short (less than 10 characters)",
            suggestion="Consider generating more detailed content"
        ))
        
        # Rule: Confidence score should be reasonable
        rules.append(ValidationRule(
            name="confidence_score",
            check_func=lambda data: self._check_confidence(data),
            severity=ValidationSeverity.WARNING,
            message="Confidence score is below threshold",
            suggestion="Review the maker agent's output quality"
        ))
        
        # Add custom rules from config
        custom_rules = self.config.get("custom_rules", [])
        rules.extend(custom_rules)
        
        return rules
    
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute validation checks.
        
        Args:
            input_data: Data to validate (typically MakerOutput or dict)
            context: Optional workflow context
        
        Returns:
            AgentOutput containing ValidationReport
        """
        self.logger.info("Starting validation checks")
        
        try:
            # Extract input ID
            input_id = self._extract_input_id(input_data)
            
            # Run all validation rules
            issues = await self._run_validation_rules(input_data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(input_data, issues)
            
            # Determine if validation passed
            passed = self._determine_pass_status(issues, quality_score)
            
            # Collect statistics
            statistics = self._collect_statistics(input_data, issues)
            
            # Create validation report
            report = ValidationReport(
                input_id=input_id,
                passed=passed,
                quality_score=quality_score,
                issues=issues,
                rules_checked=[rule.name for rule in self.rules],
                statistics=statistics
            )
            
            self.logger.info(
                f"Validation {'PASSED' if passed else 'FAILED'} "
                f"with {len(issues)} issues (Quality: {quality_score:.2f})"
            )
            
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=report,
                metadata={
                    "passed": passed,
                    "issue_count": len(issues),
                    "quality_score": quality_score,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return AgentOutput(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def _extract_input_id(self, input_data: Any) -> str:
        """Extract an identifier from input data."""
        if isinstance(input_data, MakerOutput):
            return input_data.input_document_id
        elif isinstance(input_data, dict):
            return input_data.get("id", input_data.get("document_id", "unknown"))
        return "unknown"
    
    async def _run_validation_rules(self, input_data: Any) -> List[ValidationIssue]:
        """Run all validation rules and collect issues."""
        issues = []
        
        for rule in self.rules:
            self.logger.debug(f"Running rule: {rule.name}")
            issue = rule.validate(input_data)
            if issue:
                issues.append(issue)
                self.logger.debug(f"Rule '{rule.name}' failed: {issue.message}")
        
        return issues
    
    def _calculate_quality_score(
        self,
        input_data: Any,
        issues: List[ValidationIssue]
    ) -> float:
        """
        Calculate overall quality score.
        
        Score is based on:
        - Number and severity of issues
        - Input data characteristics
        - Confidence scores if available
        """
        base_score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                base_score -= 0.3
            elif issue.severity == ValidationSeverity.ERROR:
                base_score -= 0.2
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 0.05
        
        # Consider input confidence if available
        if isinstance(input_data, MakerOutput):
            confidence = input_data.confidence_score
            base_score = (base_score + confidence) / 2
        
        return max(0.0, min(1.0, base_score))
    
    def _determine_pass_status(
        self,
        issues: List[ValidationIssue],
        quality_score: float
    ) -> bool:
        """Determine if validation passed."""
        # Fail if there are critical issues
        if any(issue.severity == ValidationSeverity.CRITICAL for issue in issues):
            return False
        
        # Fail if there are errors
        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return False
        
        # In strict mode, fail on warnings
        if self.strict_mode and any(
            issue.severity == ValidationSeverity.WARNING for issue in issues
        ):
            return False
        
        # Check quality score threshold
        if quality_score < self.min_quality_score:
            return False
        
        return True
    
    def _collect_statistics(
        self,
        input_data: Any,
        issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """Collect statistics about the validation."""
        stats = {
            "total_rules": len(self.rules),
            "total_issues": len(issues),
            "issues_by_severity": {},
        }
        
        # Count issues by severity
        for severity in ValidationSeverity:
            count = sum(1 for issue in issues if issue.severity == severity)
            stats["issues_by_severity"][severity.value] = count
        
        # Add input-specific stats
        if isinstance(input_data, MakerOutput):
            stats["input_confidence"] = input_data.confidence_score
            stats["processing_time_ms"] = input_data.processing_time_ms
        
        return stats
    
    # Helper methods for validation rules
    
    def _has_content(self, data: Any) -> bool:
        """Check if data has non-empty content."""
        if isinstance(data, MakerOutput):
            content = data.generated_content
        elif isinstance(data, dict):
            content = data.get("content", data.get("generated_content"))
        else:
            content = data
        
        if content is None:
            return False
        
        if isinstance(content, str):
            return len(content.strip()) > 0
        
        return True
    
    def _check_minimum_length(self, data: Any, min_length: int) -> bool:
        """Check if content meets minimum length."""
        if isinstance(data, MakerOutput):
            content = data.generated_content
        elif isinstance(data, dict):
            content = data.get("content", data.get("generated_content", ""))
        else:
            content = str(data)
        
        if isinstance(content, str):
            return len(content) >= min_length
        
        return True
    
    def _check_confidence(self, data: Any) -> bool:
        """Check if confidence score is acceptable."""
        if isinstance(data, MakerOutput):
            return data.confidence_score >= self.min_quality_score
        
        return True
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule."""
        self.rules.append(rule)
        self.logger.info(f"Added validation rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a validation rule by name."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        removed = len(self.rules) < initial_count
        
        if removed:
            self.logger.info(f"Removed validation rule: {rule_name}")
        
        return removed
