"""Main pipeline orchestrator for denoising and time-series extraction."""

import logging
from pathlib import Path
from typing import List, Optional

import nibabel as nib

from denoising.config.schemas import PipelineConfig
from denoising.core.atlas import AtlasManager
from denoising.core.denoiser import Denoiser
from denoising.core.extractor import TimeSeriesExtractor
from denoising.io.confounds import ConfoundsHandler
from denoising.io.file_handler import parse_bids_filename

logger = logging.getLogger(__name__)


class DenoisingPipeline:
    """Main pipeline for fMRI denoising and time-series extraction."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline with configuration.

        Args:
            config: Pipeline configuration.
        """
        self.config = config
        self.atlas_manager = AtlasManager(
            atlas_name=config.atlas.name,
            resolution=config.atlas.resolution,
            n_regions=config.atlas.n_regions,
        )
        self.denoiser = Denoiser(
            smoothing_fwhm=config.denoising.smoothing_fwhm,
            detrend=config.denoising.detrend,
            standardize=config.denoising.standardize,
            low_pass=config.denoising.low_pass,
            high_pass=config.denoising.high_pass,
            t_r=config.denoising.t_r,
        )
        self.extractor = TimeSeriesExtractor()
        self.confounds_handler = ConfoundsHandler(config.confounds)

    def process_subject(
        self,
        bold_path: str,
        confounds_path: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """Process a single subject's data.

        Args:
            bold_path: Path to BOLD NIfTI file.
            confounds_path: Path to confounds TSV file.
            output_dir: Output directory (uses config default if None).

        Returns:
            Path to output CSV file.
        """
        output_dir = output_dir or self.config.output.directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Processing: {bold_path}")

        # Parse BIDS filename for output naming
        bids_info = parse_bids_filename(bold_path)

        # Fetch atlas and configure masker
        masker = self.atlas_manager.fetch_atlas()
        masker_params = self.denoiser.get_masker_params()

        # Load and select confounds
        confounds = self.confounds_handler.load_and_select(confounds_path)

        # IF BOTH COSINES AND FILTERING BANDPASS 
        if "cosine" in confounds and (
            masker_params['low_pass'] is not None and masker_params['high_pass'] is not None):
            raise ValueError("Both cosines and bandpass filters are in confounds. Please remove one of them.")
        
        # Load BOLD header to get TR if not specified
        if self.denoiser.t_r is None:
            bold_img = nib.load(bold_path)
            self.denoiser.t_r = bold_img.header.get_zooms()[-1]
            masker_params['t_r'] = self.denoiser.t_r
            logger.info(f"Detected TR: {self.denoiser.t_r} s")
        
        for key, value in masker_params.items():
            setattr(masker, key, value)

        logger.info(f"Selected confounds: {confounds}")

        # Extract time-series
        timeseries = self.extractor.extract_timeseries(
            bold_path,
            masker,
            confounds=confounds,
        )

        # Generate output filename and save
        output_filename = self.extractor.get_output_filename(
            subject=bids_info.get("subject", "unknown"),
            session=bids_info.get("session", "unknown"),
            task=bids_info.get("task", "unknown"),
            run=bids_info.get("run", "unknown"),
            atlas_name=self.config.atlas.name,
            pattern=self.config.output.naming_pattern,
        )
        output_path = str(Path(output_dir) / output_filename)

        self.extractor.save_timeseries(
            timeseries,
            output_path,
            include_metadata=self.config.output.include_metadata,
        )

        logger.info(f"Completed: {output_path}")
        return output_path

    def process_batch(
        self,
        subjects: List[dict],
        output_dir: Optional[str] = None,
    ) -> List[str]:
        """Process multiple subjects.

        Args:
            subjects: List of dicts with 'bold_path' and 'confounds_path' keys.
            output_dir: Output directory.

        Returns:
            List of output file paths.
        """
        results = []
        for i, subject in enumerate(subjects):
            logger.info(f"Processing subject {i+1}/{len(subjects)}")
            try:
                output = self.process_subject(
                    subject["bold_path"],
                    subject["confounds_path"],
                    output_dir,
                )
                results.append(output)
            except Exception as e:
                logger.error(f"Failed to process {subject['bold_path']}: {e}")
                results.append(None)

        return results