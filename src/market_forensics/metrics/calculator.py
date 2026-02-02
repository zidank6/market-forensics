"""Core microstructure metrics computation.

Computes metrics for trade and top-of-book data within event windows.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from ..data.models import TopOfBook, Trade
from ..windows.extractor import EventWindow


class MetricsError(Exception):
    """Exception raised for metrics computation errors."""

    pass


@dataclass
class WindowMetrics:
    """Computed metrics for a single window (pre or post).

    Attributes:
        trade_count: Number of trades in the window.
        trade_volume: Total volume (sum of trade sizes).
        avg_trade_size: Average trade size (None if no trades).
        vwap: Volume-weighted average price (None if no trades).
        avg_spread: Average bid-ask spread (None if no TOB data).
        avg_spread_bps: Average spread in basis points (None if no TOB data).
        avg_midprice: Average midprice (None if no TOB data).
        realized_volatility: Simple realized volatility proxy based on price returns.
        min_price: Minimum trade price (None if no trades).
        max_price: Maximum trade price (None if no trades).
    """

    trade_count: int
    trade_volume: float
    avg_trade_size: Optional[float]
    vwap: Optional[float]
    avg_spread: Optional[float]
    avg_spread_bps: Optional[float]
    avg_midprice: Optional[float]
    realized_volatility: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "trade_count": self.trade_count,
            "trade_volume": self.trade_volume,
            "avg_trade_size": self.avg_trade_size,
            "vwap": self.vwap,
            "avg_spread": self.avg_spread,
            "avg_spread_bps": self.avg_spread_bps,
            "avg_midprice": self.avg_midprice,
            "realized_volatility": self.realized_volatility,
            "min_price": self.min_price,
            "max_price": self.max_price,
        }


@dataclass
class EventMetrics:
    """Complete metrics for an event window (pre and post).

    Attributes:
        window_id: Unique identifier for the window.
        symbol: Trading pair symbol.
        event_timestamp: ISO-formatted event timestamp.
        event_direction: Direction of the event (up/down).
        event_magnitude: Magnitude of the price shock.
        pre_metrics: Metrics for the pre-event window.
        post_metrics: Metrics for the post-event window.
    """

    window_id: str
    symbol: str
    event_timestamp: str
    event_direction: str
    event_magnitude: float
    pre_metrics: WindowMetrics
    post_metrics: WindowMetrics

    def to_dict(self) -> dict:
        """Convert to dictionary with flattened structure."""
        return {
            "window_id": self.window_id,
            "symbol": self.symbol,
            "event_timestamp": self.event_timestamp,
            "event_direction": self.event_direction,
            "event_magnitude": self.event_magnitude,
            # Pre-window metrics (prefixed)
            "pre_trade_count": self.pre_metrics.trade_count,
            "pre_trade_volume": self.pre_metrics.trade_volume,
            "pre_avg_trade_size": self.pre_metrics.avg_trade_size,
            "pre_vwap": self.pre_metrics.vwap,
            "pre_avg_spread": self.pre_metrics.avg_spread,
            "pre_avg_spread_bps": self.pre_metrics.avg_spread_bps,
            "pre_avg_midprice": self.pre_metrics.avg_midprice,
            "pre_realized_volatility": self.pre_metrics.realized_volatility,
            "pre_min_price": self.pre_metrics.min_price,
            "pre_max_price": self.pre_metrics.max_price,
            # Post-window metrics (prefixed)
            "post_trade_count": self.post_metrics.trade_count,
            "post_trade_volume": self.post_metrics.trade_volume,
            "post_avg_trade_size": self.post_metrics.avg_trade_size,
            "post_vwap": self.post_metrics.vwap,
            "post_avg_spread": self.post_metrics.avg_spread,
            "post_avg_spread_bps": self.post_metrics.avg_spread_bps,
            "post_avg_midprice": self.post_metrics.avg_midprice,
            "post_realized_volatility": self.post_metrics.realized_volatility,
            "post_min_price": self.post_metrics.min_price,
            "post_max_price": self.post_metrics.max_price,
        }


def compute_trade_metrics(trades: List[Trade]) -> tuple:
    """Compute trade-based metrics.

    Args:
        trades: List of trades.

    Returns:
        Tuple of (trade_count, trade_volume, avg_trade_size, vwap, realized_vol, min_price, max_price)
    """
    trade_count = len(trades)

    if trade_count == 0:
        return (0, 0.0, None, None, None, None, None)

    trade_volume = sum(t.size for t in trades)
    avg_trade_size = trade_volume / trade_count

    # VWAP = sum(price * size) / sum(size)
    vwap = sum(t.price * t.size for t in trades) / trade_volume

    # Price stats
    prices = [t.price for t in trades]
    min_price = min(prices)
    max_price = max(prices)

    # Realized volatility proxy: standard deviation of log returns
    # Only if we have at least 2 data points
    realized_vol = None
    if trade_count >= 2:
        log_returns = []
        for i in range(1, len(trades)):
            if trades[i - 1].price > 0:
                log_return = math.log(trades[i].price / trades[i - 1].price)
                log_returns.append(log_return)

        if log_returns:
            mean_return = sum(log_returns) / len(log_returns)
            variance = sum((r - mean_return) ** 2 for r in log_returns) / len(log_returns)
            realized_vol = math.sqrt(variance)

    return (trade_count, trade_volume, avg_trade_size, vwap, realized_vol, min_price, max_price)


def compute_tob_metrics(tob: List[TopOfBook]) -> tuple:
    """Compute top-of-book based metrics.

    Args:
        tob: List of top-of-book snapshots.

    Returns:
        Tuple of (avg_spread, avg_spread_bps, avg_midprice)
    """
    if not tob:
        return (None, None, None)

    spreads = [t.spread for t in tob]
    spreads_bps = [t.spread_bps for t in tob]
    midprices = [t.mid_price for t in tob]

    avg_spread = sum(spreads) / len(spreads)
    avg_spread_bps = sum(spreads_bps) / len(spreads_bps)
    avg_midprice = sum(midprices) / len(midprices)

    return (avg_spread, avg_spread_bps, avg_midprice)


def compute_window_metrics(trades: List[Trade], tob: List[TopOfBook]) -> WindowMetrics:
    """Compute all metrics for a single window.

    Args:
        trades: Trades in the window.
        tob: Top-of-book snapshots in the window.

    Returns:
        WindowMetrics with all computed values.
    """
    (trade_count, trade_volume, avg_trade_size, vwap, realized_vol,
     min_price, max_price) = compute_trade_metrics(trades)

    (avg_spread, avg_spread_bps, avg_midprice) = compute_tob_metrics(tob)

    return WindowMetrics(
        trade_count=trade_count,
        trade_volume=trade_volume,
        avg_trade_size=avg_trade_size,
        vwap=vwap,
        avg_spread=avg_spread,
        avg_spread_bps=avg_spread_bps,
        avg_midprice=avg_midprice,
        realized_volatility=realized_vol,
        min_price=min_price,
        max_price=max_price,
    )


def compute_event_metrics(window: EventWindow) -> EventMetrics:
    """Compute metrics for both pre and post windows of an event.

    Args:
        window: EventWindow containing pre/post data.

    Returns:
        EventMetrics with pre and post metrics.
    """
    pre_metrics = compute_window_metrics(window.pre_trades, window.pre_tob)
    post_metrics = compute_window_metrics(window.post_trades, window.post_tob)

    return EventMetrics(
        window_id=window.window_id,
        symbol=window.event.symbol,
        event_timestamp=window.event.timestamp.isoformat(),
        event_direction=window.event.direction.value,
        event_magnitude=window.event.magnitude,
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
    )


def compute_all_metrics(windows: List[EventWindow]) -> List[EventMetrics]:
    """Compute metrics for all event windows.

    Args:
        windows: List of EventWindow objects.

    Returns:
        List of EventMetrics for each window.
    """
    return [compute_event_metrics(w) for w in windows]


def save_metrics_json(
    metrics: List[EventMetrics],
    output_path: Union[Path, str],
) -> str:
    """Save metrics as JSON file.

    Args:
        metrics: List of EventMetrics to save.
        output_path: Path to output JSON file.

    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [m.to_dict() for m in metrics]
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


