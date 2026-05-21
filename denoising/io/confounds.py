"""Confounds loading and selection from TSV files."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from denoising.config.schemas import ConfoundsConfig

logger = logging.getLogger(__name__)


class ConfoundsHandler:
    """Handle confounds loading and selection."""

    def __init__(self, config: ConfoundsConfig):
        """Initialize ConfoundsHandler.

        Args:
            config: Confounds configuration.
        """
        self.config = config

    def load_confounds(self, tsv_path: str) -> pd.DataFrame:
        """Load confounds from TSV file.

        Args:
            tsv_path: Path to confounds TSV file.

        Returns:
            DataFrame with confounds.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(tsv_path)
        if not path.exists():
            raise FileNotFoundError(f"Confounds file not found: {tsv_path}")

        logger.info(f"Loading confounds from {tsv_path}")
        df = pd.read_csv(tsv_path, sep="\t", comment="#")
        logger.info(f"Loaded {len(df.columns)} confound columns")

        return df

    def get_available_confounds(self, tsv_path: str) -> List[str]:
        """Get list of available confound columns.

        Args:
            tsv_path: Path to confounds TSV file.

        Returns:
            List of column names.
        """
        df = self.load_confounds(tsv_path)
        return df.columns.tolist()

    def select_confounds(self, confounds_df: pd.DataFrame, n_timepoints: Optional[int] = None) -> np.ndarray:
        """Select confounds based on configuration strategy.

        Args:
            confounds_df: DataFrame with all confounds.
            n_timepoints: Expected number of timepoints for validation.

        Returns:
            Confounds matrix (timepoints x confounds).
        """
        if self.config.strategy == "simple":
            columns = self._select_simple_confounds(confounds_df)
        elif self.config.strategy == "scrubbing":
            columns = self._select_scrubbing_confounds(confounds_df)
        else:
            columns = self._select_custom_confounds(confounds_df)

        selected = confounds_df[columns].copy()

        # Validate timepoints
        #if n_timepoints is not None:
        #    self._validate_confounds(selected.values, n_timepoints)

        logger.info(f"Selected {selected.shape[1]} confounds: {selected.columns.tolist()}")
        return selected#.values

    def load_and_select(self, tsv_path: str, demean: Optional[bool] = False, n_timepoints: Optional[int] = None) -> np.ndarray:
        """Load and select confounds in one step.

        Args:
            tsv_path: Path to confounds TSV file.
            n_timepoints: Expected number of timepoints for validation.

        Returns:
            Confounds matrix.
        """
        df = self.load_confounds(tsv_path)
        if demean:
            df.subtract(df.mean(), axis=0, inplace=True)

        df.interpolate('values', inplace=True).ffill(inplace=True).bfill(inplace=True)
        df.fillna(0, inplace=True)
        return self.select_confounds(df, n_timepoints)

    def _select_custom_confounds(self, confounds_df: pd.DataFrame) -> List[str]:
        """Select confounds based on custom column list.

        Args:
            confounds_df: DataFrame with all confounds.

        Returns:
            List of selected column names.

        Raises:
            ValueError: If specified columns don't exist.
        """
        available = confounds_df.columns.tolist()
        missing = [c for c in self.config.columns if c not in available]

        if missing:
            raise ValueError(f"Confounds not found: {missing}")

        return self.config.columns

    def _select_simple_confounds(self, confounds_df: pd.DataFrame) -> List[str]:
        """Select basic motion and physiological confounds.

        Args:
            confounds_df: DataFrame with all confounds.

        Returns:
            List of selected column names.
        """
        simple_patterns = [
            "csf",
            "white_matter",
            "trans_x",
            "trans_y",
            "trans_z",
            "rot_x",
            "rot_y",
            "rot_z",
        ]

        columns = []
        for pattern in simple_patterns:
            matching = [c for c in confounds_df.columns if pattern in c.lower()]
            columns.extend(matching)

        return columns

    def _select_scrubbing_confounds(self, confounds_df: pd.DataFrame) -> List[str]:
        """Select confounds with framewise displacement threshold.

        Args:
            confounds_df: DataFrame with all confounds.

        Returns:
            List of selected column names.
        """
        columns = self._select_simple_confounds(confounds_df)

        if self.config.fd_threshold is not None:
            fd_cols = [c for c in confounds_df.columns if "framewise_displacement" in c.lower()]
            columns.extend(fd_cols)

        return columns

    def _validate_confounds(self, confounds: np.ndarray, n_timepoints: int):
        """Validate confounds matrix matches expected timepoints.

        Args:
            confounds: Confounds matrix.
            n_timepoints: Expected number of timepoints.

        Raises:
            ValueError: If validation fails.
        """
        if confounds.shape[0] != n_timepoints:
            raise ValueError(
                f"Confounds have {confounds.shape[0]} timepoints, "
                f"expected {n_timepoints}"
            )