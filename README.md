# fMRI Denoising Pipeline

A Python package for denoising BOLD fMRI data and extracting time-series using nilearn. Supports both CLI and Jupyter notebook usage with flexible configuration through YAML files.

## Features

- **Atlas-based time-series extraction** using Schaefer 2018 atlas
- **Flexible denoising** with configurable smoothing, detrending, standardization, and filtering
- **Confounds handling** with custom, simple, and scrubbing strategies
- **Batch processing** support for multiple subjects
- **BIDS-compliant** output naming
- **CLI and Python API** for flexible usage

## Installation

### From source

```bash
git clone <repository-url>
cd Denoising
pip install -e .
```

### Using requirements.txt

```bash
pip install -r requirements.txt
```

### With optional dependencies

```bash
pip install -e ".[dev,jupyter]"
```

## Quick Start

### Command Line Interface

The CLI supports three modes: **BIDS mode** (recommended), **legacy single subject**, and **legacy batch**.

#### BIDS Mode (Recommended)

Process a single subject from a BIDS dataset:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --bids-path /path/to/bids/dataset \
    --subject 01 \
    --output-dir ./output
```

Process multiple subjects from a BIDS dataset:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --bids-path /path/to/bids/dataset \
    --subjects 01 02 03 \
    --task rest \
    --output-dir ./output
```

Process all subjects from a BIDS dataset:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --bids-path /path/to/bids/dataset \
    --subjects all \
    --task rest \
    --output-dir ./output
```

BIDS filtering options:
- `--task`: Task name (e.g., 'rest')
- `--space`: Space (default: MNI152NLin2009cAsym)
- `--desc`: Description (default: preproc)

#### Legacy Single Subject Mode

Process a single subject (confounds auto-detected from BIDS naming):

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --bold path/to/sub-01_task-rest_bold.nii.gz \
    --output-dir ./output
```

#### Legacy Batch Mode

Process multiple subjects from a list file:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --subjects-list subjects_list.txt \
    --output-dir ./output
```

The `subjects_list.txt` file should contain one BOLD file path per line:

```
path/to/subject1_bold.nii.gz
path/to/subject2_bold.nii.gz
```

### Python API

```python
from denoising import DenoisingPipeline
from denoising.config import load_config
from denoising.io.file_handler import BIDSFileLoader

# Load configuration
config = load_config("configs/default_config.yaml")

# Initialize pipeline
pipeline = DenoisingPipeline(config)

# Process single subject (confounds auto-detected)
timeseries = pipeline.process_subject(
    bold_path="path/to/sub-01_task-rest_bold.nii.gz",
    output_dir="./output"
)

# Process multiple subjects (legacy mode)
subjects = [
    {"bold_path": "path/to/sub1_bold.nii.gz"},
    {"bold_path": "path/to/sub2_bold.nii.gz"},
]
outputs = pipeline.process_batch(subjects, output_dir="./output")

# Process BIDS dataset
bids_loader = BIDSFileLoader("/path/to/bids/dataset")
subjects = ["01", "02", "03"]
outputs = pipeline.process_batch(subjects, output_dir="./output", bids_loader=bids_loader)
```

## Configuration

All parameters are configured through YAML files. See [`configs/default_config.yaml`](configs/default_config.yaml) for an example.

### Configuration Sections

#### Atlas

```yaml
atlas:
  name: "schaefer_2018"  # Atlas name
  resolution: 2           # Resolution in mm (1 or 2)
  n_regions: 400          # Number of brain regions
```

#### Denoising

```yaml
denoising:
  smoothing_fwhm: 6.0    # Spatial smoothing FWHM (mm)
  detrend: true          # Apply linear detrending
  standardize: "zscore"  # Standardization: zscore, psc, or false
  standardize_confounds: true  # Standardize confounds before regression
  low_pass: 0.1          # Low-pass filter cutoff (Hz)
  high_pass: 0.01        # High-pass filter cutoff (Hz)
  t_r: null              # Repetition time (s), auto-detected if null
```

#### Confounds

Uses nilearn's `load_confounds` format:

```yaml
confounds:
  strategy: ["motion", "compcor"]  # Confounds strategies to use
  motion: "basic"                  # Motion options: basic, derivatives, power2, full
  compcor: "anat_combined"         # CompCor options: anat_combined, anat_separated, temp_combined, temp_separated
  n_compcor: 5                     # Number of CompCor components
  global_signal: null              # Global signal: basic, derivatives, power2, full, or null
  high_pass: null                  # High-pass filter for confounds (Hz)
  low_pass: null                   # Low-pass filter for confounds (Hz)
  cosine: null                     # Cosine regressors: number or "full"
  scrub: null                      # Number of volumes to remove (scrubbing)
  fd_th: null                      # Framewise displacement threshold
  dvars_th: null                   # DVARS threshold
  tr: null                         # Repetition time for confounds (s)
```

#### BIDS Configuration

For BIDS mode file discovery:

```yaml
bids:
  dataset_path: null      # Path to BIDS dataset root (required for BIDS mode)
  task: null              # Task name (e.g., 'rest')
  space: "MNI152NLin2009cAsym"  # Space (e.g., 'MNI152NLin2009cAsym')
  desc: "preproc"         # Description (e.g., 'preproc')
  datatype: "func"        # Data type
  extension: "nii.gz"     # File extension
```

#### Output

```yaml
output:
  directory: "./output"
  naming_pattern: "sub-{subject}_ses-{session}_task-{task}_run-{run}_atlas-{atlas_name}.csv"
```

Output is organized in BIDS-compliant directory structure:
```
output/
└── sub-01/
    └── ses-1/
        └── time-series/
            └── sub-01_ses-1_task-rest_run-1_atlas-schaefer_2018.csv
```

## Project Structure

```
Denoising/
├── denoising/                    # Main package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core processing modules
│   │   ├── atlas.py              # Atlas fetching
│   │   ├── denoiser.py           # Denoising operations
│   │   ├── extractor.py          # Time-series extraction
│   │   └── pipeline.py           # Main pipeline orchestrator
│   ├── io/                       # Input/output handling
│   │   ├── file_handler.py       # File operations
│   │   └── confounds.py          # Confounds loading/selection
│   ├── cli/                      # Command-line interface
│   │   └── main.py               # CLI entry point
│   └── utils/                    # Utility functions
├── configs/                      # Configuration files
│   └── default_config.yaml       # Default parameters
├── notebooks/                    # Jupyter notebooks
│   └── example_usage.ipynb       # Usage examples
├── tests/                        # Test suite
├── pyproject.toml                # Project metadata
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Output Format

The output CSV file contains:

- **Rows**: Time points (TRs)
- **Columns**: Brain regions (named from atlas)
- **Metadata header**: Comments with timepoints and regions count

Example:
```
# Timepoints: 200
# Regions: 400
# Columns: brain regions
7Networks_LH_VisCent_ExStr_1,7Networks_LH_VisCent_ExStr_2,...
0.123,0.456,...
0.234,0.567,...
...
```

## Dependencies

- nilearn >= 0.10.0
- numpy >= 1.23.0
- pandas >= 1.5.0
- pyyaml >= 6.0
- pydantic >= 2.0.0
- nibabel >= 5.0.0
- scikit-learn >= 1.2.0
- tqdm >= 4.65.0

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please ensure code follows PEP 8 style conventions and includes tests.

## Citation

If you use this package in your research, please cite:

[Add citation information]