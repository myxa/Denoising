"""Atlas fetching and management."""

import logging
from pathlib import Path
from typing import List, Optional

import nibabel as nib
import nilearn.datasets
import numpy as np
from nilearn.maskers import NiftiLabelsMasker

from denoising.utils.helpers import download_file

import pandas as pd

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

            
        elif self.atlas_name.lower() == "brainnetome":
            atlas = self._fetch_brainnetome_atlas(cache_dir)
            self._atlas_data = atlas
            self._masker = NiftiLabelsMasker(
                labels_img=atlas.maps,
                labels=atlas.labels,
                standardize=False,
            )
            
        else:
            raise ValueError(f"Atlas {self.atlas_name} not supported")

        return self._masker

    def _fetch_brainnetome_atlas(self, cache_dir: Optional[str] = None):
        """Fetch Brainnetome atlas.

        Args:
            cache_dir: Directory to cache atlas files.

        Returns:
            Atlas data object with maps and labels attributes.
        """
        if cache_dir is None:
            cache_dir = Path.home() / "nilearn_data" / "brainnetome"
        else:
            cache_dir = Path(cache_dir) / "brainnetome"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard Brainnetome atlas file names
        atlas_file = cache_dir / f"BN_Atlas_246_{self.resolution}mm.nii.gz"
        labels_file = cache_dir / f"BN_Atlas_246_Label.txt"
        
        # Brainnetome atlas download URLs
        if self.resolution == 1:
            atlas_url = "https://pan.cstcloud.cn/unode/stor/downloadByUrl?downloadId=1.eyJidWNrZXQiOiJkZWZhdWx0IiwibGVuIjoxNzYzMjEsInNpemUiOjE3NjMyMSwicG9zIjowLCJuYW1lIjoiQk5fQXRsYXNfMjQ2XzFtbS5uaWkuZ3oiLCJjdGltZSI6MTc3OTIxNTczNCwia2V5IjoiR3MyMkJRSHlVYl9Zd0lJSXB3MHFLQmdNOEJNQUFyREIiLCJhZ2UiOjg2NDAwLCJwYXJ0T25lIjp7InNpemUiOjE3NjMyMSwiZm4iOiJLRkdxTFB4SFFwZy0wLTE3NjMyMSIsImNyYzMyIjozMjY1ODc3NTM3LCJiaWQiOjEsImNpZCI6MX19.415090223"
        elif self.resolution == 2:
            atlas_url = "https://pan.cstcloud.cn/unode/stor/downloadByUrl?downloadId=1.eyJidWNrZXQiOiJkZWZhdWx0IiwibGVuIjo0MTE0MCwic2l6ZSI6NDExNDAsInBvcyI6MCwibmFtZSI6IkJOX0F0bGFzXzI0Nl8ybW0ubmlpLmd6IiwiY3RpbWUiOjE3NzkyMTEwMjEsImtleSI6InNjMVZPVUdlcHpLa2RDSEZZX2hnMEZPUXp1MEFBS0MwIiwiYWdlIjo4NjQwMCwicGFydE9uZSI6eyJzaXplIjo0MTE0MCwiZm4iOiJNZlR4UXRlSFF6Zy0wLTQxMTQwIiwiY3JjMzIiOjI5ODMzMzA0OTYsImJpZCI6MSwiY2lkIjoxfX0.1577558658"
        
        labels_url = "https://pan.cstcloud.cn/unode/stor/downloadByUrl?downloadId=1.eyJidWNrZXQiOiJkZWZhdWx0IiwibGVuIjo1ODAyLCJzaXplIjo1ODAyLCJwb3MiOjAsIm5hbWUiOiJCTl9BdGxhc18yNDZfTFVULnR4dCIsImN0aW1lIjoxNzc5MjE1ODk1LCJrZXkiOiJ1bGV4dG1Kd0hJeGNjdVFDZWwzdTZnUVJXUThBQUJhcSIsImFnZSI6ODY0MDAsInBhcnRPbmUiOnsic2l6ZSI6NTgwMiwiZm4iOiJoa194MmRaLVFYZy0wLTU4MDIiLCJjcmMzMiI6ODk4MzQwOTA0LCJiaWQiOjEsImNpZCI6MX19.49470083"
        
        # Download atlas file if not exists
        if not atlas_file.exists():
            logger.info(f"Downloading Brainnetome atlas from {atlas_url}")
            try:
                download_file(atlas_url, atlas_file, "Brainnetome atlas")
            except Exception as e:
                logger.error(f"Failed to download Brainnetome atlas: {e}")
                raise RuntimeError(
                    f"Could not download Brainnetome atlas. Please download manually from "
                    f"https://atlas.brainnetome.org/download.html and place "
                    f"BN_Atlas_246_*mm.nii.gz in {cache_dir}"
                )
        
        # Download labels file if not exists
        if not labels_file.exists():
            logger.info(f"Downloading Brainnetome labels from {labels_url}")
            try:
                download_file(labels_url, labels_file, "Brainnetome labels")

                labels = pd.read_csv(labels_file, sep=' ', index_col=0, 
                                     names=['label', 1, 2, 3, 4]).label.to_list()
                labels[0] = "Background"
            except Exception as e:
                logger.error(f"Failed to download Brainnetome labels: {e}")
                # Generate default labels if download fails
                logger.warning("Generating default region labels")
                atlas_img = nib.load(atlas_file)
                atlas_data = atlas_img.get_fdata()
                n_regions = len(np.unique(atlas_data)) - 1  # Subtract background
                labels = [f"Region_{i+1}" for i in range(n_regions)]
                
        else:
            # Read labels from existing file
            labels = pd.read_csv(labels_file, sep=' ', index_col=0, 
                                 names=['label', 1, 2, 3, 4]).label.to_list()
            labels[0] = "Background"
        
        # Load atlas image
        atlas_img = nib.load(atlas_file)
        
        # Create atlas data object
        class AtlasData:
            def __init__(self, maps, labels):
                self.maps = maps
                self.labels = labels
        
        return AtlasData(atlas_img, labels)