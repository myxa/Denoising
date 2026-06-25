"""Main pipeline orchestrator for denoising and time-series extraction."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from tqdm.auto import tqdm

import nibabel as nib

from denoising.config.schemas import PipelineConfig
from denoising.core.atlas import AtlasManager
from denoising.core.denoiser import Denoiser
from denoising.core.extractor import TimeSeriesExtractor
from denoising.io.nilearn_confounds import NilearnConfoundsHandler
from denoising.io.file_handler import parse_bids_filename, BIDSFileLoader

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
            standardize_confounds=config.denoising.standardize_confounds,
            low_pass=config.denoising.low_pass,
            high_pass=config.denoising.high_pass,
            t_r=config.denoising.t_r,
        )
        self.extractor = TimeSeriesExtractor()
        self.confounds_handler = NilearnConfoundsHandler(config.confounds)

    def process_subject(
        self,
        bold_path: str,
        output_dir: Optional[str] = None,
        bids_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """Process a single subject's data.

        Args:
            bold_path: Path to BOLD NIfTI file.
            output_dir: Output directory (uses config default if None).
            bids_info: Optional pre-parsed BIDS entities.

        Returns:
            Tuple of (timeseries DataFrame, output CSV file path).
        """
        output_dir = output_dir or self.config.output.directory

        logger.info(f"Processing: {bold_path}")

        # Parse BIDS filename for output naming
        if bids_info is None:
            bids_info = parse_bids_filename(bold_path)
        
        # Create BIDS-compliant output directory structure
        subject = bids_info.get("subject", "unknown")
        session = bids_info.get("session")
        
        subject_output_dir = Path(output_dir) / f"sub-{subject}"
        if session:
            subject_output_dir = subject_output_dir / f"ses-{session}"
        subject_output_dir = subject_output_dir / "time-series"
        
        # Fetch atlas and configure masker
        masker = self.atlas_manager.fetch_atlas()
        masker_params = self.denoiser.get_masker_params()

        # Load and select confounds
        confounds, sample_mask = self.confounds_handler.load_and_select(bold_path)

        # IF BOTH COSINES AND BANDPASS 
        if self.confounds_handler.config.high_pass and masker_params['high_pass']:
            raise ValueError("Both DCT and bandpass filters of masker. Please remove one of them.")
        
        if self.confounds_handler.config.high_pass and masker_params['detrend']:
            raise ValueError("Using both DCT from fmriprep confounds and detrend of masker is redundant")
        
        # Load BOLD header to get TR if not specified
        # needed only for masker's bandpass
        if self.denoiser.t_r is None and self.denoiser.low_pass is not None:
            bold_img = nib.load(bold_path)
            self.denoiser.t_r = bold_img.header.get_zooms()[-1]
            masker_params['t_r'] = self.denoiser.t_r
            logger.info(f"Detected TR: {self.denoiser.t_r} s")
        
        for key, value in masker_params.items():
            setattr(masker, key, value)

        logger.info(f"Selected confounds: {confounds.columns.tolist()}")

        # Extract time-series
        timeseries = self.extractor.extract_timeseries(
            bold_path,
            masker,
            confounds=confounds,
            sample_mask=sample_mask,
        )
        if output_dir is not None:
            # Generate output filename and save
            output_filename = self.extractor.get_output_filename(
                subject=subject,
                session=session or "unknown",
                task=bids_info.get("task", "unknown"),
                run=bids_info.get("run", "unknown"),
                atlas_name=self.config.atlas.name,
                n_rois=self.config.atlas.n_regions,
                pattern=self.config.output.naming_pattern,
            )
            output_path = str(subject_output_dir / output_filename)

            self.extractor.save_timeseries(
                timeseries,
                output_path,
            )

            logger.info(f"Completed: {output_path}")
        return timeseries

    def process_batch(
        self,
        subjects: Union[str, List[str], List[dict]],
        output_dir: Optional[str] = None,
        bids_loader: Optional[BIDSFileLoader] = None,
    ) -> List[tuple]:
        """Process multiple subjects.

        Args:
            subjects: 'all' for all subjects in dataset (if bids provided), List of subject IDs (BIDS mode) or list of dicts with 'bold_path' key (legacy mode).
            output_dir: Output directory.
            bids_loader: Optional BIDSFileLoader instance for BIDS mode.

        Returns:
            List of tuples (timeseries DataFrame, output path) or None for failed subjects.
        """
        results = []
        failed = []

        if subjects == "all":
            subjects = bids_loader.get_all_subjects()
            
        
        # Detect mode: BIDS mode if subjects are strings, legacy mode if dicts
        is_bids_mode = True if isinstance(bids_loader, BIDSFileLoader) else False
        
        if is_bids_mode:
            if bids_loader is None:
                raise ValueError("bids_loader is required for BIDS mode")
            if self.config.bids is None:
                raise ValueError("BIDS config is required for BIDS mode")
            
            logger.info(f"Processing {len(subjects)} subjects in BIDS mode")
            
            for subject_id in tqdm(subjects):
                logger.info(f"Processing subject: {subject_id}")
                try:
                    # Get all files for this subject
                    files = bids_loader.get_subject_img(
                        subject=subject_id,
                        task=self.config.bids.task,
                        space=self.config.bids.space,
                        desc=self.config.bids.desc,
                        datatype=self.config.bids.datatype,
                        extension=self.config.bids.extension,
                    )
                    
                    if not files:
                        logger.warning(f"No files found for subject {subject_id}")
                        results.append(None)
                        failed.append(subject_id)
                        continue
                    
                    # Process each file (handles multiple sessions/runs)
                    for file_path in files:
                        logger.info(f"Processing file: {file_path}")
                        output = self.process_subject(
                            file_path,
                            output_dir,
                        )
                        results.append(output)
                        
                except Exception as e:
                    logger.error(f"Failed to process subject {subject_id}: {e}")
                    failed.append(subject_id)
                    results.append(None)
                    
        else:
            # Legacy mode
            logger.info(f"Processing {len(subjects)} subjects in legacy mode")
            
            for i, subject in enumerate(subjects):
                logger.info(f"Processing subject {i+1}/{len(subjects)}")
                try:
                    output = self.process_subject(
                        subject["bold_path"],
                        output_dir,
                    )
                    results.append(output)
                except Exception as e:
                    logger.error(f"Failed to process {subject['bold_path']}: {e}")
                    failed.append(i)
                    results.append(None)

        if failed:
            print('Failed to process:', failed)
            logger.warning(f"Failed to process {len(failed)} subjects: {failed}")

        return results