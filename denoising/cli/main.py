"""Command-line interface for fMRI denoising pipeline."""

import argparse
import logging
import sys
from pathlib import Path

from denoising.config.config_loader import load_config, setup_logging
from denoising.core.pipeline import DenoisingPipeline
from denoising.io.file_handler import validate_file_exists


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Denoise BOLD fMRI data and extract time-series using nilearn",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--bold",
        type=str,
        help="Path to BOLD NIfTI file (single subject mode)",
    )
    group.add_argument(
        "--subjects-list",
        type=str,
        help="Path to text file with subject info (batch mode)",
    )

    parser.add_argument(
        "--confounds",
        type=str,
        help="Path to confounds TSV file (required with --bold)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory (overrides config)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def run_single_subject(
    config_path: str,
    bold_path: str,
    confounds_path: str,
    output_dir: str = None,
    verbose: bool = False,
) -> str:
    """Process a single subject.

    Args:
        config_path: Path to config file.
        bold_path: Path to BOLD file.
        confounds_path: Path to confounds file.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        Output file path.
    """
    config = load_config(config_path)
    if verbose:
        config.logging.level = "DEBUG"

    setup_logging(config)

    validate_file_exists(bold_path)
    validate_file_exists(confounds_path)

    pipeline = DenoisingPipeline(config)
    return pipeline.process_subject(bold_path, confounds_path, output_dir)


def run_batch(
    config_path: str,
    subjects_list_path: str,
    output_dir: str = None,
    verbose: bool = False,
) -> list:
    """Process multiple subjects from a list file.

    Args:
        config_path: Path to config file.
        subjects_list_path: Path to subjects list file.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        List of output file paths.
    """
    config = load_config(config_path)
    if verbose:
        config.logging.level = "DEBUG"

    setup_logging(config)

    subjects = []
    with open(subjects_list_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                subjects.append({"bold_path": parts[0].strip(), "confounds_path": parts[1].strip()})

    pipeline = DenoisingPipeline(config)
    return pipeline.process_batch(subjects, output_dir)


def main():
    """Main entry point for CLI."""
    args = parse_args()

    try:
        if args.bold:
            if not args.confounds:
                print("Error: --confounds required with --bold", file=sys.stderr)
                sys.exit(1)

            output = run_single_subject(
                args.config,
                args.bold,
                args.confounds,
                args.output_dir,
                args.verbose,
            )
            print(f"Output: {output}")

        else:
            outputs = run_batch(
                args.config,
                args.subjects_list,
                args.output_dir,
                args.verbose,
            )
            print(f"Processed {len(outputs)} subjects")
            for i, out in enumerate(outputs):
                if out:
                    print(f"  {i+1}. {out}")
                else:
                    print(f"  {i+1}. Failed")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()