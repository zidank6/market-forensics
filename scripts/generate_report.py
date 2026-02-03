#!/usr/bin/env python3
"""Generate final research summary report.

Produces a markdown report summarizing replication and sensitivity results.
All numbers are derived from the generated CSV files, not hardcoded.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_csv(path: str) -> List[dict]:
    """Load a CSV file as a list of dicts."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def generate_report(
    replication_csv: str,
    sensitivity_csv: str,
    output_path: str,
) -> None:
    """Generate the markdown report.

    Args:
        replication_csv: Path to replication_summary.csv
        sensitivity_csv: Path to sensitivity_summary.csv
        output_path: Path for output markdown file
    """
    # Load data
    replication_data = load_csv(replication_csv)
    sensitivity_data = load_csv(sensitivity_csv)

    # Calculate totals for replication
    total_events = sum(int(r["events_detected"]) for r in replication_data)
    total_windows = sum(int(r["windows_extracted"]) for r in replication_data)
    total_liquidity = sum(int(r["liquidity_first_count"]) for r in replication_data)
    total_price = sum(int(r["price_first_count"]) for r in replication_data)
    total_trade = sum(int(r["trade_first_count"]) for r in replication_data)

    # Calculate percentages
    pct_liquidity = 100 * total_liquidity / total_windows if total_windows > 0 else 0
    pct_price = 100 * total_price / total_windows if total_windows > 0 else 0
    pct_trade = 100 * total_trade / total_windows if total_windows > 0 else 0

    # Analyze sensitivity: is liquidity-first stable?
    sens_windows = [int(s["windows_extracted"]) for s in sensitivity_data]
    sens_liquidity = [int(s["liquidity_first"]) for s in sensitivity_data]
    sens_liquidity_pct = [
        100 * liq / win if win > 0 else 0
        for liq, win in zip(sens_liquidity, sens_windows)
    ]

    # Check if liquidity-first is consistently the plurality
    liquidity_dominant_all = all(
        int(s["liquidity_first"]) >= int(s["price_first"]) and
        int(s["liquidity_first"]) >= int(s["volume_first"])
        for s in sensitivity_data
    )

    # Generate report
    report = []
    report.append("# Replication and Robustness Analysis Report")
    report.append("")
    report.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    report.append("")
    report.append("---")
    report.append("")

    # Summary
    report.append("## Executive Summary")
    report.append("")
    report.append("This report summarizes the replication and sensitivity analysis of the")
    report.append("market forensics pipeline's change ordering detection on BTCUSDT futures data.")
    report.append("")
    report.append(f"**Key Finding:** Liquidity-first ordering accounts for **{pct_liquidity:.1f}%** of detected")
    report.append(f"events across {len(replication_data)} trading days and {total_windows} windows.")
    if liquidity_dominant_all:
        report.append("This pattern is **stable across threshold variations**.")
    else:
        report.append("This pattern shows **some variation across threshold settings**.")
    report.append("")
    report.append("---")
    report.append("")

    # Dates analyzed
    report.append("## Dates Analyzed")
    report.append("")
    report.append("| Date | Events Detected | Windows Extracted |")
    report.append("|------|-----------------|-------------------|")
    for r in replication_data:
        report.append(f"| {r['date']} | {r['events_detected']} | {r['windows_extracted']} |")
    report.append(f"| **Total** | **{total_events}** | **{total_windows}** |")
    report.append("")
    report.append("---")
    report.append("")

    # Ordering breakdown
    report.append("## Ordering Classification Breakdown")
    report.append("")
    report.append("### By Date")
    report.append("")
    report.append("| Date | Liquidity-First | Price-First | Trade-First |")
    report.append("|------|-----------------|-------------|-------------|")
    for r in replication_data:
        report.append(f"| {r['date']} | {r['liquidity_first_count']} | {r['price_first_count']} | {r['trade_first_count']} |")
    report.append(f"| **Total** | **{total_liquidity}** | **{total_price}** | **{total_trade}** |")
    report.append("")

    report.append("### Overall Distribution")
    report.append("")
    report.append(f"- **Liquidity-first:** {total_liquidity} ({pct_liquidity:.1f}%)")
    report.append(f"- **Price-first:** {total_price} ({pct_price:.1f}%)")
    report.append(f"- **Trade/Volume-first:** {total_trade} ({pct_trade:.1f}%)")
    report.append("")
    report.append("---")
    report.append("")

    # Sensitivity analysis
    report.append("## Threshold Sensitivity Analysis")
    report.append("")
    report.append(f"Sensitivity analysis was performed on {sensitivity_data[0]['date']} with varying")
    report.append("`price_shock_threshold_pct` values.")
    report.append("")
    report.append("| Threshold (%) | Events | Windows | Liquidity-First | Price-First | Volume-First |")
    report.append("|---------------|--------|---------|-----------------|-------------|--------------|")
    for s in sensitivity_data:
        report.append(f"| {s['threshold_pct']} | {s['events_detected']} | {s['windows_extracted']} | {s['liquidity_first']} | {s['price_first']} | {s['volume_first']} |")
    report.append("")

    report.append("### Observations")
    report.append("")
    report.append("1. **Event count sensitivity:** Lower thresholds detect more events")
    report.append(f"   ({sensitivity_data[0]['events_detected']} at {sensitivity_data[0]['threshold_pct']}% vs")
    report.append(f"   {sensitivity_data[-1]['events_detected']} at {sensitivity_data[-1]['threshold_pct']}%)")
    report.append("")
    report.append("2. **Classification stability:** Liquidity-first classification")
    if liquidity_dominant_all:
        report.append("   remains the dominant category across all tested thresholds.")
    else:
        report.append("   varies across threshold settings.")
    report.append("")
    report.append("3. **Liquidity-first percentages by threshold:**")
    for s, pct in zip(sensitivity_data, sens_liquidity_pct):
        report.append(f"   - {s['threshold_pct']}%: {pct:.1f}%")
    report.append("")
    report.append("---")
    report.append("")

    # Research question answer
    report.append("## Research Question: Is Liquidity-First Ordering Consistent?")
    report.append("")
    report.append("**Question:** Is the liquidity-first ordering pattern consistent across")
    report.append("different trading days and threshold settings?")
    report.append("")
    report.append("**Answer:**")
    report.append("")

    if liquidity_dominant_all and pct_liquidity > 50:
        report.append("**Yes**, with qualifications. Liquidity-first ordering is the most common")
        report.append(f"classification, appearing in {pct_liquidity:.1f}% of detected events across")
        report.append(f"{len(replication_data)} days. This pattern holds across threshold variations")
        report.append(f"from {sensitivity_data[0]['threshold_pct']}% to {sensitivity_data[-1]['threshold_pct']}%.")
    elif pct_liquidity > 40:
        report.append("**Partially**. Liquidity-first ordering is the plurality classification")
        report.append(f"({pct_liquidity:.1f}%), but other patterns (price-first, volume-first) represent")
        report.append("a significant portion of events. Results are threshold-dependent.")
    else:
        report.append("**No**. While liquidity-first ordering is present, it does not dominate")
        report.append("the detected events. Other patterns are equally or more common.")

    report.append("")
    report.append("### Caveats")
    report.append("")
    report.append("1. Analysis covers only 3 trading days; more data would strengthen conclusions")
    report.append("2. All data is from a single symbol (BTCUSDT) and exchange (Binance Futures)")
    report.append("3. Temporal ordering does not imply causation")
    report.append("4. Results depend on threshold and baseline window parameters")
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Report generated by `scripts/generate_report.py`*")

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(report))

    print(f"Report written to: {output_path}")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate final research summary report."
    )
    parser.add_argument(
        "--replication-csv",
        default="outputs/replication_summary.csv",
        help="Path to replication_summary.csv",
    )
    parser.add_argument(
        "--sensitivity-csv",
        default="outputs/sensitivity_summary.csv",
        help="Path to sensitivity_summary.csv",
    )
    parser.add_argument(
        "--output",
        default="outputs/replication_report.md",
        help="Path for output markdown report",
    )

    args = parser.parse_args()

    try:
        generate_report(
            replication_csv=args.replication_csv,
            sensitivity_csv=args.sensitivity_csv,
            output_path=args.output,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Make sure replication_summary.csv and sensitivity_summary.csv exist.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
