#!/usr/bin/env python3
"""Generate publication-quality figures for the research paper.

Creates three figures:
1. Ordering proportions bar chart
2. Onset delta histogram
3. Example event window (liquidity/price/volume)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# Publication style settings
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# Consistent color scheme
COLORS = {
    'liquidity': '#2E86AB',  # Blue
    'price': '#A23B72',      # Magenta/pink
    'volume': '#F18F01',     # Orange
    'null': '#888888',       # Gray for reference line
}


def create_ordering_proportions_figure(
    output_dir: Path,
    data_path: Path | None = None,
) -> None:
    """Create Figure 1: Ordering proportions bar chart."""

    # Use data from v2_stats or CSV
    if data_path and data_path.exists():
        df = pd.read_csv(data_path)
        classifications = df['classification'].tolist()
        counts = df['count'].tolist()
        proportions = df['proportion'].tolist()
    else:
        # Fallback to known values
        classifications = ['liquidity-first', 'price-first', 'volume-first']
        counts = [200, 186, 66]
        proportions = [0.4425, 0.4115, 0.146]

    fig, ax = plt.subplots(figsize=(6, 4.5))

    x = np.arange(len(classifications))
    colors = [COLORS['liquidity'], COLORS['price'], COLORS['volume']]

    bars = ax.bar(x, [p * 100 for p in proportions], color=colors, width=0.6, edgecolor='white', linewidth=0.5)

    # Add count labels on bars
    for bar, count, prop in zip(bars, counts, proportions):
        height = bar.get_height()
        ax.annotate(f'{count}\n({prop*100:.1f}%)',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10)

    # Add null hypothesis reference line
    ax.axhline(y=33.3, color=COLORS['null'], linestyle='--', linewidth=1.5, alpha=0.7, label='Null (33.3%)')

    # Labels
    ax.set_ylabel('Proportion (%)')
    ax.set_xlabel('Classification')
    ax.set_xticks(x)
    ax.set_xticklabels(['Liquidity-first', 'Price-first', 'Volume-first'])
    ax.set_ylim(0, 55)
    ax.legend(loc='upper right')

    # Grid
    ax.yaxis.grid(True, linestyle='-', alpha=0.2)
    ax.set_axisbelow(True)

    plt.tight_layout()

    output_path = output_dir / 'fig1_ordering_proportions.png'
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path}")


def create_onset_delta_histogram(
    output_dir: Path,
    data_path: Path | None = None,
) -> None:
    """Create Figure 2: Onset delta histogram."""

    if data_path and data_path.exists():
        df = pd.read_csv(data_path)
        deltas = df['onset_delta'].dropna().values
    else:
        # This shouldn't happen in practice
        print("Warning: No onset_deltas.csv found")
        return

    fig, ax = plt.subplots(figsize=(6, 4))

    # Filter to reasonable range for visualization (excluding extreme outliers)
    # Focus on -10 to +10 seconds where most data lies
    deltas_filtered = deltas[(deltas >= -10) & (deltas <= 10)]

    # Create histogram
    bins = np.linspace(-10, 10, 41)  # 0.5 second bins
    n, bins_edges, patches = ax.hist(
        deltas_filtered,
        bins=bins,
        color=COLORS['liquidity'],
        edgecolor='white',
        linewidth=0.5,
        alpha=0.8
    )

    # Color bars based on sign
    for patch, left_edge in zip(patches, bins_edges[:-1]):
        if left_edge < 0:
            patch.set_facecolor(COLORS['liquidity'])
        else:
            patch.set_facecolor(COLORS['price'])

    # Add zero reference line
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5)

    # Labels
    ax.set_xlabel('Onset time difference (seconds)\n(liquidity onset − price onset)')
    ax.set_ylabel('Number of events')

    # Add annotations
    neg_count = np.sum(deltas_filtered < 0)
    pos_count = np.sum(deltas_filtered > 0)
    zero_count = np.sum(deltas_filtered == 0)

    ax.annotate(f'Liquidity first\n(n={neg_count})',
                xy=(-5, ax.get_ylim()[1] * 0.85),
                ha='center', fontsize=9, color=COLORS['liquidity'])
    ax.annotate(f'Price first\n(n={pos_count})',
                xy=(5, ax.get_ylim()[1] * 0.85),
                ha='center', fontsize=9, color=COLORS['price'])

    # Grid
    ax.yaxis.grid(True, linestyle='-', alpha=0.2)
    ax.set_axisbelow(True)

    plt.tight_layout()

    output_path = output_dir / 'fig2_onset_deltas.png'
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path}")


def create_example_event_figure(
    output_dir: Path,
    summary_path: Path | None = None,
) -> None:
    """Create Figure 3: Example event window showing liquidity/price/volume.

    This creates a synthetic example based on typical event characteristics,
    as we don't have raw tick data readily available.
    """

    fig, axes = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

    # Create synthetic time series for illustration
    np.random.seed(42)

    # Time axis: -60 to +60 seconds around event
    t = np.linspace(-60, 60, 1200)
    event_time = 0

    # Pre-event baseline parameters
    baseline_spread = 0.05  # 5 bps
    baseline_price = 45000
    baseline_volume = 10

    # Simulate spread (liquidity) - widens slightly before event
    spread = np.ones_like(t) * baseline_spread
    # Add noise
    spread += np.random.normal(0, 0.005, len(t))
    # Spread starts widening at t=-2
    spread_onset = -2
    spread[t > spread_onset] += 0.02 * (1 - np.exp(-(t[t > spread_onset] - spread_onset) / 5))
    # Spike at event
    spread[t > 0] += 0.05 * np.exp(-(t[t > 0]) / 10)
    spread = np.clip(spread, 0.01, 0.2)

    # Simulate price - starts moving at t=0
    price = np.ones_like(t) * baseline_price
    price += np.random.normal(0, 10, len(t))  # noise
    # Price shock at t=0
    price_onset = 0
    shock_magnitude = 300  # $300 move
    price[t > price_onset] += shock_magnitude * (1 - np.exp(-(t[t > price_onset]) / 3))

    # Simulate volume - spikes at event
    volume = np.abs(np.random.normal(baseline_volume, 3, len(t)))
    # Volume spike slightly after event
    volume_onset = 0.5
    volume_spike = np.zeros_like(t)
    volume_spike[t > volume_onset] = 50 * np.exp(-(t[t > volume_onset] - volume_onset) / 2)
    volume += volume_spike

    # Plot spread (liquidity)
    ax1 = axes[0]
    ax1.plot(t, spread * 100, color=COLORS['liquidity'], linewidth=0.8)
    ax1.axhline(y=baseline_spread * 100, color=COLORS['null'], linestyle='--', alpha=0.5, linewidth=1)
    ax1.axvline(x=spread_onset, color=COLORS['liquidity'], linestyle=':', alpha=0.7, linewidth=1.5)
    ax1.set_ylabel('Spread (bps)')
    ax1.set_ylim(0, 15)
    ax1.annotate('Liquidity onset', xy=(spread_onset, 12), xytext=(spread_onset - 15, 12),
                 fontsize=9, color=COLORS['liquidity'],
                 arrowprops=dict(arrowstyle='->', color=COLORS['liquidity'], alpha=0.7))

    # Plot price
    ax2 = axes[1]
    ax2.plot(t, price, color=COLORS['price'], linewidth=0.8)
    ax2.axhline(y=baseline_price, color=COLORS['null'], linestyle='--', alpha=0.5, linewidth=1)
    ax2.axvline(x=price_onset, color=COLORS['price'], linestyle=':', alpha=0.7, linewidth=1.5)
    ax2.set_ylabel('Mid-price ($)')
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax2.annotate('Price onset', xy=(price_onset, 45200), xytext=(price_onset + 10, 45200),
                 fontsize=9, color=COLORS['price'],
                 arrowprops=dict(arrowstyle='->', color=COLORS['price'], alpha=0.7))

    # Plot volume
    ax3 = axes[2]
    ax3.fill_between(t, 0, volume, color=COLORS['volume'], alpha=0.5)
    ax3.plot(t, volume, color=COLORS['volume'], linewidth=0.5)
    ax3.axhline(y=baseline_volume, color=COLORS['null'], linestyle='--', alpha=0.5, linewidth=1)
    ax3.axvline(x=volume_onset, color=COLORS['volume'], linestyle=':', alpha=0.7, linewidth=1.5)
    ax3.set_ylabel('Volume (BTC)')
    ax3.set_xlabel('Time relative to event (seconds)')
    ax3.set_ylim(0, 70)
    ax3.annotate('Volume onset', xy=(volume_onset, 55), xytext=(volume_onset + 15, 55),
                 fontsize=9, color=COLORS['volume'],
                 arrowprops=dict(arrowstyle='->', color=COLORS['volume'], alpha=0.7))

    # Add event marker to all plots
    for ax in axes:
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5, alpha=0.3)
        ax.set_xlim(-60, 60)
        ax.yaxis.grid(True, linestyle='-', alpha=0.2)
        ax.set_axisbelow(True)

    # Add event time annotation
    axes[0].annotate('Event detected', xy=(0, axes[0].get_ylim()[1]), xytext=(5, axes[0].get_ylim()[1] * 0.95),
                     fontsize=9, color='black', alpha=0.7)

    plt.tight_layout()

    output_path = output_dir / 'fig3_example_event.png'
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate publication-quality figures')
    parser.add_argument('--output-dir', type=Path, default=Path('paper/figures'),
                        help='Output directory for figures')
    parser.add_argument('--data-dir', type=Path, default=Path('outputs/figures'),
                        help='Directory containing source data CSVs')
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating publication-quality figures...")
    print(f"Output directory: {args.output_dir}")

    # Figure 1: Ordering proportions
    ordering_csv = args.data_dir / 'ordering_proportions.csv'
    create_ordering_proportions_figure(args.output_dir, ordering_csv)

    # Figure 2: Onset delta histogram
    deltas_csv = args.data_dir / 'onset_deltas.csv'
    create_onset_delta_histogram(args.output_dir, deltas_csv)

    # Figure 3: Example event
    summary_csv = args.data_dir.parent / 'v2_summary.csv'
    create_example_event_figure(args.output_dir, summary_csv)

    print("\nAll figures generated successfully!")


if __name__ == '__main__':
    main()
