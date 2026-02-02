"""Reproducible pipeline runner.

Runs the full market forensics pipeline end-to-end:
events -> windows -> metrics -> ordering -> plots
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .config import load_config
from .data.loaders import load_tob, load_trades
from .data.models import TopOfBook, Trade
from .events.detector import detect_price_shocks_from_config
from .events.ordering import (
    analyze_all_orderings,
    analyze_event_ordering_from_config,
    save_orderings,
)
from .metrics.calculator import compute_all_metrics, save_metrics
from .plots.generator import MATPLOTLIB_AVAILABLE, generate_all_plots
from .windows.extractor import (
    extract_windows_from_config,
    save_windows,
)


def run_pipeline(
    config_path: str,
    trades_path: str,
    tob_path: str,
    output_dir: str,
    verbose: bool = True,
) -> dict:
    """Run the full pipeline end-to-end.

    Args:
        config_path: Path to configuration file.
        trades_path: Path to trades data file (CSV or JSONL).
        tob_path: Path to top-of-book data file (CSV or JSONL).
        output_dir: Directory to save all outputs.
        verbose: Whether to print progress messages.

    Returns:
        Dictionary with paths to all generated outputs.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'config': config_path,
        'events': [],
        'windows': [],
        'metrics': {},
        'orderings': {},
        'plots': {},
    }

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    # Load config
    log(f"Loading config from {config_path}...")
    config = load_config(config_path)

    # Load data
    log(f"Loading trades from {trades_path}...")
    trades = load_trades(trades_path)
    log(f"  Loaded {len(trades)} trades")

    log(f"Loading top-of-book from {tob_path}...")
    tob = load_tob(tob_path)
    log(f"  Loaded {len(tob)} TOB snapshots")

    # Detect events
    log("Detecting price shock events...")
    events = detect_price_shocks_from_config(tob, config)
    log(f"  Detected {len(events)} events")
    results['events'] = [
        {
            'timestamp': e.timestamp.isoformat(),
            'symbol': e.symbol,
            'direction': e.direction.value,
            'magnitude': e.magnitude,
        }
        for e in events
    ]

    if not events:
        log("No events detected. Pipeline complete.")
        return results

    # Extract windows
    log("Extracting event windows...")
    windows = extract_windows_from_config(events, trades, tob, config)
    log(f"  Extracted {len(windows)} windows (overlapping events filtered)")

    # Save windows
    log("Saving windows to outputs/windows/...")
    window_paths = save_windows(windows, output_dir / "windows")
    results['windows'] = window_paths

    # Compute metrics
    log("Computing metrics...")
    metrics = compute_all_metrics(windows)

    log("Saving metrics to outputs/metrics/...")
    metrics_paths = save_metrics(metrics, output_dir / "metrics")
    results['metrics'] = metrics_paths

    # Analyze ordering
    log("Analyzing change ordering...")
    orderings = [
        analyze_event_ordering_from_config(w, config)
        for w in windows
    ]

    log("Saving orderings to outputs/metrics/...")
    orderings_paths = save_orderings(orderings, output_dir / "metrics")
    results['orderings'] = orderings_paths

    # Generate plots
    log("Generating plots...")
    if MATPLOTLIB_AVAILABLE:
        plot_paths = generate_all_plots(windows, orderings, output_dir / "plots")
        results['plots'] = plot_paths
        log(f"  Generated {len(plot_paths.get('event_plots', []))} event plots")
    else:
        log("  matplotlib not available, skipping graphical plots")
        # Still generate summary table
        from .plots.generator import generate_summary_table
        table_path = generate_summary_table(
            orderings, output_dir / "plots" / "ordering_summary.csv"
        )
        results['plots'] = {'summary_table': table_path}

    # Save run summary
    summary_path = output_dir / "run_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    log(f"Run summary saved to {summary_path}")

    log("\nPipeline complete!")
    log(f"  Events detected: {len(events)}")
    log(f"  Windows extracted: {len(windows)}")
    log(f"  Outputs saved to: {output_dir}")

    # Print ordering summary
    if orderings:
        from collections import Counter
        counts = Counter(o.classification for o in orderings)
        log("\nOrdering classification summary:")
        for cls, count in sorted(counts.items()):
            log(f"  {cls}: {count}")

    return results


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run the market forensics pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config on sample data
  python -m market_forensics.run

  # Run with custom paths
  python -m market_forensics.run --config config/default.json \\
      --trades data/sample/trades.csv \\
      --tob data/sample/tob.csv \\
      --output outputs
        """,
    )

    # Get default paths relative to repo root
    default_config = "config/default.json"

    parser.add_argument(
        "--config", "-c",
        default=default_config,
        help=f"Path to configuration file (default: {default_config})",
    )
    parser.add_argument(
        "--trades", "-t",
        default=None,
        help="Path to trades CSV/JSONL file (default: from config paths.data_dir)",
    )
    parser.add_argument(
        "--tob", "-b",
        default=None,
        help="Path to top-of-book CSV/JSONL file (default: from config paths.data_dir)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: from config paths.output_dir)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()

    # Load config to get default paths
    config = load_config(args.config)
    data_dir = Path(config.get("paths", {}).get("data_dir", "data/sample"))
    output_dir = config.get("paths", {}).get("output_dir", "outputs")

    # Use config-derived paths if not overridden by CLI args
    trades_path = args.trades if args.trades else str(data_dir / "trades.csv")
    tob_path = args.tob if args.tob else str(data_dir / "tob.csv")
    output_path = args.output if args.output else output_dir

    try:
        run_pipeline(
            config_path=args.config,
            trades_path=trades_path,
            tob_path=tob_path,
            output_dir=output_path,
            verbose=not args.quiet,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
