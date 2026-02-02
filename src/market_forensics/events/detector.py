"""Price-shock event detector.

Detects moments where price moves by a configurable threshold within a rolling window.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Union

from ..data.models import Event, EventDirection, TopOfBook, Trade


class DetectorError(Exception):
    """Exception raised for detector-related errors."""

    pass


def detect_price_shocks(
    data: Union[List[Trade], List[TopOfBook]],
    threshold_pct: float,
    window_seconds: float,
) -> List[Event]:
    """Detect price shock events in trade or top-of-book data.

    A price shock is detected when the price moves by >= threshold_pct within
    a rolling window of window_seconds.

    Args:
        data: List of Trade or TopOfBook records, must be sorted by timestamp.
        threshold_pct: Minimum percentage move to trigger an event (e.g., 1.0 for 1%).
        window_seconds: Rolling window duration in seconds.

    Returns:
        List of detected Event objects, sorted by timestamp.

    Raises:
        DetectorError: If input validation fails.
    """
    if threshold_pct <= 0:
        raise DetectorError(f"threshold_pct must be positive, got {threshold_pct}")
    if window_seconds <= 0:
        raise DetectorError(f"window_seconds must be positive, got {window_seconds}")

    if not data:
        return []

    # Validate and extract price series
    prices = _extract_prices(data)
    timestamps = [_get_timestamp(d) for d in data]
    symbol = _get_symbol(data[0])

    # Validate timestamps are sorted
    _validate_sorted_timestamps(timestamps)

    events: List[Event] = []
    window_delta = timedelta(seconds=window_seconds)

    # Sliding window approach: for each point, look back within the window
    # and check if the price has moved by >= threshold_pct
    for i in range(len(data)):
        current_ts = timestamps[i]
        current_price = prices[i]
        window_start = current_ts - window_delta

        # Find the earliest index within the window
        j = i
        while j > 0 and timestamps[j - 1] >= window_start:
            j -= 1

        # Get min and max prices within the window up to current point
        window_prices = prices[j : i + 1]
        if len(window_prices) < 2:
            continue

        min_price = min(window_prices)
        max_price = max(window_prices)

        # Check if there's a price shock
        # We look for the move from the earliest extreme to current
        reference_price = prices[j]
        if reference_price == 0:
            continue

        pct_change = ((current_price - reference_price) / reference_price) * 100

        if abs(pct_change) >= threshold_pct:
            direction = EventDirection.UP if pct_change > 0 else EventDirection.DOWN

            # Avoid duplicate events too close together
            # Only emit if this is the first event or sufficiently distant from last
            if events:
                last_event_ts = events[-1].timestamp
                if (current_ts - last_event_ts) < window_delta:
                    # Update existing event if magnitude is larger
                    if abs(pct_change) > abs(events[-1].magnitude):
                        # Replace with larger magnitude event
                        events[-1] = Event(
                            timestamp=current_ts,
                            symbol=symbol,
                            event_type="price_shock",
                            direction=direction,
                            magnitude=pct_change,
                            metadata={
                                "reference_price": reference_price,
                                "current_price": current_price,
                                "threshold_pct": threshold_pct,
                                "window_seconds": window_seconds,
                            },
                        )
                    continue

            events.append(
                Event(
                    timestamp=current_ts,
                    symbol=symbol,
                    event_type="price_shock",
                    direction=direction,
                    magnitude=pct_change,
                    metadata={
                        "reference_price": reference_price,
                        "current_price": current_price,
                        "threshold_pct": threshold_pct,
                        "window_seconds": window_seconds,
                    },
                )
            )

    return events


def detect_price_shocks_from_config(
    data: Union[List[Trade], List[TopOfBook]],
    config: dict,
) -> List[Event]:
    """Detect price shocks using configuration dictionary.

    Args:
        data: List of Trade or TopOfBook records.
        config: Configuration dictionary with 'event_detection' section.

    Returns:
        List of detected Event objects.

    Raises:
        DetectorError: If config is missing required keys.
    """
    try:
        event_config = config["event_detection"]
        threshold_pct = event_config["price_shock_threshold_pct"]
        window_seconds = event_config["rolling_window_seconds"]
    except KeyError as e:
        raise DetectorError(f"Missing required config key: {e}")

    return detect_price_shocks(data, threshold_pct, window_seconds)


def _extract_prices(data: Union[List[Trade], List[TopOfBook]]) -> List[float]:
    """Extract prices from trade or top-of-book data."""
    if not data:
        return []

    if isinstance(data[0], Trade):
        return [t.price for t in data]
    elif isinstance(data[0], TopOfBook):
        return [t.mid_price for t in data]
    else:
        raise DetectorError(f"Unsupported data type: {type(data[0])}")


def _get_timestamp(record: Union[Trade, TopOfBook]) -> datetime:
    """Get timestamp from a data record."""
    return record.timestamp


def _get_symbol(record: Union[Trade, TopOfBook]) -> str:
    """Get symbol from a data record."""
    return record.symbol


def _validate_sorted_timestamps(timestamps: List[datetime]) -> None:
    """Validate that timestamps are sorted in ascending order.

    Raises:
        DetectorError: If timestamps are not sorted or contain duplicates that
                       would indicate data quality issues.
    """
    for i in range(1, len(timestamps)):
        if timestamps[i] < timestamps[i - 1]:
            raise DetectorError(
                f"Timestamps must be sorted in ascending order. "
                f"Found {timestamps[i]} after {timestamps[i - 1]} at index {i}"
            )
