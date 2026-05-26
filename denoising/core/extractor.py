"""Time-series extraction from denoised fMRI data."""

import logging
from pathlib import Path
from typing import Optional

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.maskers import NiftiLabelsMasker

logger = logging.getLogger(__name__)


class TimeSeriesExtractor:
    """Extract time-series from fMRI data using atlas."""

    def __init__(self):
        """Initialize TimeSeriesExtractor."""
        pass

    def extract_timeseries(
        self,
        bold_img: str,
        masker: NiftiLabelsMasker,
        confounds: Optional[np.ndarray] = None,
        sample_mask: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Extract time-series from BOLD image.

        Args:
            bold_img: Path to BOLD NIfTI file.
            masker: Configured NiftiLabelsMasker instance.
            confounds: Confounds matrix (timepoints x confounds).

        Returns:
            DataFrame with time-series (rows=timepoints, columns=regions).
        """
        logger.info(f"Extracting time-series from {bold_img}")

        timeseries = masker.fit_transform(bold_img, 
                                          confounds=confounds,
                                          sample_mask=sample_mask)

        region_names = self._get_region_names(masker)
        df = pd.DataFrame(timeseries, columns=region_names)

        logger.info(f"Extracted time-series shape: {df.shape}")
        return df

    def _get_region_names(self, masker: NiftiLabelsMasker) -> list:
        """Get region names from masker.

        Args:
            masker: NiftiLabelsMasker instance.

        Returns:
            List of region names.
        """
        if hasattr(masker, "labels") and masker.labels is not None:
            return masker.labels[1:] # not include background
        return [f"region_{i}" for i in range(masker.n_elements_)]

    def save_timeseries(
        self,
        timeseries: pd.DataFrame,
        output_path: str,
    ):
        """Save time-series to CSV file.

        Args:
            timeseries: Time-series DataFrame.
            output_path: Output file path.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        timeseries.to_csv(output_path, index=False)
        logger.info(f"Saved time-series to {output_path}")

    def get_output_filename(
        self,
        subject: str,
        session: str,
        task: str,
        run: str,
        atlas_name: str,
        pattern: str = "sub-{subject}_ses-{session}_task-{task}_run-{run}_atlas-{atlas_name}.csv",
    ) -> str:
        """Generate output filename from BIDS entities.

        Args:
            subject: Subject ID.
            session: Session ID.
            task: Task name.
            run: Run number.
            atlas_name: Atlas name.
            pattern: Naming pattern with placeholders.

        Returns:
            Formatted filename.
        """
        return pattern.format(
            subject=subject,
            session=session,
            task=task,
            run=run,
            atlas_name=atlas_name,
        )