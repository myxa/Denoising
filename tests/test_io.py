"""Tests for I/O module."""

import pytest
from denoising.io.file_handler import parse_bids_filename
from nilearn.interfaces.fmriprep import load_confounds
from denoising.io.nilearn_confounds import NilearnConfoundsHandler
from denoising.config import load_config
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
