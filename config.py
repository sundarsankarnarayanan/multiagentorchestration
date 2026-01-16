"""
Configuration management for the AI agent system.
"""

from typing import Any, Dict, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class AgentConfig(BaseSettings):
    """Configuration for individual agents."""
    
    # Scout configuration
    scout_preview_length: int = Field(default=500, description="Length of content preview")
    scout_extract_metadata: bool = Field(default=True, description="Extract document metadata")
    scout_analyze_structure: bool = Field(default=True, description="Analyze document structure")
    
    # Maker configuration
    maker_transformation_type: str = Field(default="summarization", description="Default transformation type")
    maker_max_output_length: int = Field(default=1000, description="Maximum output length")
    maker_model: str = Field(default="default", description="Model to use for generation")
    
    # Checker configuration
    checker_min_quality_score: float = Field(default=0.5, description="Minimum quality score", ge=0.0, le=1.0)
    checker_strict_mode: bool = Field(default=False, description="Fail on warnings")
    
    # Curator configuration
    curator_retry_on_failure: bool = Field(default=False, description="Retry failed steps")
    curator_max_retries: int = Field(default=3, description="Maximum retries")
    
    class Config:
        env_prefix = "AGENT_"
        case_sensitive = False


class WorkflowConfig(BaseSettings):
    """Configuration for workflow execution."""

    workflow_dir: Path = Field(
        default=Path("workflows/templates"),
        description="Directory containing workflow templates"
    )
    enable_parallel_execution: bool = Field(
        default=False,
        description="Enable parallel agent execution where possible"
    )
    max_workflow_duration_seconds: int = Field(
        default=300,
        description="Maximum workflow execution time"
    )
    save_intermediate_results: bool = Field(
        default=True,
        description="Save intermediate results from each agent"
    )

    class Config:
        env_prefix = "WORKFLOW_"
        case_sensitive = False


class CredentialsConfig(BaseSettings):
    """Configuration for API credentials."""

    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models (set via ANTHROPIC_API_KEY env var)"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models (set via OPENAI_API_KEY env var)"
    )

    class Config:
        env_prefix = ""  # Use direct env var names without prefix
        case_sensitive = True  # API keys are typically uppercase
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_redacted_dict(self) -> Dict[str, str]:
        """Return credentials with redacted values for safe logging."""
        return {
            "anthropic_api_key": self._redact(self.anthropic_api_key),
            "openai_api_key": self._redact(self.openai_api_key)
        }

    @staticmethod
    def _redact(value: Optional[str]) -> str:
        """Redact sensitive values for display."""
        if not value:
            return "not_set"
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"


class SystemConfig(BaseSettings):
    """Main system configuration."""
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Storage
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    output_dir: Path = Field(default=Path("output"), description="Output directory")
    
    # Performance
    max_concurrent_workflows: int = Field(default=5, description="Max concurrent workflows")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    
    # Agent and workflow configs
    agent: AgentConfig = Field(default_factory=AgentConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)

    class Config:
        env_prefix = "SYSTEM_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent type.
        
        Args:
            agent_type: Type of agent (scout, maker, checker, curator)
        
        Returns:
            Configuration dictionary
        """
        prefix = f"{agent_type}_"
        config = {}
        
        for field_name, field_value in self.agent.dict().items():
            if field_name.startswith(prefix):
                config_key = field_name[len(prefix):]
                config[config_key] = field_value
        
        return config
    
    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workflow.workflow_dir.mkdir(parents=True, exist_ok=True)

    def validate_ai_postprocessing(self, provider: str = "anthropic") -> tuple[bool, Optional[str]]:
        """
        Validate that required API keys are available for AI post-processing.

        Args:
            provider: AI provider ('anthropic' or 'openai')

        Returns:
            Tuple of (is_valid, error_message)
        """
        if provider == "anthropic":
            if not self.credentials.anthropic_api_key:
                return False, "AI post-processing requires ANTHROPIC_API_KEY environment variable"
        elif provider == "openai":
            if not self.credentials.openai_api_key:
                return False, "AI post-processing requires OPENAI_API_KEY environment variable"
        else:
            return False, f"Unknown AI provider: {provider}"

        return True, None


# Global configuration instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = SystemConfig()
        _config.ensure_directories()
    return _config


def reload_config() -> SystemConfig:
    """Reload configuration from environment."""
    global _config
    _config = SystemConfig()
    _config.ensure_directories()
    return _config


def validate_ocr_config(ocr_config: Dict[str, Any]) -> list[str]:
    """
    Validate OCR configuration and return warnings if API keys are missing.

    Args:
        ocr_config: OCR configuration dictionary from agent config

    Returns:
        List of warning messages (empty if all OK)
    """
    warnings = []

    # Check if AI post-processing is enabled
    ai_postprocess = ocr_config.get("ai_postprocess", False)
    if not ai_postprocess:
        return warnings

    # Get AI provider
    ai_provider = ocr_config.get("ai_provider", "anthropic")

    # Validate credentials
    config = get_config()
    is_valid, error_msg = config.validate_ai_postprocessing(ai_provider)

    if not is_valid:
        warnings.append(error_msg)
        if ai_provider == "anthropic":
            warnings.append("Set ANTHROPIC_API_KEY in .env file or environment")
        elif ai_provider == "openai":
            warnings.append("Set OPENAI_API_KEY in .env file or environment")

    return warnings
