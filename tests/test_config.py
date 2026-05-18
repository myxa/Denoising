"""Tests for configuration module."""

import pytest
from denoising.config.schemas import AtlasConfig, DenoisingConfig, ConfoundsConfig, PipelineConfig


def test_atlas_config():
    """Test AtlasConfig validation."""
    config = AtlasConfig(name="schaefer_2018", resolution=2, n_regions=400)
    assert config.name == "schaefer_2018"
    assert config.resolution == 2
    assert config.n_regions == 400


def test_atlas_config_invalid_resolution():
    """Test AtlasConfig with invalid resolution."""
    with pytest.raises(ValueError, match="Resolution must be 1 or 2"):
        AtlasConfig(resolution=3)


def test_denoising_config():
    """Test DenoisingConfig."""
    config = DenoisingConfig(smoothing_fwhm=6.0, detrend=True, standardize="zscore")
    assert config.smoothing_fwhm == 6.0
    assert config.detrend is True
    assert config.standardize == "zscore"


def test_denoising_config_invalid_standardize():
    """Test DenoisingConfig with invalid standardize."""
    with pytest.raises(ValueError, match="Standardize must be"):
        DenoisingConfig(standardize="invalid")


def test_confounds_config():
    """Test ConfoundsConfig."""
    config = ConfoundsConfig(strategy="custom", columns=["csf", "white_matter"])
    assert config.strategy == "custom"
    assert "csf" in config.columns


def test_confounds_config_invalid_strategy():
    """Test ConfoundsConfig with invalid strategy."""
    with pytest.raises(ValueError, match="Strategy must be"):
        ConfoundsConfig(strategy="invalid")


def test_pipeline_config():
    """Test PipelineConfig."""
    config = PipelineConfig()
    assert config.atlas.name == "schaefer_2018"
    assert config.denoising.smoothing_fwhm == 6.0
    assert config.confounds.strategy == "custom"