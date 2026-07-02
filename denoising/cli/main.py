"""Command-line interface for fMRI denoising pipeline."""

import argparse
import logging
import sys
from typing import List, Optional

from denoising.config.config_loader import load_config, setup_logging
from denoising.core.pipeline import DenoisingPipeline
from denoising.io.file_handler import BIDSFileLoader


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

    parser.add_argument(
        "--bids-path",
        type=str,
        required=True,
        help="Path to BIDS dataset root",
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
            # Handle 'all' special value: argparse with nargs='+' wraps it as ['all']
            subjects = "all" if args.subjects == ["all"] else args.subjects
            outputs = run_bids_batch(
                args.config,
                args.bids_path,
                subjects,
                args.task,
                args.space,
                args.desc,
                args.output_dir,
                args.verbose,
            )
            print(f"Processed {len(outputs)} files")
        else:
            print("Error: --subject or --subjects required", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()