"""Tests for I/O module."""

import pytest
from denoising.io.file_handler import parse_bids_filename


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