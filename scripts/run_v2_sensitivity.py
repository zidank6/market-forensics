#!/usr/bin/env python3
"""V2 threshold sensitivity analysis runner.

Runs the market forensics pipeline across all v2 (asset, date) pairs with
varying price_shock_threshold_pct values to verify results are robust.

Outputs:
- outputs/sensitivity.csv: threshold, n_events, pct_liquidity_first
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
from typing import List, Tuple

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_dates_manifest(manifest_path: str) -> dict:
    """Load dates manifest from config/dates.json."""
    with open(manifest_path) as f:
        return json.load(f)


def get_canonical_data_path(asset: str, date: str) -> Path:
    """Get path to canonical data for asset/date pair."""
    return REPO_ROOT / "data" / "binance" / "futures_um" / asset / "canonical" / date


def data_exists(asset: str, date: str) -> bool:
    """Check if canonical data exists for asset/date pair."""
    data_dir = get_canonical_data_path(asset, date)
    return (data_dir / "trades.csv").exists() and (data_dir / "tob.csv").exists()


def get_available_pairs(manifest: dict) -> List[Tuple[str, str]]:
    """Get list of (asset, date) pairs with available data."""
    pairs = []
    all_assets = [k for k, v in manifest.items() if isinstance(v, list) and k.isupper()]

    for asset in all_assets:
        for date in manifest.get(asset, []):
            if data_exists(asset, date):
                pairs.append((asset, date))

    return pairs


def create_config_with_threshold(base_config_path: str, threshold: float) -> str:
    """Create a temp config file with modified threshold.

    Args:
        base_config_path: Path to base config file
        threshold: New price_shock_threshold_pct value

    Returns:
        Path to temporary config file
    """
    with open(base_config_path) as f:
        config = json.load(f)

    if "event_detection" not in config:
        config["event_detection"] = {}
    config["event_detection"]["price_shock_threshold_pct"] = threshold

    fd, temp_path = tempfile.mkstemp(suffix=".json", prefix=f"config_{threshold}_")
    with os.fdopen(fd, "w") as f:
        json.dump(config, f, indent=2)

    return temp_path


def run_pipeline_for_pair(
    asset: str,
    date: str,
    config_path: str,
    output_dir: str,
    verbose: bool = True,
) -> bool:
    """Run pipeline for a single (asset, date) pair."""
    data_dir = get_canonical_data_path(asset, date)
    trades_path = data_dir / "trades.csv"
    tob_path = data_dir / "tob.csv"

    cmd = [
        sys.executable,
        "-m", "market_forensics.run",
        "--config", config_path,
        "--trades", str(trades_path),
        "--tob", str(tob_path),
        "--output", output_dir,
        "--quiet",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    result = subprocess.run(cmd, env=env, cwd=str(REPO_ROOT), capture_output=True)
    return result.returncode == 0


def count_orderings_from_dir(output_dir: str) -> Tuple[int, int]:
    """Count total events and liquidity-first events from output directory.

    Returns:
        Tuple of (n_events, n_liquidity_first)
    """
    orderings_path = Path(output_dir) / "metrics" / "event_orderings.csv"

    if not orderings_path.exists():
        return (0, 0)

    n_events = 0
    n_liquidity_first = 0

    with open(orderings_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_events += 1
            classification = row.get("classification", "").lower()
            if "liquidity" in classification:
                n_liquidity_first += 1

    return (n_events, n_liquidity_first)


def run_sensitivity_for_threshold(
    threshold: float,
    pairs: List[Tuple[str, str]],
    base_config: str,
    output_base: str,
    verbose: bool = True,
) -> Tuple[int, int]:
    """Run pipeline with specific threshold across all pairs.

    Returns:
        Tuple of (total_events, total_liquidity_first)
    """
    temp_config = create_config_with_threshold(base_config, threshold)

    total_events = 0
    total_liquidity_first = 0

    try:
        for asset, date in pairs:
            output_dir = str(Path(output_base) / f"sens_{threshold}" / asset / date)

            success = run_pipeline_for_pair(
                asset=asset,
                date=date,
                config_path=temp_config,
                output_dir=output_dir,
                verbose=False,
            )

            if success:
                n_events, n_liq_first = count_orderings_from_dir(output_dir)
                total_events += n_events
                total_liquidity_first += n_liq_first

        return (total_events, total_liquidity_first)

    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run v2 threshold sensitivity analysis across all dates and assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default thresholds
  python scripts/run_v2_sensitivity.py

  # Custom thresholds
  python scripts/run_v2_sensitivity.py --thresholds 0.3 0.4 0.5

  # Dry run to see what would be processed
  python scripts/run_v2_sensitivity.py --dry-run
        """,
    )
    parser.add_argument(
        "--manifest",
        default="config/dates.json",
        help="Path to dates manifest (default: config/dates.json)",
    )
    parser.add_argument(
        "--base-config",
        default="config/default.json",
        help="Path to base config file (default: config/default.json)",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=[0.3, 0.4, 0.5, 0.6, 0.7],
        help="Threshold values to test (default: 0.3 0.4 0.5 0.6 0.7)",
    )
    parser.add_argument(
        "--output-base",
        default="outputs/v2_sensitivity",
        help="Base directory for intermediate outputs (default: outputs/v2_sensitivity)",
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/sensitivity.csv",
        help="Path for output summary CSV (default: outputs/sensitivity.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without running",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    # Load manifest and get available pairs
    try:
        manifest = load_dates_manifest(args.manifest)
    except FileNotFoundError:
        print(f"ERROR: Manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    pairs = get_available_pairs(manifest)

    if not pairs:
        print("ERROR: No (asset, date) pairs with data found", file=sys.stderr)
        return 1

    if verbose:
        print(f"V2 Threshold Sensitivity Analysis")
        print(f"{'='*60}")
        print(f"Manifest: {args.manifest}")
        print(f"Base config: {args.base_config}")
        print(f"Thresholds: {args.thresholds}")
        print(f"(Asset, Date) pairs: {len(pairs)}")
        print(f"Output: {args.output}")

    if args.dry_run:
        print(f"\nDRY RUN - Would test {len(args.thresholds)} thresholds on {len(pairs)} pairs")
        print(f"Thresholds: {args.thresholds}")
        print(f"\nPairs:")
        for asset, date in pairs[:10]:
            print(f"  {asset}/{date}")
        if len(pairs) > 10:
            print(f"  ... and {len(pairs) - 10} more")
        return 0

    # Run sensitivity analysis
    results = []
    for threshold in args.thresholds:
        if verbose:
            print(f"\nRunning threshold {threshold}% on {len(pairs)} pairs...")

        n_events, n_liq_first = run_sensitivity_for_threshold(
            threshold=threshold,
            pairs=pairs,
            base_config=args.base_config,
            output_base=args.output_base,
            verbose=verbose,
        )

        pct_liq_first = 100.0 * n_liq_first / n_events if n_events > 0 else 0.0

        results.append({
            "threshold": threshold,
            "n_events": n_events,
            "pct_liquidity_first": round(pct_liq_first, 2),
        })

        if verbose:
            print(f"  Events: {n_events}, Liquidity-first: {pct_liq_first:.1f}%")

    # Write output CSV
    output_path = REPO_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["threshold", "n_events", "pct_liquidity_first"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Sensitivity Analysis Results")
        print(f"{'='*60}")
        print(f"{'Threshold':<12} {'N Events':<12} {'% Liq-First':<15}")
        print("-" * 40)
        for r in results:
            print(f"{r['threshold']:<12} {r['n_events']:<12} {r['pct_liquidity_first']:<15.1f}")
        print()
        print(f"Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
