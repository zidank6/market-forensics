#!/usr/bin/env python3
"""Aggregate v2 analysis results into a unified summary table.

Reads all event_orderings.csv files from outputs/v2/{asset}/{date}/metrics/
and produces a unified summary CSV at outputs/v2_summary.csv.
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime.

    Args:
        ts_str: ISO format timestamp string (may be None or empty).

    Returns:
        Datetime object or None if parsing fails.
    """
    if not ts_str or ts_str.strip() == "":
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_onset_seconds(
    event_ts: datetime, onset_ts: Optional[datetime]
) -> Optional[float]:
    """Compute onset time in seconds relative to event timestamp.

    Args:
        event_ts: Event timestamp.
        onset_ts: Onset timestamp (may be None).

    Returns:
        Seconds from event to onset, or None if onset not detected.
    """
    if onset_ts is None:
        return None
    delta = (onset_ts - event_ts).total_seconds()
    return round(delta, 3)


def find_ordering_files(v2_output_dir: Path) -> List[Tuple[str, str, Path]]:
    """Find all event_orderings.csv files in the v2 output directory.

    Args:
        v2_output_dir: Path to outputs/v2 directory.

    Returns:
        List of (asset, date, file_path) tuples.
    """
    results = []

    if not v2_output_dir.exists():
        return results

    # Iterate over asset directories
    for asset_dir in sorted(v2_output_dir.iterdir()):
        if not asset_dir.is_dir():
            continue
        asset = asset_dir.name

        # Iterate over date directories
        for date_dir in sorted(asset_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            date = date_dir.name

            # Check for event_orderings.csv
            orderings_file = date_dir / "metrics" / "event_orderings.csv"
            if orderings_file.exists():
                results.append((asset, date, orderings_file))

    return results


def process_ordering_file(
    asset: str, date: str, file_path: Path
) -> List[dict]:
    """Process a single event_orderings.csv file.

    Args:
        asset: Asset symbol (e.g., BTCUSDT).
        date: Date string (e.g., 2024-01-10).
        file_path: Path to the CSV file.

    Returns:
        List of summary row dictionaries.
    """
    rows = []

    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            event_ts = parse_timestamp(row.get("event_timestamp"))
            if event_ts is None:
                # Skip rows with invalid event timestamps
                continue

            liquidity_ts = parse_timestamp(row.get("liquidity_onset_time"))
            price_ts = parse_timestamp(row.get("price_onset_time"))
            volume_ts = parse_timestamp(row.get("volume_onset_time"))

            onset_liquidity_sec = compute_onset_seconds(event_ts, liquidity_ts)
            onset_price_sec = compute_onset_seconds(event_ts, price_ts)
            onset_volume_sec = compute_onset_seconds(event_ts, volume_ts)

            # Compute onset_delta = onset_liquidity - onset_price
            # This is negative if liquidity leads price
            onset_delta = None
            if onset_liquidity_sec is not None and onset_price_sec is not None:
                onset_delta = round(onset_liquidity_sec - onset_price_sec, 3)

            summary_row = {
                "date": date,
                "asset": asset,
                "event_id": row.get("window_id", ""),
                "classification": row.get("classification", ""),
                "onset_liquidity_sec": onset_liquidity_sec,
                "onset_price_sec": onset_price_sec,
                "onset_volume_sec": onset_volume_sec,
                "onset_delta": onset_delta,
            }
            rows.append(summary_row)

    return rows


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Aggregate v2 event ordering results into unified summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate all results from outputs/v2/
  python scripts/aggregate_v2_results.py

  # Custom input/output paths
  python scripts/aggregate_v2_results.py --input outputs/v2 --output outputs/my_summary.csv
        """,
    )
    parser.add_argument(
        "--input", "-i",
        default="outputs/v2",
        help="Path to v2 output directory (default: outputs/v2)",
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/v2_summary.csv",
        help="Path to output summary CSV (default: outputs/v2_summary.csv)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    v2_dir = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = REPO_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)

    # Find all ordering files
    ordering_files = find_ordering_files(v2_dir)

    if not ordering_files:
        print(f"ERROR: No event_orderings.csv files found in {v2_dir}", file=sys.stderr)
        print("  Run scripts/run_v2_analysis.py first to generate results.", file=sys.stderr)
        return 1

    if verbose:
        print(f"Aggregating v2 Results")
        print(f"{'='*60}")
        print(f"Input directory: {v2_dir}")
        print(f"Output file: {output_path}")
        print(f"Found {len(ordering_files)} (asset, date) pairs with results")

    # Process all files
    all_rows = []
    for asset, date, file_path in ordering_files:
        rows = process_ordering_file(asset, date, file_path)
        all_rows.extend(rows)
        if verbose:
            print(f"  {asset}/{date}: {len(rows)} events")

    if not all_rows:
        print("ERROR: No events found in any ordering files", file=sys.stderr)
        return 1

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date", "asset", "event_id", "classification",
        "onset_liquidity_sec", "onset_price_sec", "onset_volume_sec",
        "onset_delta",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Summary")
        print(f"{'='*60}")
        print(f"Total events: {len(all_rows)}")
        print(f"Output saved to: {output_path}")

        # Classification breakdown
        from collections import Counter
        classifications = Counter(row["classification"] for row in all_rows)
        print(f"\nClassification breakdown:")
        for cls, count in sorted(classifications.items()):
            pct = 100.0 * count / len(all_rows)
            print(f"  {cls}: {count} ({pct:.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
