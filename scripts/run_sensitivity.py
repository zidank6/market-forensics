#!/usr/bin/env python3
"""Threshold sensitivity analysis runner.

Runs the market forensics pipeline with varying price_shock_threshold_pct
to check if ordering results are stable across threshold choices.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def create_config_with_threshold(base_config_path: str, threshold: float) -> str:
    """Create a temporary config file with modified threshold.

    Args:
        base_config_path: Path to base config file
        threshold: New price_shock_threshold_pct value

    Returns:
        Path to temporary config file
    """
    with open(base_config_path) as f:
        config = json.load(f)

    # Modify threshold
    if "event_detection" not in config:
        config["event_detection"] = {}
    config["event_detection"]["price_shock_threshold_pct"] = threshold

    # Write to temp file
    fd, temp_path = tempfile.mkstemp(suffix=".json", prefix=f"config_threshold_{threshold}_")
    with os.fdopen(fd, "w") as f:
        json.dump(config, f, indent=2)

    return temp_path


def run_pipeline_with_threshold(
    threshold: float,
    date: str,
    base_config: str,
    canonical_base: str,
    output_dir: str,
    verbose: bool = True,
) -> bool:
    """Run the pipeline with a specific threshold.

    Args:
        threshold: price_shock_threshold_pct value
        date: Date to run on (YYYY-MM-DD)
        base_config: Path to base config file
        canonical_base: Base path for canonical data
        output_dir: Output directory for this run

    Returns:
        True if successful, False otherwise
    """
    data_dir = os.path.join(canonical_base, date)
    trades_path = os.path.join(data_dir, "trades.csv")
    tob_path = os.path.join(data_dir, "tob.csv")

    # Validate data exists
    if not os.path.exists(trades_path):
        print(f"ERROR: Trades file not found: {trades_path}", file=sys.stderr)
        return False

    # Create temp config with modified threshold
    temp_config = create_config_with_threshold(base_config, threshold)

    try:
        # Build command
        cmd = [
            sys.executable,
            "-m", "market_forensics.run",
            "--config", temp_config,
            "--trades", trades_path,
            "--tob", tob_path,
            "--output", output_dir,
        ]
        if not verbose:
            cmd.append("--quiet")

        if verbose:
            print(f"\n{'='*60}")
            print(f"Running with threshold={threshold}%")
            print(f"  Data: {data_dir}")
            print(f"  Output: {output_dir}")
            print(f"{'='*60}")

        # Run pipeline
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")

        result = subprocess.run(cmd, env=env, cwd=str(REPO_ROOT))

        if result.returncode != 0:
            print(f"ERROR: Pipeline failed for threshold={threshold}", file=sys.stderr)
            return False

        return True
    finally:
        # Clean up temp config
        if os.path.exists(temp_config):
            os.remove(temp_config)


def count_orderings(output_dir: str) -> dict:
    """Count ordering classifications from a pipeline run."""
    orderings_path = os.path.join(output_dir, "metrics", "event_orderings.csv")
    summary_path = os.path.join(output_dir, "run_summary.json")

    # Get event count from summary
    events_detected = 0
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            summary = json.load(f)
            events_detected = len(summary.get("events", []))

    # Count classifications
    counts = {
        "events_detected": events_detected,
        "windows_extracted": 0,
        "liquidity_first": 0,
        "price_first": 0,
        "volume_first": 0,
    }

    if not os.path.exists(orderings_path):
        return counts

    with open(orderings_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts["windows_extracted"] += 1
            classification = row.get("classification", "").lower()
            if "liquidity" in classification:
                counts["liquidity_first"] += 1
            elif "price" in classification:
                counts["price_first"] += 1
            elif "volume" in classification:
                counts["volume_first"] += 1

    return counts


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run pipeline with varying thresholds for sensitivity analysis."
    )
    parser.add_argument(
        "--base-config",
        default="config/default.json",
        help="Path to base pipeline config file",
    )
    parser.add_argument(
        "--dates-config",
        default="config/replication_dates.json",
        help="Path to JSON file listing available dates",
    )
    parser.add_argument(
        "--date",
        help="Specific date to run on (default: first date from dates-config)",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=[0.4, 0.5, 0.6],
        help="Threshold values to test (default: 0.4 0.5 0.6)",
    )
    parser.add_argument(
        "--output-base",
        default="outputs",
        help="Base output directory",
    )
    parser.add_argument(
        "--output",
        default="outputs/sensitivity_summary.csv",
        help="Path for output summary CSV",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()

    # Load dates config to get canonical path and default date
    with open(args.dates_config) as f:
        dates_config = json.load(f)

    canonical_base = dates_config.get("canonical_base_path", "data/")
    available_dates = dates_config.get("dates", [])

    # Determine date to use
    date = args.date
    if not date:
        if available_dates:
            date = available_dates[0]
        else:
            print("ERROR: No date specified and none in config", file=sys.stderr)
            return 1

    if not args.quiet:
        print(f"Sensitivity analysis on date: {date}")
        print(f"Thresholds: {args.thresholds}")

    # Run pipeline for each threshold
    results = []
    for threshold in args.thresholds:
        output_dir = os.path.join(args.output_base, f"sensitivity_{threshold}")

        success = run_pipeline_with_threshold(
            threshold=threshold,
            date=date,
            base_config=args.base_config,
            canonical_base=canonical_base,
            output_dir=output_dir,
            verbose=not args.quiet,
        )

        if success:
            counts = count_orderings(output_dir)
            results.append({
                "threshold_pct": threshold,
                "date": date,
                **counts,
            })
        else:
            results.append({
                "threshold_pct": threshold,
                "date": date,
                "events_detected": -1,
                "windows_extracted": -1,
                "liquidity_first": -1,
                "price_first": -1,
                "volume_first": -1,
            })

    # Write summary CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "threshold_pct",
        "date",
        "events_detected",
        "windows_extracted",
        "liquidity_first",
        "price_first",
        "volume_first",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if not args.quiet:
        print(f"\nSummary written to: {output_path}")
        print("\nSensitivity Results:")
        print(f"{'Threshold':<12} {'Events':<8} {'Windows':<10} {'Liq-1st':<10} {'Price-1st':<10} {'Vol-1st':<10}")
        print("-" * 60)
        for r in results:
            print(f"{r['threshold_pct']:<12} {r['events_detected']:<8} {r['windows_extracted']:<10} "
                  f"{r['liquidity_first']:<10} {r['price_first']:<10} {r['volume_first']:<10}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