def save_metrics_csv(
    metrics: List[EventMetrics],
    output_path: Union[Path, str],
) -> str:
    """Save metrics as CSV file.

    Args:
        metrics: List of EventMetrics to save.
        output_path: Path to output CSV file.

    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        # Write empty CSV with headers
        fieldnames = list(EventMetrics(
            window_id="", symbol="", event_timestamp="",
            event_direction="", event_magnitude=0.0,
            pre_metrics=WindowMetrics(0, 0.0, None, None, None, None, None, None, None, None),
            post_metrics=WindowMetrics(0, 0.0, None, None, None, None, None, None, None, None),
        ).to_dict().keys())
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return str(output_path)

    fieldnames = list(metrics[0].to_dict().keys())

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            writer.writerow(m.to_dict())

    return str(output_path)


def save_metrics(
    metrics: List[EventMetrics],
    output_dir: Union[Path, str],
    basename: str = "event_metrics",
) -> dict:
    """Save metrics as both JSON and CSV files.

    Args:
        metrics: List of EventMetrics to save.
        output_dir: Directory to save files to.
        basename: Base filename (without extension).

    Returns:
        Dictionary with paths to saved files.
    """
    output_dir = Path(output_dir)

    json_path = save_metrics_json(metrics, output_dir / f"{basename}.json")
    csv_path = save_metrics_csv(metrics, output_dir / f"{basename}.csv")

    return {
        "json": json_path,
        "csv": csv_path,
    }
