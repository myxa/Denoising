"""Core processing modules."""

from denoising.core.atlas import AtlasManager
from denoising.core.extractor import SignalExtractor
from denoising.core.pipeline import DenoisingPipeline

__all__ = [
    "AtlasManager",
    "SignalExtractor",
    "DenoisingPipeline",
]