"""Time-series extraction from denoised fMRI data using atlas."""

import logging
import re
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
from nilearn.maskers import NiftiLabelsMasker

logger = logging.getLogger(__name__)


class SignalExtractor:
    """Configure NiftiLabelsMasker and extract time-series from fMRI data.

    Combines denoising parameter configuration with time-series extraction
    and file output. This replaces the former Denoiser + TimeSeriesExtractor
    split, which had no meaningful separation of concerns.
    """

    def __init__(
        self,
        smoothing_fwhm: float = 6.0,
        detrend: bool = True,
        standardize: Optional[str] = None,
        standardize_confounds: Union[str, bool] = False,
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
    ):
        """Initialize SignalExtractor.

        Args:
            smoothing_fwhm: Full width at half maximum for smoothing (mm).
            detrend: Whether to apply detrending.
            standardize: Standardization method ('zscore', 'psc', or None).
            standardize_confounds: Whether to standardize confounds before regression.
            low_pass: Low pass filter cutoff (Hz).
            high_pass: High pass filter cutoff (Hz).
            t_r: Repetition time (seconds). Required for filtering.
        """
        self.smoothing_fwhm = smoothing_fwhm
        self.detrend = detrend
        self.standardize = standardize
        self.standardize_confounds = standardize_confounds
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r

    # ------------------------------------------------------------------
    # Masker configuration
    # ------------------------------------------------------------------

    def configure_masker(
        self, masker: NiftiLabelsMasker, t_r: Optional[float] = None
    ) -> None:
        """Apply denoising parameters to a NiftiLabelsMasker instance.

        Args:
            masker: A NiftiLabelsMasker instance (already initialised with an atlas).
            t_r: Override repetition time. Falls back to self.t_r if None.
        """
        effective_tr = t_r if t_r is not None else self.t_r

        params = {
            "smoothing_fwhm": self.smoothing_fwhm,
            "detrend": self.detrend,
            "standardize": self.standardize,
            "standardize_confounds": self.standardize_confounds,
            "low_pass": self.low_pass,
            "high_pass": self.high_pass,
        }
        if effective_tr is not None:
            params["t_r"] = effective_tr

        for key, value in params.items():
            setattr(masker, key, value)

    # ------------------------------------------------------------------
    # Time-series extraction
    # ------------------------------------------------------------------

    def extract(
        self,
        bold_img: str,
        masker: NiftiLabelsMasker,
        confounds: Optional[pd.DataFrame] = None,
        sample_mask: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Extract time-series from BOLD image using a configured masker.

        Args:
            bold_img: Path to BOLD NIfTI file.
            masker: Configured NiftiLabelsMasker instance.
            confounds: Confounds DataFrame (timepoints x confounds).
            sample_mask: Boolean array indicating which timepoints to keep.

        Returns:
            DataFrame with time-series (rows=timepoints, columns=regions).
        """
        logger.info(f"Extracting time-series from {bold_img}")

        timeseries = masker.fit_transform(
            bold_img, confounds=confounds, sample_mask=sample_mask
        )

        region_names = self._get_region_names(masker)
        df = pd.DataFrame(timeseries, columns=region_names)

        logger.info(f"Extracted time-series shape: {df.shape}")
        return df

    @staticmethod
    def _get_region_names(masker: NiftiLabelsMasker) -> list:
        """Get region names from masker, skipping background (label 0)."""
        if hasattr(masker, "labels") and masker.labels is not None:
            return masker.labels[1:]  # skip background
        return [f"region_{i}" for i in range(masker.n_elements_)]

    # ------------------------------------------------------------------
    # File output
    # ------------------------------------------------------------------

    @staticmethod
    def save(timeseries: pd.DataFrame, output_path: str) -> None:
        """Save time-series DataFrame to CSV file.

        Args:
            timeseries: Time-series DataFrame.
            output_path: Output file path.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        timeseries.to_csv(output_path, index=False)
        logger.info(f"Saved time-series to {output_path}")

    @staticmethod
    def make_output_filename(
        subject: str,
        session: Optional[str] = None,
        task: Optional[str] = None,
        run: Optional[str] = None,
        atlas_name: str = "atlas",
        n_rois: Optional[int] = None,
        pattern: str = "sub-{subject}_ses-{session}_task-{task}_run-{run}_atlas-{atlas_name}-{n_rois}rois.csv",
    ) -> str:
        """Generate output filename from BIDS entities.

        Placeholders for which the corresponding value is ``None`` are
        removed from the pattern together with any leading separator
        (``_`` or ``-``) and any trailing non-placeholder text that
        belongs to the same BIDS entity suffix.

        This ensures that optional entities (e.g. ``ses-{session}``)
        do not produce dangling ``ses-unknown`` fragments, and that
        compound suffixes like ``-{n_rois}rois`` are fully removed
        when ``n_rois`` is ``None``.

        Args:
            subject: Subject ID (required).
            session: Session ID (optional — omitted from name when ``None``).
            task: Task name (optional — omitted when ``None``).
            run: Run number (optional — omitted when ``None``).
            atlas_name: Atlas name.
            n_rois: Number of ROIs (optional — omitted when ``None``).
            pattern: Naming pattern with placeholders.

        Returns:
            Formatted filename.
        """
        values = {
            "subject": subject,
            "session": session,
            "task": task,
            "run": run,
            "atlas_name": atlas_name,
            "n_rois": n_rois,
        }

        # Remove placeholders whose value is None, together with any
        # leading BIDS entity label (e.g. "ses-", "task-", "run-") and
        # any trailing literal text (e.g. "rois" after "{n_rois}").
        #
        # Examples when session=None:
        #   "_ses-{session}"  ->  ""
        #   "ses-{session}"   ->  ""
        #   "-{n_rois}rois"   ->  ""   (n_rois=None)
        for key, val in values.items():
            if val is None:
                # Pattern 1: "word-{placeholder}suffix" (e.g. "ses-{session}")
                pattern = re.sub(
                    rf"[-_]?[A-Za-z]+-\{{\s*{key}\s*\}}[A-Za-z0-9]*", "", pattern
                )
                # Pattern 2: "-{placeholder}suffix" (e.g. "-{n_rois}rois")
                # Use a helper to avoid f-string brace confusion.
                _pat = r"-?\{" + re.escape(key) + r"\}[A-Za-z0-9]*"
                pattern = re.sub(_pat, "", pattern)

        # Clean up any repeated or dangling separators left behind.
        pattern = re.sub(r"[-_]{2,}", "_", pattern).strip("_-")

        # Build the final format kwargs, keeping only non-None values
        fmt_kwargs = {k: v for k, v in values.items() if v is not None}
        return pattern.format(**fmt_kwargs)
