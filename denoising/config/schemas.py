"""Configuration schemas using Pydantic for validation."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class AtlasConfig(BaseModel):
    """Atlas configuration parameters."""

    name: str = "schaefer_2018"
    resolution: int = 2
    n_regions: int = 400

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: int) -> int:
        if v not in [1, 2]:
            raise ValueError("Resolution must be 1 or 2 mm")
        return v


class NilearnConfoundsConfig(BaseModel):
    """Nilearn load_confounds configuration parameters."""

    strategy: List[str] = Field(
        default_factory=lambda: ["motion", "compcor"],
        description="List of confound strategies to use"
    )

    motion: Optional[str] = Field(
        default="basic",
        description="Motion parameters: basic, derivatives, power2, full"
    )

    compcor: Optional[str] = Field(
        default=None,
        description="CompCor strategy: anat_combined, anat_separated, temp_combined, temp_separated"
    )
    n_compcor: Optional[int] = Field(
        default=None,
        description="Number of CompCor components to use"
    )

    global_signal: Optional[str] = Field(
        default=None,
        description="Global signal: basic, derivatives, power2, full"
    )

    high_pass: Optional[bool] = Field(
        default=None,
        description="High pass - descrete cosine regressors: true, false"
    )

    scrub: Optional[int] = Field(
        default=None,
        description="Number of volumes to remove before/after high motion"
    )
    fd_th: Optional[float] = Field(
        default=None,
        description="Framewise displacement threshold"
    )
    dvars_th: Optional[float] = Field(
        default=None,
        description="DVARS threshold"
    )

    @field_validator("motion", "global_signal")
    @classmethod
    def validate_motion_options(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["basic", "derivatives", "power2", "full"]:
            raise ValueError("Must be basic, derivatives, power2, or full")
        return v

    @field_validator("compcor")
    @classmethod
    def validate_compcor_options(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["anat_combined", "anat_separated", "temp_combined", "temp_separated"]:
            raise ValueError("Must be anat_combined, anat_separated, temp_combined, or temp_separated")
        return v

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: List[str]) -> List[str]:
        valid_strategies = ["motion", "compcor", "global_signal", "high_pass", "low_pass", "cosine", "scrub"]
        invalid = [s for s in v if s not in valid_strategies]
        if invalid:
            raise ValueError(f"Invalid strategies: {invalid}. Valid options: {valid_strategies}")
        return v


class DenoisingConfig(BaseModel):
    """Denoising parameters."""

    smoothing_fwhm: float = None
    detrend: bool = True
    standardize: Optional[str] = None
    standardize_confounds: Optional[bool] = True
    low_pass: Optional[float] = None
    high_pass: Optional[float] = None
    t_r: Optional[float] = None

    @field_validator("standardize")
    @classmethod
    def validate_standardize(cls, v: str) -> str:
        if v not in ["zscore", "psc", "zscore_sample", None]:
            raise ValueError("Standardize must be zscore, psc, or None")
        return v


class OutputConfig(BaseModel):
    """Output configuration."""

    directory: str = "./output"
    naming_pattern: str = "sub-{subject}_ses-{session}_task-{task}_run-{run}_atlas-{atlas_name}.csv"


class BIDSConfig(BaseModel):
    """BIDS dataset configuration."""

    dataset_path: str = Field(..., description="Path to BIDS dataset root")
    task: Optional[str] = Field(None, description="Task name (e.g., 'rest')")
    space: Optional[str] = Field(None, description="Space (e.g., 'MNI152NLin2009cAsym')")
    desc: Optional[str] = Field(None, description="Description (e.g., 'preproc')")
    datatype: str = "func"
    extension: str = "nii.gz"
    #validate: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    file: str = "./logs/denoising.log"

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError("Level must be DEBUG, INFO, WARNING, or ERROR")
        return v.upper()


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""

    atlas: AtlasConfig = Field(default_factory=AtlasConfig)
    denoising: DenoisingConfig = Field(default_factory=DenoisingConfig)
    confounds: NilearnConfoundsConfig = Field(default_factory=NilearnConfoundsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    bids: Optional[BIDSConfig] = Field(None, description="BIDS dataset configuration")

class ConfoundsConfig(BaseModel):
    pass