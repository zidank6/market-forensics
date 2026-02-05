#!/usr/bin/env python3
"""Multi-day multi-asset pipeline runner for Market Forensics v2.

Runs the market forensics pipeline across all dates and assets defined
in config/dates.json, outputting results to outputs/v2/{asset}/{date}/.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_dates_manifest(manifest_path: str) -> dict:
    """Load the dates manifest from config/dates.json.

    Args:
        manifest_path: Path to the dates.json file.

    Returns:
        Dictionary with asset names as keys and list of dates as values.

    Raises:
        FileNotFoundError: If manifest file does not exist.
        json.JSONDecodeError: If manifest is not valid JSON.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Dates manifest not found: {manifest_path}")

    with open(path) as f:
        return json.load(f)


def get_canonical_data_path(asset: str, date: str) -> Path:
    """Get the path to canonical data for an asset/date pair.

    Args:
        asset: Asset symbol (e.g., BTCUSDT, ETHUSDT)
        date: Date in YYYY-MM-DD format

    Returns:
        Path to the canonical data directory.
    """
    return REPO_ROOT / "data" / "binance" / "futures_um" / asset / "canonical" / date


def data_exists(asset: str, date: str) -> bool:
    """Check if canonical data exists for an asset/date pair.

    Args:
        asset: Asset symbol
        date: Date in YYYY-MM-DD format

    Returns:
        True if both trades.csv and tob.csv exist.
    """
    data_dir = get_canonical_data_path(asset, date)
    trades_path = data_dir / "trades.csv"
    tob_path = data_dir / "tob.csv"
    return trades_path.exists() and tob_path.exists()


