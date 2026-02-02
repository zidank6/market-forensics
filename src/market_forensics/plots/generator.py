"""Plot generation for events and aggregate summaries.

Generates visualizations for individual events and aggregate statistics.
Requires matplotlib for plotting (graceful error if not available).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..data.models import TopOfBook, Trade
from ..events.ordering import EventOrdering
from ..windows.extractor import EventWindow

# Check for matplotlib availability
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore


class PlotError(Exception):
    """Exception raised for plotting errors."""

    pass


def check_matplotlib() -> None:
    """Check if matplotlib is available.

    Raises:
        PlotError: If matplotlib is not installed.
    """
    if not MATPLOTLIB_AVAILABLE:
        raise PlotError(
            "matplotlib is required for plotting. "
            "Install with: pip install matplotlib"
        )


@dataclass
class PlotPaths:
    """Paths to generated plots for an event."""

    price_plot: str
    spread_plot: str
    volume_plot: str


def plot_event_price(
    window: EventWindow,
    output_path: Union[Path, str],
    figsize: tuple = (10, 4),
) -> str:
    """Plot price/midprice over time around an event.

    Args:
        window: EventWindow with pre/post data.
        output_path: Path to save the plot.
        figsize: Figure size.

    Returns:
        Path to saved plot.

    Raises:
        PlotError: If matplotlib is not available.
    """
    check_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    event_time = window.event.timestamp

    # Plot TOB midprices
    all_tob = window.pre_tob + window.post_tob
    if all_tob:
        times = [t.timestamp for t in all_tob]
        prices = [t.mid_price for t in all_tob]
        ax.plot(times, prices, 'b-', label='Mid Price', linewidth=1.5)

    # Plot trade prices
    all_trades = window.pre_trades + window.post_trades
    if all_trades:
        times = [t.timestamp for t in all_trades]
        prices = [t.price for t in all_trades]
        ax.scatter(times, prices, c='gray', alpha=0.5, s=20, label='Trades')

    # Mark event time
    ax.axvline(event_time, color='red', linestyle='--', linewidth=2, label='Event')

    ax.set_xlabel('Time')
    ax.set_ylabel('Price')
    ax.set_title(f'{window.event.symbol} - Price around {window.event.event_type}\n'
                 f'Direction: {window.event.direction.value}, Magnitude: {window.event.magnitude:.2f}%')
    ax.legend(loc='best')

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)

    return str(output_path)


def plot_event_spread(
    window: EventWindow,
    output_path: Union[Path, str],
    figsize: tuple = (10, 4),
) -> str:
    """Plot spread over time around an event.

    Args:
        window: EventWindow with pre/post data.
        output_path: Path to save the plot.
        figsize: Figure size.

    Returns:
        Path to saved plot.

    Raises:
        PlotError: If matplotlib is not available or no TOB data.
    """
    check_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    event_time = window.event.timestamp

    all_tob = window.pre_tob + window.post_tob
    if all_tob:
        times = [t.timestamp for t in all_tob]
        spreads = [t.spread for t in all_tob]
        ax.plot(times, spreads, 'g-', linewidth=1.5)
        ax.fill_between(times, spreads, alpha=0.3, color='green')

    # Mark event time
    ax.axvline(event_time, color='red', linestyle='--', linewidth=2, label='Event')

    ax.set_xlabel('Time')
    ax.set_ylabel('Spread')
    ax.set_title(f'{window.event.symbol} - Spread around {window.event.event_type}')
    ax.legend(loc='best')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)

    return str(output_path)


def plot_event_volume(
    window: EventWindow,
    output_path: Union[Path, str],
    bucket_seconds: float = 5.0,
    figsize: tuple = (10, 4),
) -> str:
    """Plot trade volume over time around an event.

    Args:
        window: EventWindow with pre/post data.
        output_path: Path to save the plot.
        bucket_seconds: Time bucket for volume aggregation.
        figsize: Figure size.

    Returns:
        Path to saved plot.

    Raises:
        PlotError: If matplotlib is not available.
    """
    check_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    event_time = window.event.timestamp

    # Bucket trades by time
    all_trades = window.pre_trades + window.post_trades
    if all_trades:
        buckets: Dict[datetime, float] = {}
        for t in all_trades:
            # Round down to bucket start
            ts = t.timestamp
            bucket_start = ts.replace(
                second=int(ts.second // bucket_seconds) * int(bucket_seconds),
                microsecond=0,
            )
            buckets[bucket_start] = buckets.get(bucket_start, 0.0) + t.size

        times = sorted(buckets.keys())
        volumes = [buckets[t] for t in times]

        ax.bar(times, volumes, width=bucket_seconds / 86400, alpha=0.7, color='blue')

    # Mark event time
    ax.axvline(event_time, color='red', linestyle='--', linewidth=2, label='Event')

    ax.set_xlabel('Time')
    ax.set_ylabel('Volume')
    ax.set_title(f'{window.event.symbol} - Volume around {window.event.event_type}')
    ax.legend(loc='best')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)

    return str(output_path)


def plot_event(
    window: EventWindow,
    output_dir: Union[Path, str],
) -> PlotPaths:
    """Generate all plots for a single event.

    Args:
        window: EventWindow with pre/post data.
        output_dir: Directory to save plots.

    Returns:
        PlotPaths with paths to all generated plots.
    """
    output_dir = Path(output_dir)
    window_id = window.window_id

    price_path = plot_event_price(
        window, output_dir / f"{window_id}_price.png"
    )
    spread_path = plot_event_spread(
        window, output_dir / f"{window_id}_spread.png"
    )
    volume_path = plot_event_volume(
        window, output_dir / f"{window_id}_volume.png"
    )

    return PlotPaths(
        price_plot=price_path,
        spread_plot=spread_path,
        volume_plot=volume_path,
    )


def plot_all_events(
    windows: List[EventWindow],
    output_dir: Union[Path, str],
) -> List[PlotPaths]:
    """Generate plots for all events.

    Args:
        windows: List of EventWindow objects.
        output_dir: Directory to save plots.

    Returns:
        List of PlotPaths for each event.
    """
    return [plot_event(w, output_dir) for w in windows]


def plot_ordering_distribution(
    orderings: List[EventOrdering],
    output_path: Union[Path, str],
    figsize: tuple = (8, 6),
) -> str:
    """Plot distribution of ordering classifications.

    Args:
        orderings: List of EventOrdering results.
        output_path: Path to save the plot.
        figsize: Figure size.

    Returns:
        Path to saved plot.

    Raises:
        PlotError: If matplotlib is not available.
    """
    check_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count classifications
    counts = Counter(o.classification for o in orderings)

    # Define order and colors
    order = ['liquidity-first', 'volume-first', 'price-first', 'undetermined']
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']

    labels = []
    values = []
    bar_colors = []
    for i, label in enumerate(order):
        if label in counts:
            labels.append(label)
            values.append(counts[label])
            bar_colors.append(colors[i])

    fig, ax = plt.subplots(figsize=figsize)

    bars = ax.bar(labels, values, color=bar_colors)

    # Add count labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(val), ha='center', va='bottom', fontsize=12)

    ax.set_xlabel('Classification')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Event Ordering Classifications')

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)

    return str(output_path)


def plot_ordering_by_symbol(
    orderings: List[EventOrdering],
    output_path: Union[Path, str],
    figsize: tuple = (10, 6),
) -> str:
    """Plot ordering distribution grouped by symbol.

    Args:
        orderings: List of EventOrdering results.
        output_path: Path to save the plot.
        figsize: Figure size.

    Returns:
        Path to saved plot.

    Raises:
        PlotError: If matplotlib is not available.
    """
    check_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Group by symbol and classification
    symbol_counts: Dict[str, Counter] = {}
    for o in orderings:
        if o.symbol not in symbol_counts:
            symbol_counts[o.symbol] = Counter()
        symbol_counts[o.symbol][o.classification] += 1

    symbols = sorted(symbol_counts.keys())
    categories = ['liquidity-first', 'volume-first', 'price-first', 'undetermined']
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']

    fig, ax = plt.subplots(figsize=figsize)

    x = range(len(symbols))
    width = 0.2

    for i, (cat, color) in enumerate(zip(categories, colors)):
        values = [symbol_counts[s].get(cat, 0) for s in symbols]
        offset = (i - len(categories) / 2 + 0.5) * width
        ax.bar([xi + offset for xi in x], values, width, label=cat, color=color)

    ax.set_xlabel('Symbol')
    ax.set_ylabel('Count')
    ax.set_title('Event Ordering by Symbol')
    ax.set_xticks(x)
    ax.set_xticklabels(symbols, rotation=45)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)

    return str(output_path)


def generate_summary_table(
    orderings: List[EventOrdering],
    output_path: Union[Path, str],
) -> str:
    """Generate summary table of ordering classifications as CSV.

    Args:
        orderings: List of EventOrdering results.
        output_path: Path to save the CSV.

    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count by symbol and classification
    symbol_counts: Dict[str, Counter] = {}
    for o in orderings:
        if o.symbol not in symbol_counts:
            symbol_counts[o.symbol] = Counter()
        symbol_counts[o.symbol][o.classification] += 1

    # Write CSV
    categories = ['liquidity-first', 'volume-first', 'price-first', 'undetermined']
    fieldnames = ['symbol', 'total'] + categories

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for symbol in sorted(symbol_counts.keys()):
            counts = symbol_counts[symbol]
            row = {
                'symbol': symbol,
                'total': sum(counts.values()),
            }
            for cat in categories:
                row[cat] = counts.get(cat, 0)
            writer.writerow(row)

        # Total row
        total_counts = Counter()
        for counts in symbol_counts.values():
            total_counts.update(counts)
        row = {
            'symbol': 'TOTAL',
            'total': sum(total_counts.values()),
        }
        for cat in categories:
            row[cat] = total_counts.get(cat, 0)
        writer.writerow(row)

    return str(output_path)


