"""Helper functions for the denoising pipeline."""

import logging
from pathlib import Path
from nilearn.interfaces.fmriprep import load_confounds
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

def create_confounds_strategy(image_path: str, strategy: dict) -> None:
    """Create confounds strategy from image path.

    Args:
        image_path: Path to image.

    Returns:
        None
    """
    df, _ = load_confounds(image_path, **strategy)
    for i in df.columns:
        print(f'    - "{i}"')


def download_file(url: str, destination: Path, description: str = "file") -> None:
    """Download a file with progress bar.

    Args:
        url: URL to download from.
        destination: Path to save the file.
        description: Description for progress bar.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    with open(destination, 'wb') as f, tqdm(
        desc=description,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
