#!/usr/bin/env python3
"""Generate key visualizations for v2 analysis results.

Creates:
1. Bar chart of ordering proportions (liquidity-first vs others)
2. Histogram of onset deltas (t_liquidity - t_price in seconds)

Falls back to ASCII/CSV output if matplotlib is not available.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent

# Check for matplotlib availability
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def load_summary_csv(summary_path: Path) -> List[dict]:
    """Load v2_summary.csv.

    Args:
        summary_path: Path to v2_summary.csv.

    Returns:
        List of row dictionaries.
    """
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    rows = []
    with open(summary_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def count_classifications(rows: List[dict]) -> dict:
    """Count events by classification."""
    counts = {}
    for row in rows:
        cls = row.get("classification", "unknown")
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def extract_onset_deltas(rows: List[dict]) -> List[float]:
    """Extract onset_delta values (filtering out None/empty)."""
    deltas = []
    for row in rows:
        delta_str = row.get("onset_delta", "")
        if delta_str and delta_str.strip() != "":
            try:
                deltas.append(float(delta_str))
            except ValueError:
                pass
    return deltas


def generate_proportion_bar_chart_matplotlib(
    counts: dict, output_path: Path
) -> str:
    """Generate bar chart of ordering proportions using matplotlib."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("No events to plot")

    # Sort by count descending, but put liquidity-first first if present
    items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))

    labels = [item[0] for item in items]
    values = [item[1] for item in items]
    percentages = [100.0 * v / total for v in values]

    # Color liquidity-first differently
    colors = ['#2ecc71' if label == 'liquidity-first' else '#3498db' for label in labels]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, percentages, color=colors, edgecolor='black', linewidth=0.5)

    # Add value labels on bars
    for bar, count, pct in zip(bars, values, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f'{pct:.1f}%\n(n={count})',
            ha='center', va='bottom', fontsize=10
        )

    ax.set_xlabel('Classification', fontsize=12)
    ax.set_ylabel('Proportion (%)', fontsize=12)
    ax.set_title(f'Event Ordering Classification (n={total})', fontsize=14)
    ax.set_ylim(0, max(percentages) + 15)

    # Add horizontal line at 33.3% (null hypothesis)
    ax.axhline(y=33.33, color='red', linestyle='--', linewidth=1, label='33% null')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(output_path)