def generate_all_plots(
    windows: List[EventWindow],
    orderings: List[EventOrdering],
    output_dir: Union[Path, str],
) -> dict:
    """Generate all plots and summary tables.

    Args:
        windows: List of EventWindow objects.
        orderings: List of EventOrdering results.
        output_dir: Directory to save all outputs.

    Returns:
        Dictionary with paths to all generated files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        'event_plots': [],
        'summary_plots': {},
        'summary_table': None,
    }

    # Generate per-event plots
    if MATPLOTLIB_AVAILABLE:
        for window in windows:
            try:
                plot_paths = plot_event(window, output_dir / 'events')
                paths['event_plots'].append({
                    'window_id': window.window_id,
                    'price': plot_paths.price_plot,
                    'spread': plot_paths.spread_plot,
                    'volume': plot_paths.volume_plot,
                })
            except Exception:
                # Skip failed plots
                pass

        # Generate aggregate plots
        if orderings:
            try:
                dist_path = plot_ordering_distribution(
                    orderings, output_dir / 'ordering_distribution.png'
                )
                paths['summary_plots']['distribution'] = dist_path
            except Exception:
                pass

            try:
                by_symbol_path = plot_ordering_by_symbol(
                    orderings, output_dir / 'ordering_by_symbol.png'
                )
                paths['summary_plots']['by_symbol'] = by_symbol_path
            except Exception:
                pass

    # Generate summary table (doesn't require matplotlib)
    if orderings:
        table_path = generate_summary_table(
            orderings, output_dir / 'ordering_summary.csv'
        )
        paths['summary_table'] = table_path

    return paths
