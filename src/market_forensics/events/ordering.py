"""Change ordering detection within events.

Determines the sequence of changes (liquidity, volume, price) around events.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..data.models import TopOfBook, Trade
from ..windows.extractor import EventWindow


class OrderingError(Exception):
    """Exception raised for ordering detection errors."""

    pass


class OnsetType(Enum):
    """Type of onset detected."""

    LIQUIDITY = "liquidity"  # Spread change
    VOLUME = "volume"  # Trade volume/activity change
    PRICE = "price"  # Price movement


@dataclass
class OnsetDetection:
    """Result of onset detection for a single signal.

    Attributes:
        onset_type: Type of signal (liquidity, volume, price).
        onset_time: Timestamp when the signal first exceeded threshold.
        baseline_value: The baseline value computed from pre-window.
        baseline_std: Standard deviation of baseline (None if insufficient data).
        threshold_value: The threshold value used (baseline + k*std).
        onset_value: The value at onset time.
        k_std: Number of standard deviations used for threshold.
    """

    onset_type: OnsetType
    onset_time: Optional[datetime]
    baseline_value: Optional[float]
    baseline_std: Optional[float]
    threshold_value: Optional[float]
    onset_value: Optional[float]
    k_std: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "onset_type": self.onset_type.value,
            "onset_time": self.onset_time.isoformat() if self.onset_time else None,
            "baseline_value": self.baseline_value,
            "baseline_std": self.baseline_std,
            "threshold_value": self.threshold_value,
            "onset_value": self.onset_value,
            "k_std": self.k_std,
        }


@dataclass
class EventOrdering:
    """Complete ordering analysis for an event.

    Attributes:
        window_id: Unique identifier for the window.
        symbol: Trading pair symbol.
        event_timestamp: Event timestamp.
        event_direction: Event direction (up/down).
        liquidity_onset: Onset detection for spread/liquidity.
        volume_onset: Onset detection for trade volume.
        price_onset: Onset detection for price movement.
        ordering: List of onset types in order of occurrence.
        classification: String classification (e.g., "liquidity-first").
    """

    window_id: str
    symbol: str
    event_timestamp: str
    event_direction: str
    liquidity_onset: OnsetDetection
    volume_onset: OnsetDetection
    price_onset: OnsetDetection
    ordering: List[OnsetType]
    classification: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "window_id": self.window_id,
            "symbol": self.symbol,
            "event_timestamp": self.event_timestamp,
            "event_direction": self.event_direction,
            "liquidity_onset_time": (
                self.liquidity_onset.onset_time.isoformat()
                if self.liquidity_onset.onset_time else None
            ),
            "volume_onset_time": (
                self.volume_onset.onset_time.isoformat()
                if self.volume_onset.onset_time else None
            ),
            "price_onset_time": (
                self.price_onset.onset_time.isoformat()
                if self.price_onset.onset_time else None
            ),
            "ordering": [o.value for o in self.ordering],
            "classification": self.classification,
            "liquidity_baseline": self.liquidity_onset.baseline_value,
            "liquidity_threshold": self.liquidity_onset.threshold_value,
            "volume_baseline": self.volume_onset.baseline_value,
            "volume_threshold": self.volume_onset.threshold_value,
            "price_baseline": self.price_onset.baseline_value,
            "price_threshold": self.price_onset.threshold_value,
        }


def _compute_baseline_stats(values: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """Compute mean and standard deviation of values.

    Args:
        values: List of values.

    Returns:
        Tuple of (mean, std) or (None, None) if insufficient data.
    """
    if len(values) < 2:
        if len(values) == 1:
            return (values[0], None)
        return (None, None)

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)

    return (mean, std)


def detect_spread_onset(
    pre_tob: List[TopOfBook],
    post_tob: List[TopOfBook],
    k_std: float,
) -> OnsetDetection:
    """Detect when spread first exceeds baseline + k*std.

    Spread widening indicates liquidity withdrawal.

    Args:
        pre_tob: Pre-event top-of-book data.
        post_tob: Post-event top-of-book data.
        k_std: Number of standard deviations for threshold.

    Returns:
        OnsetDetection for spread/liquidity.
    """
    # Compute baseline from pre-window spreads
    pre_spreads = [t.spread for t in pre_tob]
    baseline, std = _compute_baseline_stats(pre_spreads)

    if baseline is None:
        return OnsetDetection(
            onset_type=OnsetType.LIQUIDITY,
            onset_time=None,
            baseline_value=None,
            baseline_std=None,
            threshold_value=None,
            onset_value=None,
            k_std=k_std,
        )

    # Threshold: baseline + k*std (spread widening)
    # Use a minimum std to avoid division issues
    effective_std = std if std is not None and std > 0 else baseline * 0.01
    threshold = baseline + k_std * effective_std

    # Find first time spread exceeds threshold in post-window
    onset_time = None
    onset_value = None
    for tob in post_tob:
        if tob.spread >= threshold:
            onset_time = tob.timestamp
            onset_value = tob.spread
            break

    return OnsetDetection(
        onset_type=OnsetType.LIQUIDITY,
        onset_time=onset_time,
        baseline_value=baseline,
        baseline_std=std,
        threshold_value=threshold,
        onset_value=onset_value,
        k_std=k_std,
    )


def detect_volume_onset(
    pre_trades: List[Trade],
    post_trades: List[Trade],
    k_std: float,
    bucket_seconds: float = 5.0,
) -> OnsetDetection:
    """Detect when trade volume first exceeds baseline + k*std.

    Volume is aggregated into time buckets.

    Args:
        pre_trades: Pre-event trades.
        post_trades: Post-event trades.
        k_std: Number of standard deviations for threshold.
        bucket_seconds: Duration of each volume bucket.

    Returns:
        OnsetDetection for volume.
    """
    def _bucket_volume(trades: List[Trade], bucket_sec: float) -> List[Tuple[datetime, float]]:
        """Aggregate trade volume into time buckets."""
        if not trades:
            return []

        buckets: Dict[datetime, float] = {}
        for t in trades:
            # Round down to bucket start
            ts = t.timestamp
            bucket_start = ts.replace(
                second=int(ts.second // bucket_sec) * int(bucket_sec),
                microsecond=0,
            )
            buckets[bucket_start] = buckets.get(bucket_start, 0.0) + t.size

        return sorted(buckets.items(), key=lambda x: x[0])

    pre_buckets = _bucket_volume(pre_trades, bucket_seconds)
    post_buckets = _bucket_volume(post_trades, bucket_seconds)

    # Compute baseline from pre-window
    pre_volumes = [v for _, v in pre_buckets]
    baseline, std = _compute_baseline_stats(pre_volumes)

    if baseline is None:
        return OnsetDetection(
            onset_type=OnsetType.VOLUME,
            onset_time=None,
            baseline_value=None,
            baseline_std=None,
            threshold_value=None,
            onset_value=None,
            k_std=k_std,
        )

    # Threshold: baseline + k*std (volume spike)
    effective_std = std if std is not None and std > 0 else baseline * 0.1
    threshold = baseline + k_std * effective_std

    # Find first bucket exceeding threshold
    onset_time = None
    onset_value = None
    for bucket_time, volume in post_buckets:
        if volume >= threshold:
            onset_time = bucket_time
            onset_value = volume
            break

    return OnsetDetection(
        onset_type=OnsetType.VOLUME,
        onset_time=onset_time,
        baseline_value=baseline,
        baseline_std=std,
        threshold_value=threshold,
        onset_value=onset_value,
        k_std=k_std,
    )


def detect_price_onset(
    pre_tob: List[TopOfBook],
    post_tob: List[TopOfBook],
    k_std: float,
    event_direction: str,
) -> OnsetDetection:
    """Detect when price first moves beyond baseline + k*std.

    Uses midprice from top-of-book.

    Args:
        pre_tob: Pre-event top-of-book data.
        post_tob: Post-event top-of-book data.
        k_std: Number of standard deviations for threshold.
        event_direction: Direction of event ("up" or "down").

    Returns:
        OnsetDetection for price movement.
    """
    # Compute baseline from pre-window midprices
    pre_prices = [t.mid_price for t in pre_tob]
    baseline, std = _compute_baseline_stats(pre_prices)

    if baseline is None:
        return OnsetDetection(
            onset_type=OnsetType.PRICE,
            onset_time=None,
            baseline_value=None,
            baseline_std=None,
            threshold_value=None,
            onset_value=None,
            k_std=k_std,
        )

    # For price, direction matters
    # Down event: look for price below baseline - k*std
    # Up event: look for price above baseline + k*std
    effective_std = std if std is not None and std > 0 else baseline * 0.001
    if event_direction == "down":
        threshold = baseline - k_std * effective_std
    else:
        threshold = baseline + k_std * effective_std

    # Find first time price crosses threshold
    onset_time = None
    onset_value = None
    for tob in post_tob:
        if event_direction == "down" and tob.mid_price <= threshold:
            onset_time = tob.timestamp
            onset_value = tob.mid_price
            break
        elif event_direction == "up" and tob.mid_price >= threshold:
            onset_time = tob.timestamp
            onset_value = tob.mid_price
            break

    return OnsetDetection(
        onset_type=OnsetType.PRICE,
        onset_time=onset_time,
        baseline_value=baseline,
        baseline_std=std,
        threshold_value=threshold,
        onset_value=onset_value,
        k_std=k_std,
    )


def determine_ordering(
    liquidity: OnsetDetection,
    volume: OnsetDetection,
    price: OnsetDetection,
) -> Tuple[List[OnsetType], str]:
    """Determine the ordering of onset times.

    Args:
        liquidity: Liquidity/spread onset detection.
        volume: Volume onset detection.
        price: Price onset detection.

    Returns:
        Tuple of (ordered list of OnsetTypes, classification string).
    """
    # Collect detections that have onset times
    detections = []
    if liquidity.onset_time is not None:
        detections.append((liquidity.onset_time, OnsetType.LIQUIDITY))
    if volume.onset_time is not None:
        detections.append((volume.onset_time, OnsetType.VOLUME))
    if price.onset_time is not None:
        detections.append((price.onset_time, OnsetType.PRICE))

    if not detections:
        return ([], "undetermined")

    # Sort by onset time
    detections.sort(key=lambda x: x[0])
    ordering = [d[1] for d in detections]

    # Classify based on what comes first
    first = ordering[0]
    if first == OnsetType.LIQUIDITY:
        classification = "liquidity-first"
    elif first == OnsetType.VOLUME:
        classification = "volume-first"
    else:
        classification = "price-first"

    return (ordering, classification)


def analyze_event_ordering(
    window: EventWindow,
    k_std: float = 2.0,
    volume_bucket_seconds: float = 5.0,
) -> EventOrdering:
    """Analyze the ordering of changes for a single event window.

    Args:
        window: EventWindow with pre/post data.
        k_std: Number of standard deviations for thresholds.
        volume_bucket_seconds: Duration of volume buckets.

    Returns:
        EventOrdering with complete analysis.
    """
    event_direction = window.event.direction.value

    liquidity_onset = detect_spread_onset(
        window.pre_tob, window.post_tob, k_std
    )
    volume_onset = detect_volume_onset(
        window.pre_trades, window.post_trades, k_std, volume_bucket_seconds
    )
    price_onset = detect_price_onset(
        window.pre_tob, window.post_tob, k_std, event_direction
    )

    ordering, classification = determine_ordering(
        liquidity_onset, volume_onset, price_onset
    )

    return EventOrdering(
        window_id=window.window_id,
        symbol=window.event.symbol,
        event_timestamp=window.event.timestamp.isoformat(),
        event_direction=event_direction,
        liquidity_onset=liquidity_onset,
        volume_onset=volume_onset,
        price_onset=price_onset,
        ordering=ordering,
        classification=classification,
    )


def analyze_event_ordering_from_config(
    window: EventWindow,
    config: dict,
) -> EventOrdering:
    """Analyze event ordering using configuration.

    Args:
        window: EventWindow with pre/post data.
        config: Configuration dictionary with 'ordering_detection' section.

    Returns:
        EventOrdering with complete analysis.

    Raises:
        OrderingError: If config is missing required keys.
    """
    try:
        ordering_config = config["ordering_detection"]
        k_std = ordering_config["threshold_std_multiplier"]
    except KeyError as e:
        raise OrderingError(f"Missing required config key: {e}")

    # Volume bucket is optional, default to 5 seconds
    volume_bucket = ordering_config.get("volume_bucket_seconds", 5.0)

    return analyze_event_ordering(window, k_std, volume_bucket)


def analyze_all_orderings(
    windows: List[EventWindow],
    k_std: float = 2.0,
) -> List[EventOrdering]:
    """Analyze ordering for all event windows.

    Args:
        windows: List of EventWindow objects.
        k_std: Number of standard deviations for thresholds.

    Returns:
        List of EventOrdering objects.
    """
    return [analyze_event_ordering(w, k_std) for w in windows]


def save_orderings_json(
    orderings: List[EventOrdering],
    output_path: Union[Path, str],
) -> str:
    """Save orderings as JSON file.

    Args:
        orderings: List of EventOrdering objects.
        output_path: Path to output file.

    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [o.to_dict() for o in orderings]
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


