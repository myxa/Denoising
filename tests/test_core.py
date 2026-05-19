"""Tests for core module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from denoising.core.atlas import AtlasManager
from denoising.core.denoiser import Denoiser
from nilearn.maskers import NiftiLabelsMasker


def test_denoiser_initialization():
    """Test Denoiser initialization."""
    denoiser = Denoiser(
        smoothing_fwhm=6.0,
        detrend=True,
        standardize="zscore",
        low_pass=0.1,
        high_pass=0.01,
        t_r=2.0,
    )

    assert denoiser.smoothing_fwhm == 6.0
    assert denoiser.detrend is True
    assert denoiser.standardize == "zscore"
    assert denoiser.low_pass == 0.1
    assert denoiser.high_pass == 0.01
    assert denoiser.t_r == 2.0


def test_denoiser_get_masker_params():
    """Test Denoiser masker parameter generation."""
    denoiser = Denoiser(smoothing_fwhm=8.0, detrend=False, standardize="false")
    params = denoiser.get_masker_params()

    assert params["smoothing_fwhm"] == 8.0
    assert params["detrend"] is False
    assert params["standardize"] is False
    assert params["standardize_confounds"] is False


def test_denoiser_get_masker_params_with_filters():
    """Test Denoiser masker parameters with filtering."""
    denoiser = Denoiser(low_pass=0.1, high_pass=0.01, t_r=2.0)
    params = denoiser.get_masker_params()

    assert params["low_pass"] == 0.1
    assert params["high_pass"] == 0.01


def test_denoiser_validate_timeseries():
    """Test timeseries validation."""
    denoiser = Denoiser()
    timeseries = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    result = denoiser.validate_timeseries(timeseries, 3)
    assert result is True


def test_denoiser_validate_timeseries_mismatch():
    """Test timeseries validation with mismatch."""
    denoiser = Denoiser()
    timeseries = [[1, 2, 3], [4, 5, 6]]

    with pytest.raises(ValueError, match="Timeseries has 2 timepoints, expected 3"):
        denoiser.validate_timeseries(timeseries, 3)

def test_download_bnt():
    manager = AtlasManager(atlas_name="brainnetome", resolution=1, n_regions=246)
    masker = manager.fetch_atlas()
    assert isinstance(masker, NiftiLabelsMasker)
    assert isinstance(masker.labels, list)
    assert masker.labels[0] == "Background"


def test_atlas_manager_brainnetome_initialization():
    """Test AtlasManager initialization with brainnetome atlas."""
    manager = AtlasManager(atlas_name="brainnetome", resolution=2, n_regions=246)
    
    assert manager.atlas_name == "brainnetome"
    assert manager.resolution == 2
    assert manager.n_regions == 246
    assert manager._atlas_data is None
    assert manager._masker is None

