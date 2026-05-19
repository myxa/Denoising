"""Denoising operations for fMRI data."""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class Denoiser:
    """Apply denoising operations to fMRI data."""

    def __init__(
        self,
        smoothing_fwhm: float = 6.0,
        detrend: bool = True,
        standardize: str = "zscore",
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
    ):
        """Initialize Denoiser.

        Args:
            smoothing_fwhm: Full width at half maximum for smoothing (mm).
            detrend: Whether to apply detrending.
            standardize: Standardization method ('zscore', 'psc', or 'false').
            low_pass: Low pass filter cutoff (Hz).
            high_pass: High pass filter cutoff (Hz).
            t_r: Repetition time (seconds). Required for filtering.
        """
        self.smoothing_fwhm = smoothing_fwhm
        self.detrend = detrend
        self.standardize = standardize
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r

    def get_masker_params(self) -> dict:
        """Get parameters for NiftiLabelsMasker.

        Returns:
            Dictionary of masker parameters.
        """
        params = {
            "smoothing_fwhm": self.smoothing_fwhm,
            "detrend": self.detrend,
            "standardize": self.standardize != "false",
            "standardize_confounds": self.standardize != "false",
        }

        if self.low_pass is not None and self.t_r is not None:
            params["low_pass"] = self.low_pass
        if self.high_pass is not None and self.t_r is not None:
            params["high_pass"] = self.high_pass

        return params

    def validate_timeseries(self, timeseries: np.ndarray, n_timepoints: int) -> bool:
        """Validate that timeseries matches expected timepoints.

        Args:
            timeseries: Timeseries array.
            n_timepoints: Expected number of timepoints.

        Returns:
            True if valid.

        Raises:
            ValueError: If validation fails.
        """
        if timeseries.shape[0] != n_timepoints:
            raise ValueError(
                f"Timeseries has {timeseries.shape[0]} timepoints, "
                f"expected {n_timepoints}"
            )
        return True