def generate_delta_histogram_matplotlib(
    deltas: List[float], output_path: Path
) -> str:
    """Generate histogram of onset deltas using matplotlib."""
    if not deltas:
        raise ValueError("No onset deltas to plot")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Determine bins
    n_bins = min(30, max(10, len(deltas) // 5))

    ax.hist(deltas, bins=n_bins, color='#3498db', edgecolor='black', linewidth=0.5, alpha=0.7)

    # Add vertical line at 0
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, label='0 (simultaneous)')

    # Statistics
    mean_delta = sum(deltas) / len(deltas)
    median_delta = sorted(deltas)[len(deltas) // 2]
    negative_count = sum(1 for d in deltas if d < 0)
    negative_pct = 100.0 * negative_count / len(deltas)

    ax.axvline(x=mean_delta, color='green', linestyle='-', linewidth=1.5, label=f'Mean: {mean_delta:.2f}s')

    ax.set_xlabel('Onset Delta (seconds): t_liquidity - t_price', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title(f'Distribution of Onset Deltas (n={len(deltas)})\n'
                 f'Negative = liquidity leads price ({negative_pct:.1f}%)', fontsize=14)
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(output_path)


def generate_proportion_bar_chart_ascii(counts: dict, output_path: Path) -> str:
    """Generate ASCII bar chart of ordering proportions."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("No events to plot")

    items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    max_label_len = max(len(label) for label, _ in items)
    max_bar_width = 50

    lines = []
    lines.append(f"Event Ordering Classification (n={total})")
    lines.append("=" * 70)
    lines.append(f"{'Classification':<{max_label_len}}  {'Bar':<{max_bar_width}}  Count  Pct")
    lines.append("-" * 70)

    for label, count in items:
        pct = 100.0 * count / total
        bar_len = int(pct / 100.0 * max_bar_width)
        bar = '#' * bar_len
        marker = '*' if label == 'liquidity-first' else ' '
        lines.append(f"{label:<{max_label_len}} {marker}|{bar:<{max_bar_width}}| {count:5d}  {pct:5.1f}%")

    lines.append("-" * 70)
    lines.append("(* = liquidity-first, --- = 33% null hypothesis)")
    lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)

    return str(output_path)


def generate_delta_histogram_ascii(deltas: List[float], output_path: Path) -> str:
    """Generate ASCII histogram of onset deltas."""
    if not deltas:
        raise ValueError("No onset deltas to plot")

    # Compute histogram bins
    min_val = min(deltas)
    max_val = max(deltas)
    n_bins = 20
    bin_width = (max_val - min_val) / n_bins if max_val > min_val else 1.0

    bins = [0] * n_bins
    for d in deltas:
        idx = min(int((d - min_val) / bin_width), n_bins - 1)
        bins[idx] += 1

    max_count = max(bins) if bins else 1
    bar_width = 40

    lines = []
    lines.append(f"Distribution of Onset Deltas (n={len(deltas)})")
    lines.append("=" * 70)
    lines.append("t_liquidity - t_price (seconds)")
    lines.append("Negative = liquidity leads price")
    lines.append("-" * 70)

    for i, count in enumerate(bins):
        bin_start = min_val + i * bin_width
        bin_end = bin_start + bin_width
        bar_len = int(count / max_count * bar_width)
        bar = '#' * bar_len
        # Mark bins that contain 0
        zero_marker = '*' if bin_start <= 0 < bin_end else ' '
        lines.append(f"[{bin_start:7.2f}, {bin_end:7.2f}) {zero_marker}|{bar:<{bar_width}}| {count:4d}")

    lines.append("-" * 70)

    # Statistics
    mean_delta = sum(deltas) / len(deltas)
    median_delta = sorted(deltas)[len(deltas) // 2]
    negative_count = sum(1 for d in deltas if d < 0)
    negative_pct = 100.0 * negative_count / len(deltas)

    lines.append(f"Mean:   {mean_delta:.3f}s")
    lines.append(f"Median: {median_delta:.3f}s")
    lines.append(f"Negative (liquidity leads): {negative_count}/{len(deltas)} ({negative_pct:.1f}%)")
    lines.append("(* marks bin containing 0)")

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)

    return str(output_path)


def save_counts_csv(counts: dict, output_path: Path) -> str:
    """Save classification counts to CSV."""
    total = sum(counts.values())
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["classification", "count", "proportion"])
        for label, count in sorted(counts.items()):
            pct = count / total if total > 0 else 0
            writer.writerow([label, count, round(pct, 4)])
    return str(output_path)


def save_deltas_csv(deltas: List[float], output_path: Path) -> str:
    """Save onset deltas to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["onset_delta"])
        for d in deltas:
            writer.writerow([d])
    return str(output_path)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate v2 figures for analysis results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all figures
  python scripts/generate_v2_figures.py

  # Custom paths
  python scripts/generate_v2_figures.py --input outputs/v2_summary.csv --output-dir outputs/figures
        """,
    )
    parser.add_argument(
        "--input", "-i",
        default="outputs/v2_summary.csv",
        help="Path to v2_summary.csv (default: outputs/v2_summary.csv)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="outputs/figures",
        help="Directory for output figures (default: outputs/figures)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    # Resolve paths
    input_path = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_dir = REPO_ROOT / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        rows = load_summary_csv(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("  Run scripts/aggregate_v2_results.py first.", file=sys.stderr)
        return 1

    if not rows:
        print("ERROR: Summary file is empty", file=sys.stderr)
        return 1

    counts = count_classifications(rows)
    deltas = extract_onset_deltas(rows)

    if verbose:
        print(f"Generate v2 Figures")
        print(f"{'='*60}")
        print(f"Input: {input_path}")
        print(f"Output directory: {output_dir}")
        print(f"Total events: {len(rows)}")
        print(f"Events with onset_delta: {len(deltas)}")
        print(f"matplotlib available: {MATPLOTLIB_AVAILABLE}")
        print()

    generated_files = []

    # Generate proportion bar chart
    if verbose:
        print("Generating proportion bar chart...")

    if MATPLOTLIB_AVAILABLE:
        try:
            path = generate_proportion_bar_chart_matplotlib(counts, output_dir / "ordering_proportions.png")
            generated_files.append(path)
            if verbose:
                print(f"  Saved: {path}")
        except Exception as e:
            print(f"  WARNING: Failed to generate matplotlib chart: {e}", file=sys.stderr)
            MATPLOTLIB_AVAILABLE_BACKUP = False
        else:
            MATPLOTLIB_AVAILABLE_BACKUP = True
    else:
        MATPLOTLIB_AVAILABLE_BACKUP = False

    if not MATPLOTLIB_AVAILABLE or not MATPLOTLIB_AVAILABLE_BACKUP:
        path = generate_proportion_bar_chart_ascii(counts, output_dir / "ordering_proportions.txt")
        generated_files.append(path)
        if verbose:
            print(f"  Saved (ASCII fallback): {path}")

    # Always save CSV
    path = save_counts_csv(counts, output_dir / "ordering_proportions.csv")
    generated_files.append(path)
    if verbose:
        print(f"  Saved: {path}")

    # Generate delta histogram
    if deltas:
        if verbose:
            print("Generating onset delta histogram...")

        if MATPLOTLIB_AVAILABLE:
            try:
                path = generate_delta_histogram_matplotlib(deltas, output_dir / "onset_deltas.png")
                generated_files.append(path)
                if verbose:
                    print(f"  Saved: {path}")
            except Exception as e:
                print(f"  WARNING: Failed to generate matplotlib histogram: {e}", file=sys.stderr)
                path = generate_delta_histogram_ascii(deltas, output_dir / "onset_deltas.txt")
                generated_files.append(path)
                if verbose:
                    print(f"  Saved (ASCII fallback): {path}")
        else:
            path = generate_delta_histogram_ascii(deltas, output_dir / "onset_deltas.txt")
            generated_files.append(path)
            if verbose:
                print(f"  Saved (ASCII fallback): {path}")

        # Always save CSV
        path = save_deltas_csv(deltas, output_dir / "onset_deltas.csv")
        generated_files.append(path)
        if verbose:
            print(f"  Saved: {path}")
    else:
        if verbose:
            print("Skipping onset delta histogram (no valid deltas)")

    if verbose:
        print()
        print(f"{'='*60}")
        print(f"Generated {len(generated_files)} files")
        for f in generated_files:
            print(f"  {f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
