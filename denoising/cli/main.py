"""Command-line interface for fMRI denoising pipeline."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from denoising.config.config_loader import load_config, setup_logging
from denoising.core.pipeline import DenoisingPipeline
from denoising.io.file_handler import validate_file_exists, BIDSFileLoader


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
        "--bids-path",
        type=str,
        help="Path to BIDS dataset root (BIDS mode)",
    )
    group.add_argument(
        "--bold",
        type=str,
        help="Path to BOLD NIfTI file (single subject mode, legacy)",
    )
    group.add_argument(
        "--subjects-list",
        type=str,
        help="Path to text file with subject info (batch mode, legacy)",
    )

    # BIDS mode arguments
    parser.add_argument(
        "--subject",
        type=str,
        help="Subject ID for BIDS mode (e.g., '01')",
    )
    parser.add_argument(
        "--subjects",
        type=str,
        nargs='+',
        help="List of subject IDs for BIDS batch mode",
    )

    # BIDS filtering arguments
    parser.add_argument(
        "--task",
        type=str,
        help="Task name for BIDS query (e.g., 'rest')",
    )
    parser.add_argument(
        "--space",
        type=str,
        default="MNI152NLin2009cAsym",
        help="Space for BIDS query (default: MNI152NLin2009cAsym)",
    )
    parser.add_argument(
        "--desc",
        type=str,
        default="preproc",
        help="Description for BIDS query (default: preproc)",
    )

    # Legacy mode arguments
    parser.add_argument(
        "--confounds",
        type=str,
        help="Path to confounds TSV file (required with --bold in legacy mode)",
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
    output_dir: str = None,
    verbose: bool = False,
) -> tuple:
    """Process a single subject (legacy mode).

    Args:
        config_path: Path to config file.
        bold_path: Path to BOLD file.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        Tuple of (timeseries DataFrame, output path).
    """
    config = load_config(config_path)
    if verbose:
        config.logging.level = "DEBUG"

    setup_logging(config)

    validate_file_exists(bold_path)

    pipeline = DenoisingPipeline(config)
    return pipeline.process_subject(bold_path, output_dir)


def run_batch(
    config_path: str,
    subjects_list_path: str,
    output_dir: str = None,
    verbose: bool = False,
) -> list:
    """Process multiple subjects from a list file (legacy mode).

    Args:
        config_path: Path to config file.
        subjects_list_path: Path to subjects list file.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        List of tuples (timeseries DataFrame, output path).
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
            if len(parts) >= 1:
                subjects.append({"bold_path": parts[0].strip()})

    pipeline = DenoisingPipeline(config)
    return pipeline.process_batch(subjects, output_dir)


def run_bids_single(
    config_path: str,
    bids_path: str,
    subject: str,
    task: Optional[str] = None,
    space: Optional[str] = None,
    desc: Optional[str] = None,
    output_dir: str = None,
    verbose: bool = False,
) -> list:
    """Process a single subject using BIDS dataset.

    Args:
        config_path: Path to config file.
        bids_path: Path to BIDS dataset root.
        subject: Subject ID.
        task: Task name.
        space: Space.
        desc: Description.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        List of tuples (timeseries DataFrame, output path).
    """
    config = load_config(config_path)
    if verbose:
        config.logging.level = "DEBUG"

    setup_logging(config)

    # Create BIDS loader
    bids_loader = BIDSFileLoader(bids_path)

    # Update config with BIDS parameters from CLI
    if task is not None:
        config.bids.task = task
    if space is not None:
        config.bids.space = space
    if desc is not None:
        config.bids.desc = desc

    pipeline = DenoisingPipeline(config)
    return pipeline.process_batch([subject], output_dir, bids_loader)


def run_bids_batch(
    config_path: str,
    bids_path: str,
    subjects: List[str],
    task: Optional[str] = None,
    space: Optional[str] = None,
    desc: Optional[str] = None,
    output_dir: str = None,
    verbose: bool = False,
) -> list:
    """Process multiple subjects using BIDS dataset.

    Args:
        config_path: Path to config file.
        bids_path: Path to BIDS dataset root.
        subjects: List of subject IDs.
        task: Task name.
        space: Space.
        desc: Description.
        output_dir: Output directory.
        verbose: Enable verbose logging.

    Returns:
        List of tuples (timeseries DataFrame, output path).
    """
    config = load_config(config_path)
    if verbose:
        config.logging.level = "DEBUG"

    setup_logging(config)

    # Create BIDS loader
    bids_loader = BIDSFileLoader(bids_path)

    # Update config with BIDS parameters from CLI
    if task is not None:
        config.bids.task = task
    if space is not None:
        config.bids.space = space
    if desc is not None:
        config.bids.desc = desc

    pipeline = DenoisingPipeline(config)
    return pipeline.process_batch(subjects, output_dir, bids_loader)


def main():
    """Main entry point for CLI."""
    args = parse_args()

    try:
        if args.bids_path:
            # BIDS mode
            if args.subject:
                # Single subject
                outputs = run_bids_single(
                    args.config,
                    args.bids_path,
                    args.subject,
                    args.task,
                    args.space,
                    args.desc,
                    args.output_dir,
                    args.verbose,
                )
                print(f"Processed {len(outputs)} files")
                for i, out in enumerate(outputs):
                    if out:
                        print(f"  {i+1}. {out[1]}")
                    else:
                        print(f"  {i+1}. Failed")
            elif args.subjects:
                # Batch mode
                outputs = run_bids_batch(
                    args.config,
                    args.bids_path,
                    args.subjects,
                    args.task,
                    args.space,
                    args.desc,
                    args.output_dir,
                    args.verbose,
                )
                print(f"Processed {len(outputs)} files")
            else:
                print("Error: --subject or --subjects required with --bids-path", file=sys.stderr)
                sys.exit(1)

        elif args.bold:
            # Legacy single subject mode
            output = run_single_subject(
                args.config,
                args.bold,
                args.output_dir,
                args.verbose,
            )
            print(f"Output: {output[1]}")

        else:
            # Legacy batch mode
            outputs = run_batch(
                args.config,
                args.subjects_list,
                args.output_dir,
                args.verbose,
            )
            print(f"Processed {len(outputs)} subjects")
            for i, out in enumerate(outputs):
                if out:
                    print(f"  {i+1}. {out[1]}")
                else:
                    print(f"  {i+1}. Failed")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()