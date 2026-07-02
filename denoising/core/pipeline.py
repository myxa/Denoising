"""Main pipeline orchestrator for denoising and time-series extraction."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from tqdm.auto import tqdm

import nibabel as nib
from nilearn.maskers import NiftiLabelsMasker

from denoising.config.schemas import PipelineConfig
from denoising.core.atlas import AtlasManager
from denoising.core.extractor import SignalExtractor
from denoising.io.nilearn_confounds import NilearnConfoundsHandler
from denoising.io.file_handler import BIDSFileLoader

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
        self.atlas_data = self.atlas_manager.fetch_atlas()

        self.extractor = SignalExtractor(
            smoothing_fwhm=config.denoising.smoothing_fwhm,
            detrend=config.denoising.detrend,
            standardize=config.denoising.standardize,
            standardize_confounds=config.denoising.standardize_confounds,
            low_pass=config.denoising.low_pass,
            high_pass=config.denoising.high_pass,
            t_r=config.denoising.t_r,
        )
        self.confounds_handler = NilearnConfoundsHandler(config.confounds)

    def process_subject(
        self,
        bold_path: str,
        mask_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        bids_info: Dict[str, str] = None,
    ) -> str:
        """Process a single subject's data.

        Args:
            bold_path: Path to BOLD NIfTI file.
            mask_path: Optional path to a mask image.
            output_dir: Output directory (uses config default if None).
            bids_info: Pre-parsed BIDS entities (required).

        Returns:
            Tuple of (timeseries DataFrame, output CSV file path).
        """
        if bids_info is None:
            raise ValueError("bids_info is required. Use BIDSFileLoader.get_bids_entities() to extract entities.")

        output_dir = output_dir or self.config.output.directory

        logger.info(f"Processing: {bold_path}")

        # Create BIDS-compliant output directory structure
        subject = bids_info.get("subject", "unknown")
        session = bids_info.get("session")

        subject_output_dir = Path(output_dir) / f"sub-{subject}"
        if session:
            subject_output_dir = subject_output_dir / f"ses-{session}"
        subject_output_dir = subject_output_dir / "time-series"

        # Fetch atlas and configure masker
        masker = NiftiLabelsMasker(
            labels_img=self.atlas_data.maps,
            labels=self.atlas_data.labels,
            mask_img=mask_path
            )

        # Load and select confounds
        confounds, sample_mask = self.confounds_handler.load_and_select(bold_path)

        # Conflict checks: DCT (from confounds) vs bandpass / detrend (from masker)
        if self.confounds_handler.config.high_pass and self.extractor.high_pass is not None:
            raise ValueError(
                "Both DCT (from confounds) and bandpass filter (from masker) are enabled. "
                "Please remove one of them."
            )

        if self.confounds_handler.config.high_pass and self.extractor.detrend:
            raise ValueError(
                "Using both DCT (from fmriprep confounds) and detrend (from masker) is redundant. "
                "Please disable one of them."
            )

        # Detect TR from BOLD header if needed for bandpass filtering
        detected_tr = None
        if self.extractor.t_r is None and self.extractor.low_pass is not None:
            bold_img = nib.load(bold_path)
            detected_tr = bold_img.header.get_zooms()[-1]
            logger.info(f"Detected TR: {detected_tr} s")

        # Apply denoising parameters to the masker
        self.extractor.configure_masker(masker, t_r=detected_tr)

        logger.info(f"Selected confounds: {confounds.columns.tolist()}")

        # Extract time-series
        timeseries = self.extractor.extract(
            bold_path,
            masker,
            confounds=confounds,
            sample_mask=sample_mask,
        )

        if output_dir is not None:
            # Generate output filename and save
            output_filename = SignalExtractor.make_output_filename(
                subject=subject,
                session=session,
                task=bids_info.get("task"),
                run=bids_info.get("run"),
                atlas_name=self.config.atlas.name,
                n_rois=self.config.atlas.n_regions,
                pattern=self.config.output.naming_pattern,
            )
            output_path = str(subject_output_dir / output_filename)

            SignalExtractor.save(timeseries, output_path)

            logger.info(f"Completed: {output_path}")

        return timeseries

    def process_batch(
        self,
        subjects: Union[str, List[str]],
        output_dir: Optional[str] = None,
        bids_loader: BIDSFileLoader = None,
    ) -> List[tuple]:
        """Process multiple subjects using BIDS dataset.

        Args:
            subjects: 'all' for all subjects in dataset, or list of subject IDs.
            output_dir: Output directory.
            bids_loader: BIDSFileLoader instance.

        Returns:
            List of tuples (timeseries DataFrame, output path) or None for failed subjects.
        """
        if bids_loader is None:
            raise ValueError("bids_loader is required")
        if self.config.bids is None:
            raise ValueError("BIDS config is required")

        results = []
        failed = []

        if subjects == "all":
            subjects = bids_loader.get_all_subjects()

        logger.info(f"Processing {len(subjects)} subjects")

        for subject_id in tqdm(subjects):
            logger.info(f"Processing subject: {subject_id}")
            try:
                # Get all files for this subject
                files = bids_loader.get_subject_img(
                    subject=subject_id,
                    task=self.config.bids.task,
                    space=self.config.bids.space,
                    desc="preproc",
                    session=self.config.bids.session,
                    datatype="func",
                )
                masks = bids_loader.get_subject_mask(
                    subject=subject_id,
                    task=self.config.bids.task,
                    space=self.config.bids.space,
                    desc="brain",
                    session=self.config.bids.session,
                    datatype="func",
                )

                if not files:
                    logger.warning(f"No files found for subject {subject_id}")
                    results.append(None)
                    failed.append(subject_id)
                    continue

                if masks:
                    all_files = list(zip(files, masks))
                else:
                    all_files = [(f, None) for f in files]

                # Process each file (handles multiple sessions/runs)
                for img, mask in all_files:
                    logger.info(f"Processing file: {img}")
                    bids_info = bids_loader.get_bids_entities(img)
                    output = self.process_subject(
                        img,
                        mask,
                        output_dir,
                        bids_info=bids_info,
                    )
                    results.append(output)

            except Exception as e:
                logger.error(f"Failed to process subject {subject_id}: {e}")
                failed.append(subject_id)
                results.append(None)

        if failed:
            print("Failed to process:", failed)
            logger.warning(f"Failed to process {len(failed)} subjects: {failed}")

        return results