"""File I/O operations for BOLD and output files."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
import bids

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


class BIDSFileLoader:
    """Load BIDS files using pybids BIDSLayout."""

    def __init__(self, bids_path: str):
        """Initialize BIDSFileLoader.

        Args:
            bids_path: Path to BIDS dataset root.
            validate: Whether to validate BIDS dataset.
        """
        try:
            from bids import BIDSLayout
        except ImportError:
            raise ImportError(
                "pybids is required for BIDS mode. Install it with: pip install pybids"
            )
        
        self.layout = BIDSLayout(bids_path, validate=False, config=['bids', 'derivatives'])
        logger.info(f"Initialized BIDSLayout for: {bids_path}")

    def get_subject_files(
        self,
        subject: str,
        task: Optional[str] = None,
        space: Optional[str] = None,
        desc: Optional[str] = None,
        session: Optional[str] = None,
        datatype: str = "func",
        extension: str = "nii.gz",
    ) -> List[str]:
        """Get all BOLD files for a subject matching criteria.

        Args:
            subject: Subject ID (e.g., '01').
            task: Task name (e.g., 'rest').
            space: Space (e.g., 'MNI152NLin2009cAsym').
            desc: Description (e.g., 'preproc').
            session: Session ID (optional).
            datatype: Data type (default: 'func').
            extension: File extension (default: 'nii.gz').

        Returns:
            List of file paths matching the criteria.
        """
        filters = {
            'subject': subject,
            'datatype': datatype,
            'extension': extension,
        }
        
        if task is not None:
            filters['task'] = task
        if space is not None:
            filters['space'] = space
        if desc is not None:
            filters['desc'] = desc
        if session is not None:
            filters['session'] = session

        files = self.layout.get(return_type='file', **filters)
        logger.info(f"Found {len(files)} files for subject {subject} with filters: {filters}")
        
        return files
    
    def get_subject_mask_files(
        self,
        subject: str,
        task: Optional[str] = None,
        space: Optional[str] = None,
        desc: Optional[str] = None,
        session: Optional[str] = None,
        datatype: str = "mask",
        extension: str = "nii.gz",
    ) -> List[str]:
        """Get all BOLD files for a subject matching criteria.

        Args:
            subject: Subject ID (e.g., '01').
            task: Task name (e.g., 'rest').
            space: Space (e.g., 'MNI152NLin2009cAsym').
            desc: Description (e.g., 'preproc').
            session: Session ID (optional).
            datatype: Data type (default: 'func').
            extension: File extension (default: 'nii.gz').

        Returns:
            List of file paths matching the criteria.
        """
        filters = {
            'subject': subject,
            'datatype': datatype,
            'extension': extension,
        }
        
        if task is not None:
            filters['task'] = task
        if space is not None:
            filters['space'] = space
        if desc is not None:
            filters['desc'] = desc
        if session is not None:
            filters['session'] = session

        files = self.layout.get(return_type='file', **filters)
        logger.info(f"Found {len(files)} files for subject {subject} with filters: {filters}")
        
        return files

    def get_all_subjects(self) -> List[str]:
        """Get list of all subjects in dataset.

        Returns:
            List of subject IDs.
        """
        subjects = self.layout.get_subjects()
        logger.info(f"Found {len(subjects)} subjects in dataset")
        return subjects

    def get_bids_entities(self, file_path: str) -> Dict[str, str]:
        """Get BIDS entities for a file using the layout.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary of BIDS entities.
        """
        entities = self.layout.parse_file_entities(file_path)
        return entities
