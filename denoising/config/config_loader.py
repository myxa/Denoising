"""Configuration loading and validation utilities."""

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import ValidationError

from denoising.config.schemas import PipelineConfig


def load_config(config_path: str) -> PipelineConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Validated PipelineConfig object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config validation fails.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r") as f:
        config_dict = yaml.safe_load(f)

    try:
        return PipelineConfig(**config_dict)
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")


def setup_logging(config: Optional[PipelineConfig] = None, log_file: Optional[str] = None):
    """Setup logging configuration.

    Args:
        config: PipelineConfig with logging settings.
        log_file: Override log file path.
    """
    if config:
        level = config.logging.level
        log_file = log_file or config.logging.file
    else:
        level = "INFO"
        log_file = "./logs/denoising.log"

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )