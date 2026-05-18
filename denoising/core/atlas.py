"""Atlas fetching and management."""

import logging
from pathlib import Path
from typing import List, Optional

import nilearn.datasets
from nilearn.maskers import NiftiLabelsMasker

logger = logging.getLogger(__name__)


class AtlasManager:
    """Manage atlas fetching and NiftiLabelsMasker creation."""

    def __init__(self, atlas_name: str = "schaefer_2018", resolution: int = 2, n_regions: int = 400):
        """Initialize AtlasManager.

        Args:
            atlas_name: Name of the atlas (currently only schaefer_2018 supported).
            resolution: Atlas resolution in mm (1 or 2).
            n_regions: Number of brain regions.
        """
        self.atlas_name = atlas_name
        self.resolution = resolution
        self.n_regions = n_regions
        self._atlas_data = None
        self._masker = None

    def fetch_atlas(self, cache_dir: Optional[str] = None) -> NiftiLabelsMasker:
        """Fetch atlas and create NiftiLabelsMasker.

        Args:
            cache_dir: Directory to cache atlas files.

        Returns:
            Configured NiftiLabelsMasker instance.
        """
        if self._masker is not None:
            return self._masker

        logger.info(f"Fetching {self.atlas_name} atlas with {self.n_regions} regions at {self.resolution}mm")

        if self.atlas_name == "schaefer_2018":
            atlas = nilearn.datasets.fetch_atlas_schaefer_2018(
                n_rois=self.n_regions,
                yeo_networks=7,
                resolution_mm=self.resolution,
                data_dir=cache_dir,
            )
            self._atlas_data = atlas
            self._masker = NiftiLabelsMasker(
                labels_img=atlas.maps,
                labels=atlas.labels,
                standardize=False,
            )
        else:
            raise ValueError(f"Atlas {self.atlas_name} not supported")

        return self._masker

    def get_region_names(self) -> List[str]:
        """Get region names from the atlas.

        Returns:
            List of region names.

        Raises:
            RuntimeError: If atlas hasn't been fetched yet.
        """
        if self._atlas_data is None:
            raise RuntimeError("Atlas not fetched. Call fetch_atlas() first.")
        return self._atlas_data.labels

    def get_atlas_image(self):
        """Get the atlas image.

        Returns:
            Atlas image object.

        Raises:
            RuntimeError: If atlas hasn't been fetched yet.
        """
        if self._atlas_data is None:
            raise RuntimeError("Atlas not fetched. Call fetch_atlas() first.")
        return self._atlas_data.maps

    def cache_atlas(self, cache_dir: str):
        """Cache atlas to specified directory.

        Args:
            cache_dir: Directory path for caching.
        """
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self.fetch_atlas(cache_dir=cache_dir)