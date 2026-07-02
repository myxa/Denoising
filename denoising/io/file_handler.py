"""File I/O operations for BOLD and output files."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import nibabel as nib

logger = logging.getLogger(__name__)


class BIDSFileLoader:
    """Load BIDS files using pybids BIDSLayout."""

    def __init__(self, bids_path: str):
        """Initialize BIDSFileLoader.

        Args:
            bids_path: Path to BIDS dataset root.
        """
        try:
            from bids import BIDSLayout
        except ImportError:
            raise ImportError(
                "pybids is required for BIDS mode. Install it with: pip install pybids"
            )
        
        self.layout = BIDSLayout(bids_path, validate=False, config=['bids', 'derivatives'])
        logger.info(f"Initialized BIDSLayout for: {bids_path}")

    def get_subject_img(
        self,
        subject: str,
        datatype: str = "func", # always
        extension: str = "nii.gz", # always
        desc: str = "preproc", # always preproc
        task: Optional[str] = None,
        space: Optional[str] = None,
        session: Optional[str] = None,
        
    ) -> List[str]:
        """Get all BOLD image files for a subject matching criteria.

        Args:
            subject: Subject ID (e.g., '01').
            datatype: Data type (default: 'func').
            extension: File extension (default: 'nii.gz').
            desc: Description (default: 'preproc').
            task: Task name (e.g., 'rest', optional).
            space: Space (e.g., 'MNI152NLin2009cAsym', optional).
            session: Session ID (optional).

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
    
    def get_subject_mask(
        self,
        subject: str,
        datatype: str = "func", # always
        extension: str = "nii.gz", # always
        desc: str = "brain", # always
        task: Optional[str] = None,
        space: Optional[str] = None,
        session: Optional[str] = None,
    ) -> List[str]:
        """Get all mask files for a subject matching criteria.

        Args:
            subject: Subject ID (e.g., '01').
            datatype: Data type (default: 'func').
            extension: File extension (default: 'nii.gz').
            desc: Description (default: 'brain').
            task: Task name (e.g., 'rest', optional).
            space: Space (e.g., 'MNI152NLin2009cAsym', optional).
            session: Session ID (optional).

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