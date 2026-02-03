#!/usr/bin/env python3
"""Multi-day replication runner.

Runs the market forensics pipeline on multiple dates specified in config,
outputting results to separate directories per date.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_dates_config(config_path: str) -> dict:
    """Load replication dates config."""
    with open(config_path) as f:
        return json.load(f)


def run_pipeline_for_date(
    date: str,
    base_config: str,
    canonical_base: str,
    output_base: str,
    verbose: bool = True,
) -> bool:
    """Run the pipeline for a single date.

    Args:
        date: Date in YYYY-MM-DD format
        base_config: Path to base config file
        canonical_base: Base path for canonical data
        output_base: Base output directory

    Returns:
        True if successful, False otherwise
    """
    data_dir = os.path.join(canonical_base, date)
    trades_path = os.path.join(data_dir, "trades.csv")
    tob_path = os.path.join(data_dir, "tob.csv")
    output_dir = os.path.join(output_base, date)

    # Validate data exists
    if not os.path.exists(trades_path):
        print(f"ERROR: Trades file not found: {trades_path}", file=sys.stderr)
        return False
    if not os.path.exists(tob_path):
        print(f"ERROR: TOB file not found: {tob_path}", file=sys.stderr)
        return False

    # Build command
    cmd = [
        sys.executable,
        "-m", "market_forensics.run",
        "--config", base_config,
        "--trades", trades_path,
        "--tob", tob_path,
        "--output", output_dir,
    ]
    if not verbose:
        cmd.append("--quiet")

    if verbose:
        print(f"\n{'='*60}")
        print(f"Running pipeline for {date}")
        print(f"  Data: {data_dir}")
        print(f"  Output: {output_dir}")
        print(f"{'='*60}")

    # Run pipeline
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    result = subprocess.run(cmd, env=env, cwd=str(REPO_ROOT))

    if result.returncode != 0:
        print(f"ERROR: Pipeline failed for {date}", file=sys.stderr)
        return False

    return True


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run market forensics pipeline on multiple dates."
    )
    parser.add_argument(
        "--dates-config",
        default="config/replication_dates.json",
        help="Path to JSON file listing dates to process",
    )
    parser.add_argument(
        "--base-config",
        default="config/default.json",
        help="Path to base pipeline config file",
    )
    parser.add_argument(
        "--dates",
        nargs="*",
        help="Specific dates to run (overrides config file)",
    )
    parser.add_argument(
        "--output-base",
        default="outputs",
        help="Base output directory (results go to {output-base}/{date}/)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()

    # Load dates config
    dates_config = load_dates_config(args.dates_config)
    canonical_base = dates_config.get("canonical_base_path", "data/")

    # Determine which dates to process
    if args.dates:
        dates = args.dates
    else:
        dates = dates_config.get("dates", [])

    if not dates:
        print("ERROR: No dates specified", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Replication run: {len(dates)} dates")
        print(f"Dates: {', '.join(dates)}")
        print(f"Canonical data base: {canonical_base}")
        print(f"Output base: {args.output_base}")

    # Run pipeline for each date
    results = {}
    for date in dates:
        success = run_pipeline_for_date(
            date=date,
            base_config=args.base_config,
            canonical_base=canonical_base,
            output_base=args.output_base,
            verbose=not args.quiet,
        )
        results[date] = "success" if success else "failed"

    # Summary
    if not args.quiet:
        print(f"\n{'='*60}")
        print("Replication Summary")
        print(f"{'='*60}")
        for date, status in results.items():
            print(f"  {date}: {status}")

    # Return non-zero if any failed
    if "failed" in results.values():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