def run_pipeline_for_pair(
    asset: str,
    date: str,
    base_config: str,
    output_base: str,
    verbose: bool = True,
) -> bool:
    """Run the pipeline for a single (asset, date) pair.

    Args:
        asset: Asset symbol (e.g., BTCUSDT)
        date: Date in YYYY-MM-DD format
        base_config: Path to base config file
        output_base: Base output directory (outputs will go to {base}/{asset}/{date}/)
        verbose: Whether to print progress messages

    Returns:
        True if successful, False otherwise.
    """
    data_dir = get_canonical_data_path(asset, date)
    trades_path = data_dir / "trades.csv"
    tob_path = data_dir / "tob.csv"
    output_dir = Path(output_base) / asset / date

    # Validate data exists
    if not trades_path.exists():
        if verbose:
            print(f"  WARNING: Trades file not found: {trades_path}", file=sys.stderr)
        return False
    if not tob_path.exists():
        if verbose:
            print(f"  WARNING: TOB file not found: {tob_path}", file=sys.stderr)
        return False

    # Build command
    cmd = [
        sys.executable,
        "-m", "market_forensics.run",
        "--config", base_config,
        "--trades", str(trades_path),
        "--tob", str(tob_path),
        "--output", str(output_dir),
    ]
    if not verbose:
        cmd.append("--quiet")

    if verbose:
        print(f"\n{'='*60}")
        print(f"Running pipeline: {asset} / {date}")
        print(f"  Data: {data_dir}")
        print(f"  Output: {output_dir}")
        print(f"{'='*60}")

    # Run pipeline
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    result = subprocess.run(cmd, env=env, cwd=str(REPO_ROOT))

    if result.returncode != 0:
        if verbose:
            print(f"  ERROR: Pipeline failed for {asset}/{date}", file=sys.stderr)
        return False

    return True


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run market forensics v2 pipeline on multiple dates and assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on all dates/assets in manifest
  python scripts/run_v2_analysis.py

  # Run on specific assets only
  python scripts/run_v2_analysis.py --assets BTCUSDT

  # Run on specific dates only
  python scripts/run_v2_analysis.py --dates 2024-01-10 2024-01-11

  # Dry run to see what would be processed
  python scripts/run_v2_analysis.py --dry-run
        """,
    )
    parser.add_argument(
        "--manifest",
        default="config/dates.json",
        help="Path to dates manifest file (default: config/dates.json)",
    )
    parser.add_argument(
        "--base-config",
        default="config/default.json",
        help="Path to base pipeline config file (default: config/default.json)",
    )
    parser.add_argument(
        "--assets",
        nargs="*",
        help="Specific assets to run (overrides manifest, e.g., BTCUSDT ETHUSDT)",
    )
    parser.add_argument(
        "--dates",
        nargs="*",
        help="Specific dates to run (overrides manifest, e.g., 2024-01-10 2024-01-11)",
    )
    parser.add_argument(
        "--output-base",
        default="outputs/v2",
        help="Base output directory (default: outputs/v2)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without running",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    # Load dates manifest
    try:
        manifest = load_dates_manifest(args.manifest)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in manifest: {e}", file=sys.stderr)
        return 1

    # Determine which assets to process
    # Assets are keys that are uppercase (BTCUSDT, ETHUSDT) and have list values
    all_assets = [k for k, v in manifest.items() if isinstance(v, list) and k.isupper()]

    if args.assets:
        assets = [a for a in args.assets if a in all_assets]
        if not assets:
            print(f"ERROR: None of specified assets found in manifest", file=sys.stderr)
            print(f"  Available: {all_assets}", file=sys.stderr)
            return 1
    else:
        assets = all_assets

    # Build list of (asset, date) pairs to process
    pairs_to_process = []
    pairs_skipped = []

    for asset in assets:
        dates_for_asset = manifest.get(asset, [])

        # Filter dates if specified
        if args.dates:
            dates_for_asset = [d for d in dates_for_asset if d in args.dates]

        for date in dates_for_asset:
            if data_exists(asset, date):
                pairs_to_process.append((asset, date))
            else:
                pairs_skipped.append((asset, date))

    if verbose:
        print(f"Market Forensics v2 Analysis")
        print(f"{'='*60}")
        print(f"Manifest: {args.manifest}")
        print(f"Base config: {args.base_config}")
        print(f"Output base: {args.output_base}")
        print(f"Assets: {', '.join(assets)}")
        print(f"Pairs to process: {len(pairs_to_process)}")
        if pairs_skipped:
            print(f"Pairs skipped (missing data): {len(pairs_skipped)}")
            for asset, date in pairs_skipped:
                print(f"  WARNING: Skipping {asset}/{date} - data not found")

    if not pairs_to_process:
        print("ERROR: No (asset, date) pairs with data found", file=sys.stderr)
        return 1

    # Dry run mode
    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN - Would process:")
        print(f"{'='*60}")
        for asset, date in pairs_to_process:
            data_dir = get_canonical_data_path(asset, date)
            output_dir = Path(args.output_base) / asset / date
            print(f"  {asset}/{date}")
            print(f"    Data: {data_dir}")
            print(f"    Output: {output_dir}")
        return 0

    # Run pipeline for each pair
    results = {}
    for asset, date in pairs_to_process:
        key = f"{asset}/{date}"
        success = run_pipeline_for_pair(
            asset=asset,
            date=date,
            base_config=args.base_config,
            output_base=args.output_base,
            verbose=verbose,
        )
        results[key] = "success" if success else "failed"

    # Summary
    if verbose:
        print(f"\n{'='*60}")
        print("V2 Analysis Summary")
        print(f"{'='*60}")

        success_count = sum(1 for v in results.values() if v == "success")
        failed_count = sum(1 for v in results.values() if v == "failed")

        print(f"Total pairs processed: {len(results)}")
        print(f"  Success: {success_count}")
        print(f"  Failed: {failed_count}")

        if failed_count > 0:
            print(f"\nFailed pairs:")
            for key, status in results.items():
                if status == "failed":
                    print(f"  {key}")

    # Return non-zero if any failed
    if "failed" in results.values():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
