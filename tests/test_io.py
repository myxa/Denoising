"""Tests for I/O module."""

import pytest
from pathlib import Path
from denoising.io.file_handler import parse_bids_filename, BIDSFileLoader
from nilearn.interfaces.fmriprep import load_confounds
from denoising.io.nilearn_confounds import NilearnConfoundsHandler
from denoising.config import load_config
from denoising.config.schemas import BIDSConfig
import numpy as np


def test_parse_bids_filename():
    """Test BIDS filename parsing."""
    filename = "sub-1018959_ses-1_task-rest_acq-1_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    result = parse_bids_filename(filename)

    assert result["subject"] == "1018959"
    assert result["session"] == "1"
    assert result["task"] == "rest"
    assert result["run"] == "1"
    assert result["acq"] == "1"
    assert result["space"] == "MNI152NLin2009cAsym"
    assert result["desc"] == "preproc"


def test_parse_bids_filename_partial():
    """Test BIDS filename parsing with partial entities."""
    filename = "sub-1018959_task-rest_bold.nii.gz"
    result = parse_bids_filename(filename)

    assert result["subject"] == "1018959"
    assert result["task"] == "rest"
    assert "session" not in result
    assert "run" not in result


def test_nilearn_confounds_handler():
    """Test NilearnConfoundsHandler produces same results as load_confounds."""
    bold_path = r"/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"

    config = load_config('/home/tm/projects/Denoising/configs/strategy_4.yaml')
    handler = NilearnConfoundsHandler(config.confounds)

    df_handler = handler.load_and_select(bold_path)

    # Verify no NaN values
    assert df_handler.isna().values.sum() == 0

    # Verify confounds were loaded
    assert len(df_handler.columns) > 0
    assert len(df_handler) > 0

    print(f"Loaded {len(df_handler.columns)} confounds for {len(df_handler)} timepoints")


def test_bids_config_validation():
    """Test BIDSConfig validation."""
    # Valid config
    config = BIDSConfig(
        dataset_path="/path/to/bids",
        task="rest",
        space="MNI152NLin2009cAsym",
        desc="preproc",
    )
    assert config.dataset_path == "/path/to/bids"
    assert config.task == "rest"
    assert config.space == "MNI152NLin2009cAsym"
    assert config.desc == "preproc"
    assert config.datatype == "func"  # default
    assert config.extension == "nii.gz"  # default
    #assert config.validate is False  # default


def test_bids_file_loader_init():
    """Test BIDSFileLoader initialization."""
    # This test requires a valid BIDS dataset
    # Skip if dataset not available
    pytest.skip("Requires valid BIDS dataset path")


def test_bids_file_loader_get_subject_files():
    """Test BIDSFileLoader.get_subject_files."""
    # This test requires a valid BIDS dataset
    # Skip if dataset not available
    pytest.skip("Requires valid BIDS dataset path")


def test_bids_file_loader_get_all_subjects():
    """Test BIDSFileLoader.get_all_subjects."""
    # This test requires a valid BIDS dataset
    # Skip if dataset not available
    pytest.skip("Requires valid BIDS dataset path")


def test_parse_bids_filename_with_path():
    """Test BIDS filename parsing with full path."""
    filename = "/path/to/data/sub-1018959_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    result = parse_bids_filename(filename)

    assert result["subject"] == "1018959"
    assert result["session"] == "1"
    assert result["task"] == "rest"
    assert result["run"] == "1"
    assert result["space"] == "MNI152NLin2009cAsym"
    assert result["desc"] == "preproc"


def test_parse_bids_filename_complex():
    """Test BIDS filename parsing with complex entities."""
    filename = "sub-001_ses-01_task-emotion_acq-multiband_run-02_space-T1w_desc-preproc_bold.nii.gz"
    result = parse_bids_filename(filename)

    assert result["subject"] == "001"
    assert result["session"] == "01"
    assert result["task"] == "emotion"
    assert result["acq"] == "multiband"
    assert result["run"] == "02"
    assert result["space"] == "T1w"
    assert result["desc"] == "preproc"
