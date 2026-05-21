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


class ConfoundsConfig(BaseModel):
    """Confounds selection configuration."""

    strategy: str = "custom"
    columns: List[str] = Field(default_factory=lambda: ["csf", "white_matter", "global_signal"])
    #derivatives: Optional[Dict[str, List[str]]] = None
    fd_threshold: Optional[float] = None

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        if v not in ["custom", "simple", "scrubbing"]:
            raise ValueError("Strategy must be custom, simple, or scrubbing")
        return v


class DenoisingConfig(BaseModel):
    """Denoising parameters."""

    smoothing_fwhm: float = None
    detrend: bool = True
    standardize: Union[str, bool] = False
    low_pass: Optional[float] = None
    high_pass: Optional[float] = None
    t_r: Optional[float] = None

    @field_validator("standardize")
    @classmethod
    def validate_standardize(cls, v: str) -> str:
        if v not in ["zscore", "psc", False]:
            raise ValueError("Standardize must be zscore, psc, or false")
        return v


class OutputConfig(BaseModel):
    """Output configuration."""

    directory: str = "./output"
    naming_pattern: str = "{subject}_{session}_{task}_{run}_atlas-{atlas_name}.csv"
    include_metadata: bool = True


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
    confounds: ConfoundsConfig = Field(default_factory=ConfoundsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)