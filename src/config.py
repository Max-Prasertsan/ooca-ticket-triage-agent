"""
Configuration Management Module
================================

Centralized configuration using environment variables and Pydantic Settings.
Follows the 12-Factor App methodology for configuration management.

Environment Variables:
    OPENAI_API_KEY: Required. Your OpenAI API key.
    OPENAI_MODEL: Optional. Model to use (default: gpt-4o).
    OPENAI_TEMPERATURE: Optional. Model temperature (default: 0.1).
    LOG_LEVEL: Optional. Logging verbosity (default: INFO).
    MAX_RETRIES: Optional. API retry attempts (default: 3).
"""

import logging
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    Attributes:
        openai_api_key: OpenAI API key for authentication.
        openai_model: The OpenAI model to use for triage.
        openai_temperature: Temperature setting for model responses.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_retries: Maximum number of API retry attempts.
        timeout_seconds: Request timeout in seconds.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for authentication"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use for triage"
    )
    openai_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for model responses (lower = more deterministic)"
    )
    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity level"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum API retry attempts"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Request timeout in seconds"
    )
    
    # Feature Flags
    enable_knowledge_base: bool = Field(
        default=True,
        description="Enable knowledge base search tool"
    )
    enable_customer_history: bool = Field(
        default=True,
        description="Enable customer history tool"
    )
    enable_region_status: bool = Field(
        default=True,
        description="Enable region status tool"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return upper_v
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format (basic check)."""
        if v and not v.startswith("sk-"):
            # Allow empty for testing, but warn if format looks wrong
            logging.warning("OpenAI API key format may be incorrect")
        return v
    
    def is_api_key_set(self) -> bool:
        """Check if a valid API key is configured."""
        return bool(self.openai_api_key and len(self.openai_api_key) > 10)


@lru_cache()
def get_config() -> Config:
    """
    Get cached configuration instance.
    
    Returns:
        Config: Application configuration singleton.
    
    Example:
        >>> config = get_config()
        >>> print(config.openai_model)
        'gpt-4o'
    """
    return Config()


def setup_logging(config: Optional[Config] = None) -> logging.Logger:
    """
    Configure application logging based on config settings.
    
    Args:
        config: Optional configuration instance. Uses default if not provided.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    if config is None:
        config = get_config()
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    logger = logging.getLogger("triage_agent")
    logger.setLevel(getattr(logging, config.log_level))
    
    return logger