"""Window extraction around detected events.

Extracts standardized pre/post event windows for trades and top-of-book data.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union

from ..data.models import Event, TopOfBook, Trade


class WindowError(Exception):
    """Exception raised for window extraction errors."""

    pass


@dataclass
class EventWindow:
    """Container for extracted pre/post window data around an event.

    Attributes:
        event: The detected event this window is centered on.
        pre_trades: Trades in the pre-event window.
        post_trades: Trades in the post-event window (including event time).
        pre_tob: Top-of-book snapshots in the pre-event window.
        post_tob: Top-of-book snapshots in the post-event window (including event time).
        pre_seconds: Duration of pre-event window in seconds.
        post_seconds: Duration of post-event window in seconds.
    """

    event: Event
    pre_trades: List[Trade]
    post_trades: List[Trade]
    pre_tob: List[TopOfBook]
    post_tob: List[TopOfBook]
    pre_seconds: float
    post_seconds: float

    @property
    def window_id(self) -> str:
        """Generate a unique identifier for this window."""
        ts_str = self.event.timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{self.event.symbol}_{ts_str}_{self.event.event_type}"


def extract_window(
    event: Event,
    trades: List[Trade],
    tob: List[TopOfBook],
    pre_seconds: float,
    post_seconds: float,
) -> EventWindow:
    """Extract pre/post windows for a single event.

    The pre-window contains data from (event_time - pre_seconds, event_time).
    The post-window contains data from [event_time, event_time + post_seconds).

    Args:
        event: The detected event to center the window on.
        trades: Full list of trades (must be sorted by timestamp).
        tob: Full list of top-of-book snapshots (must be sorted by timestamp).
        pre_seconds: Duration of pre-event window in seconds.
        post_seconds: Duration of post-event window in seconds.

    Returns:
        EventWindow containing the extracted data.

    Raises:
        WindowError: If parameters are invalid.
    """
    if pre_seconds < 0:
        raise WindowError(f"pre_seconds must be non-negative, got {pre_seconds}")
    if post_seconds < 0:
        raise WindowError(f"post_seconds must be non-negative, got {post_seconds}")

    event_time = event.timestamp
    pre_start = event_time - timedelta(seconds=pre_seconds)
    post_end = event_time + timedelta(seconds=post_seconds)

    # Extract trades in windows
    pre_trades = [
        t for t in trades
        if pre_start < t.timestamp < event_time and t.symbol == event.symbol
    ]
    post_trades = [
        t for t in trades
        if event_time <= t.timestamp < post_end and t.symbol == event.symbol
    ]

    # Extract top-of-book in windows
    pre_tob = [
        t for t in tob
        if pre_start < t.timestamp < event_time and t.symbol == event.symbol
    ]
    post_tob = [
        t for t in tob
        if event_time <= t.timestamp < post_end and t.symbol == event.symbol
    ]

    return EventWindow(
        event=event,
        pre_trades=pre_trades,
        post_trades=post_trades,
        pre_tob=pre_tob,
        post_tob=post_tob,
        pre_seconds=pre_seconds,
        post_seconds=post_seconds,
    )


def extract_windows(
    events: List[Event],
    trades: List[Trade],
    tob: List[TopOfBook],
    pre_seconds: float,
    post_seconds: float,
    overlap_strategy: str = "keep_first",
) -> List[EventWindow]:
    """Extract windows for multiple events with overlap handling.

    Overlapping events are handled deterministically based on the strategy:
    - "keep_first": Keep the first event, skip subsequent overlapping events.
                    An event overlaps if its timestamp falls within the window
                    of a previous event (pre_start to post_end).

    Args:
        events: List of detected events (should be sorted by timestamp).
        trades: Full list of trades.
        tob: Full list of top-of-book snapshots.
        pre_seconds: Duration of pre-event window in seconds.
        post_seconds: Duration of post-event window in seconds.
        overlap_strategy: How to handle overlapping events ("keep_first").

    Returns:
        List of EventWindow objects for non-overlapping events.

    Raises:
        WindowError: If parameters are invalid or strategy is unknown.
    """
    if overlap_strategy not in ("keep_first",):
        raise WindowError(
            f"Unknown overlap_strategy: {overlap_strategy}. Supported: 'keep_first'"
        )

    if not events:
        return []

    # Sort events by timestamp to ensure deterministic processing
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    windows: List[EventWindow] = []
    excluded_until: Optional[datetime] = None

    for event in sorted_events:
        # Check if this event overlaps with a previously processed window
        if excluded_until is not None and event.timestamp < excluded_until:
            # Skip this event as it falls within a previous window
            continue

        # Extract window for this event
        window = extract_window(event, trades, tob, pre_seconds, post_seconds)
        windows.append(window)

        # Update the exclusion boundary (end of this event's post-window)
        excluded_until = event.timestamp + timedelta(seconds=post_seconds)

    return windows


def extract_windows_from_config(
    events: List[Event],
    trades: List[Trade],
    tob: List[TopOfBook],
    config: dict,
) -> List[EventWindow]:
    """Extract windows using configuration dictionary.

    Args:
        events: List of detected events.
        trades: Full list of trades.
        tob: Full list of top-of-book snapshots.
        config: Configuration dictionary with 'windows' section.

    Returns:
        List of EventWindow objects.

    Raises:
        WindowError: If config is missing required keys.
    """
    try:
        window_config = config["windows"]
        pre_seconds = window_config["pre_event_seconds"]
        post_seconds = window_config["post_event_seconds"]
    except KeyError as e:
        raise WindowError(f"Missing required config key: {e}")

    return extract_windows(events, trades, tob, pre_seconds, post_seconds)


def save_window(
    window: EventWindow,
    output_dir: Union[Path, str],
) -> dict:
    """Save an event window to the output directory.

    Creates files:
    - {window_id}_event.json: Event metadata
    - {window_id}_pre_trades.csv: Pre-window trades
    - {window_id}_post_trades.csv: Post-window trades
    - {window_id}_pre_tob.csv: Pre-window top-of-book
    - {window_id}_post_tob.csv: Post-window top-of-book

    Args:
        window: The EventWindow to save.
        output_dir: Directory to save files to.

    Returns:
        Dictionary with paths to all saved files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    window_id = window.window_id
    paths = {}

    # Save event metadata
    event_path = output_dir / f"{window_id}_event.json"
    event_data = {
        "window_id": window_id,
        "event_timestamp": window.event.timestamp.isoformat(),
        "symbol": window.event.symbol,
        "event_type": window.event.event_type,
        "direction": window.event.direction.value,
        "magnitude": window.event.magnitude,
        "metadata": window.event.metadata,
        "pre_seconds": window.pre_seconds,
        "post_seconds": window.post_seconds,
        "pre_trades_count": len(window.pre_trades),
        "post_trades_count": len(window.post_trades),
        "pre_tob_count": len(window.pre_tob),
        "post_tob_count": len(window.post_tob),
    }
    with open(event_path, "w") as f:
        json.dump(event_data, f, indent=2)
    paths["event"] = str(event_path)

    # Save pre-window trades
    pre_trades_path = output_dir / f"{window_id}_pre_trades.csv"
    _save_trades_csv(window.pre_trades, pre_trades_path)
    paths["pre_trades"] = str(pre_trades_path)

    # Save post-window trades
    post_trades_path = output_dir / f"{window_id}_post_trades.csv"
    _save_trades_csv(window.post_trades, post_trades_path)
    paths["post_trades"] = str(post_trades_path)

    # Save pre-window top-of-book
    pre_tob_path = output_dir / f"{window_id}_pre_tob.csv"
    _save_tob_csv(window.pre_tob, pre_tob_path)
    paths["pre_tob"] = str(pre_tob_path)

    # Save post-window top-of-book
    post_tob_path = output_dir / f"{window_id}_post_tob.csv"
    _save_tob_csv(window.post_tob, post_tob_path)
    paths["post_tob"] = str(post_tob_path)

    return paths