def save_orderings_csv(
    orderings: List[EventOrdering],
    output_path: Union[Path, str],
) -> str:
    """Save orderings as CSV file.

    Args:
        orderings: List of EventOrdering objects.
        output_path: Path to output file.

    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "window_id", "symbol", "event_timestamp", "event_direction",
        "liquidity_onset_time", "volume_onset_time", "price_onset_time",
        "ordering", "classification",
        "liquidity_baseline", "liquidity_threshold",
        "volume_baseline", "volume_threshold",
        "price_baseline", "price_threshold",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for o in orderings:
            row = o.to_dict()
            # Convert ordering list to string
            row["ordering"] = ",".join(row["ordering"])
            writer.writerow(row)

    return str(output_path)


def save_orderings(
    orderings: List[EventOrdering],
    output_dir: Union[Path, str],
    basename: str = "event_orderings",
) -> dict:
    """Save orderings as both JSON and CSV.

    Args:
        orderings: List of EventOrdering objects.
        output_dir: Directory to save files to.
        basename: Base filename.

    Returns:
        Dictionary with paths to saved files.
    """
    output_dir = Path(output_dir)

    json_path = save_orderings_json(orderings, output_dir / f"{basename}.json")
    csv_path = save_orderings_csv(orderings, output_dir / f"{basename}.csv")

    return {
        "json": json_path,
        "csv": csv_path,
    }
