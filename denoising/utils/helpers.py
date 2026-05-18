"""Helper functions for the denoising pipeline."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_output_directory(path: str):
    """Create output directory if it doesn't exist.

    Args:
        path: Directory path to create.
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {path}")


def validate_file_exists(file_path: str) -> bool:
    """Check if file exists.

    Args:
        file_path: Path to check.

    Returns:
        True if file exists.

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return True


def log_progress(message: str):
    """Log progress message.

    Args:
        message: Progress message to log.
    """
    logger.info(message)