def save_windows(
    windows: List[EventWindow],
    output_dir: Union[Path, str],
) -> List[dict]:
    """Save multiple event windows to the output directory.

    Args:
        windows: List of EventWindow objects to save.
        output_dir: Directory to save files to.

    Returns:
        List of dictionaries with paths to all saved files for each window.
    """
    return [save_window(w, output_dir) for w in windows]


def _save_trades_csv(trades: List[Trade], path: Path) -> None:
    """Save trades to a CSV file."""
    fieldnames = ["timestamp", "symbol", "price", "size", "side", "trade_id"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow({
                "timestamp": trade.timestamp.isoformat(),
                "symbol": trade.symbol,
                "price": trade.price,
                "size": trade.size,
                "side": trade.side.value,
                "trade_id": trade.trade_id or "",
            })


def _save_tob_csv(tob_list: List[TopOfBook], path: Path) -> None:
    """Save top-of-book snapshots to a CSV file."""
    fieldnames = [
        "timestamp", "symbol", "bid_price", "bid_size", "ask_price", "ask_size"
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tob in tob_list:
            writer.writerow({
                "timestamp": tob.timestamp.isoformat(),
                "symbol": tob.symbol,
                "bid_price": tob.bid_price,
                "bid_size": tob.bid_size,
                "ask_price": tob.ask_price,
                "ask_size": tob.ask_size,
            })
