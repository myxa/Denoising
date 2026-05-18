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

Process a single subject:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --bold path/to/bold.nii.gz \
    --confounds path/to/confounds.tsv \
    --output-dir ./output
```

Process multiple subjects:

```bash
fmri-denoise \
    --config configs/default_config.yaml \
    --subjects-list subjects_list.txt \
    --output-dir ./output
```

The `subjects_list.txt` file should contain one subject per line:

```
path/to/subject1_bold.nii.gz,path/to/subject1_confounds.tsv
path/to/subject2_bold.nii.gz,path/to/subject2_confounds.tsv
```

### Python API

```python
from denoising import DenoisingPipeline
from denoising.config import load_config

# Load configuration
config = load_config("configs/default_config.yaml")

# Initialize pipeline
pipeline = DenoisingPipeline(config)

# Process single subject
output_file = pipeline.process_subject(
    bold_path="path/to/bold.nii.gz",
    confounds_path="path/to/confounds.tsv",
    output_dir="./output"
)

# Process multiple subjects
subjects = [
    {"bold_path": "path/to/sub1_bold.nii.gz", "confounds_path": "path/to/sub1_confounds.tsv"},
    {"bold_path": "path/to/sub2_bold.nii.gz", "confounds_path": "path/to/sub2_confounds.tsv"},
]
outputs = pipeline.process_batch(subjects, output_dir="./output")
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
  low_pass: 0.1          # Low-pass filter cutoff (Hz)
  high_pass: 0.01        # High-pass filter cutoff (Hz)
  t_r: null              # Repetition time (s), auto-detected if null
```

#### Confounds

```yaml
confounds:
  strategy: "custom"      # Selection strategy: custom, simple, scrubbing
  columns:                # Confounds to select (for custom strategy)
    - "csf"
    - "white_matter"
    - "global_signal"
    - "trans_x"
    - "trans_y"
    - "trans_z"
    - "rot_x"
    - "rot_y"
    - "rot_z"
  derivatives:            # Derivatives to compute
    csf: ["power2"]
    white_matter: ["power2"]
  fd_threshold: null      # Framewise displacement threshold (for scrubbing)
```

#### Output

```yaml
output:
  directory: "./output"
  naming_pattern: "{subject}_{session}_{task}_{run}_atlas-{atlas_name}.csv"
  include_metadata: true
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