"""Nilearn-based confounds loading using load_confounds."""

import logging
from typing import Dict, Any, Optional

import pandas as pd
from nilearn.interfaces.fmriprep import load_confounds

from denoising.config.schemas import NilearnConfoundsConfig

logger = logging.getLogger(__name__)


class NilearnConfoundsHandler:
    """Handle confounds loading using nilearn's load_confounds."""

    def __init__(self, config: NilearnConfoundsConfig):
        """Initialize with nilearn confounds configuration.

        Args:
            config: Nilearn confounds configuration.
        """
        self.config = config

    def load_and_select(self, bold_path: str) -> pd.DataFrame:
        """Load and select confounds using nilearn's load_confounds.

        Args:
            bold_path: Path to BOLD NIfTI file.

        Returns:
            DataFrame with selected confounds.
        """
        params = self._config_to_params()

        logger.info(f"Loading confounds for {bold_path}")
        logger.debug(f"Parameters: {params}")

        confounds_df, sample_mask = load_confounds(bold_path, **params)

        logger.info(f"Loaded {len(confounds_df.columns)} confounds")
        return confounds_df

    def _config_to_params(self) -> Dict[str, Any]:
        """Convert config object to params dict for load_confounds.

        Returns:
            Dictionary of parameters for nilearn's load_confounds.
        """
        params = {
            'strategy': self.config.strategy,
        }

        # Add optional parameters only if they are set
        if self.config.motion is not None:
            params['motion'] = self.config.motion
        if self.config.compcor is not None:
            params['compcor'] = self.config.compcor
        if self.config.n_compcor is not None:
            params['n_compcor'] = self.config.n_compcor
        if self.config.global_signal is not None:
            params['global_signal'] = self.config.global_signal
        if self.config.high_pass is not None:
            params['high_pass'] = self.config.high_pass
        if self.config.low_pass is not None:
            params['low_pass'] = self.config.low_pass
        if self.config.cosine is not None:
            params['cosine'] = self.config.cosine
        if self.config.scrub is not None:
            params['scrub'] = self.config.scrub
        if self.config.fd_th is not None:
            params['fd_th'] = self.config.fd_th
        if self.config.dvars_th is not None:
            params['dvars_th'] = self.config.dvars_th
        if self.config.tr is not None:
            params['tr'] = self.config.tr
        if self.config.include is not None:
            params['include'] = self.config.include
        if self.config.exclude is not None:
            params['exclude'] = self.config.exclude

        return params