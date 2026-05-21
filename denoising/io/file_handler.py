"""File I/O operations for BOLD and output files."""

import logging
import re
from pathlib import Path
from typing import Dict

import nibabel as nib

logger = logging.getLogger(__name__)


def parse_bids_filename(filename: str) -> Dict[str, str]:
    """Parse BIDS filename to extract entities.

    Args:
        filename: BIDS filename (can include path).

    Returns:
        Dictionary with BIDS entities (subject, session, task, run, etc.).
    """
    basename = Path(filename).stem
    entities = {}

    patterns = {
        "subject": r"sub-([A-Za-z0-9]+)",
        "session": r"ses-([A-Za-z0-9]+)",
        "task": r"task-([A-Za-z0-9]+)",
        "run": r"run-([0-9]+)",
        "acq": r"acq-([A-Za-z0-9]+)",
        "space": r"space-([A-Za-z0-9]+)",
        "desc": r"desc-([A-Za-z0-9]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, basename)
        if match:
            entities[key] = match.group(1)

    return entities


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
