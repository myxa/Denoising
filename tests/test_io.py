"""Tests for I/O module."""

import pytest
from denoising.io.file_handler import parse_bids_filename
from nilearn.interfaces.fmriprep import load_confounds
from denoising.io.confounds import ConfoundsHandler
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


def test_confounds():
    strategy_4 = {'strategy': ['motion', 'compcor', 'high_pass', 'global_signal'],
                  'motion': 'full',
                  'compcor': 'anat_combined',
                  'n_compcor': 10,
                  'global_signal': 'full',}
    
    bold_path = r"/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    confounds_path = r"/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_desc-confounds_timeseries.tsv"

    df_nilearn, _ = load_confounds(bold_path, **strategy_4)

    config = load_config('/home/tm/projects/Denoising/configs/strategy_4.yaml')
    conf = ConfoundsHandler(config.confounds)

    df_conf = conf.load_and_select(confounds_path)

    assert df_nilearn.isna().values.sum() == 0
    a=df_conf.isna().values.sum() == 0

    #print(df_nilearn.values[1:, :].round(4))
    #print(df_conf.values[1:, :].round(4))

    a = np.isclose(df_nilearn.values[1:, :], df_conf.values[1:, :], rtol=1e-04, atol=1e-04)

    print(sum(a))
test_confounds()
