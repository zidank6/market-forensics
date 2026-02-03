#!/usr/bin/env python3
"""Aggregate ordering results from multi-day pipeline runs.

Produces a summary CSV with ordering classification counts across all dates.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Optional

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_run_summary(run_dir: Path) -> Optional[dict]:
    """Load run_summary.json if it exists."""
    summary_path = run_dir / "run_summary.json"
    if not summary_path.exists():
        return None
    with open(summary_path) as f:
        return json.load(f)


def load_orderings(run_dir: Path) -> List[dict]:
    """Load event_orderings.csv if it exists."""
    orderings_path = run_dir / "metrics" / "event_orderings.csv"
    if not orderings_path.exists():
        return []
    with open(orderings_path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def aggregate_date(date: str, output_base: Path) -> dict:
    """Aggregate results for a single date.

    Returns:
        Dict with date, events_detected, windows_extracted, and classification counts.
    """
    run_dir = output_base / date

    # Load run summary for event count
    summary = load_run_summary(run_dir)
    events_detected = len(summary.get("events", [])) if summary else 0

    # Load orderings for classification counts
    orderings = load_orderings(run_dir)
    windows_extracted = len(orderings)

    # Count classifications
    counts = {
        "liquidity_first_count": 0,
        "price_first_count": 0,
        "trade_first_count": 0,  # volume-first in our data
    }
    for row in orderings:
        classification = row.get("classification", "").lower()
        if "liquidity" in classification:
            counts["liquidity_first_count"] += 1
        elif "price" in classification:
            counts["price_first_count"] += 1
        elif "volume" in classification or "trade" in classification:
            counts["trade_first_count"] += 1

    return {
        "date": date,
        "events_detected": events_detected,
        "windows_extracted": windows_extracted,
        **counts,
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Aggregate ordering results from multi-day runs."
    )
    parser.add_argument(
        "--dates-config",
        default="config/replication_dates.json",
        help="Path to JSON file listing dates to aggregate",
    )
    parser.add_argument(
        "--dates",
        nargs="*",
        help="Specific dates to aggregate (overrides config file)",
    )
    parser.add_argument(
        "--output-base",
        default="outputs",
        help="Base output directory containing {date}/ subdirectories",
    )
    parser.add_argument(
        "--output",
        default="outputs/replication_summary.csv",
        help="Path for output summary CSV",
    )

    args = parser.parse_args()

    # Load dates config
    with open(args.dates_config) as f:
        dates_config = json.load(f)

    # Determine which dates to process
    if args.dates:
        dates = args.dates
    else:
        dates = dates_config.get("dates", [])

    if not dates:
        print("ERROR: No dates specified", file=sys.stderr)
        return 1

    output_base = Path(args.output_base)

    # Aggregate each date
    results = []
    for date in dates:
        row = aggregate_date(date, output_base)
        results.append(row)
        print(f"Aggregated {date}: {row['windows_extracted']} windows, {row['liquidity_first_count']} liquidity-first")

    # Write summary CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "events_detected",
        "windows_extracted",
        "liquidity_first_count",
        "price_first_count",
        "trade_first_count",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSummary written to: {output_path}")

    # Print summary stats
    total_windows = sum(r["windows_extracted"] for r in results)
    total_liquidity = sum(r["liquidity_first_count"] for r in results)
    total_price = sum(r["price_first_count"] for r in results)
    total_trade = sum(r["trade_first_count"] for r in results)

    print(f"\nTotals across {len(dates)} dates:")
    print(f"  Windows: {total_windows}")
    print(f"  Liquidity-first: {total_liquidity} ({100*total_liquidity/total_windows:.1f}%)")
    print(f"  Price-first: {total_price} ({100*total_price/total_windows:.1f}%)")
    print(f"  Trade/Volume-first: {total_trade} ({100*total_trade/total_windows:.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
