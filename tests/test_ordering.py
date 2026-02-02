"""Tests for change ordering detection.

Tests for determining 'what changes first' within events (MF-006).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from market_forensics.data.models import (
    Event,
    EventDirection,
    Side,
    TopOfBook,
    Trade,
)
from market_forensics.events.ordering import (
    EventOrdering,
    OnsetDetection,
    OnsetType,
    OrderingError,
    analyze_all_orderings,
    analyze_event_ordering,
    analyze_event_ordering_from_config,
    detect_price_onset,
    detect_spread_onset,
    detect_volume_onset,
    determine_ordering,
    save_orderings,
)
from market_forensics.windows.extractor import EventWindow


def _make_trade(
    ts: datetime, price: float, size: float = 1.0, symbol: str = "BTC-USDT"
) -> Trade:
    """Helper to create a Trade for testing."""
    return Trade(
        timestamp=ts,
        symbol=symbol,
        price=price,
        size=size,
        side=Side.BUY,
        trade_id=None,
    )


def _make_tob(
    ts: datetime, mid: float, spread: float = 2.0, symbol: str = "BTC-USDT"
) -> TopOfBook:
    """Helper to create a TopOfBook for testing."""
    half_spread = spread / 2
    return TopOfBook(
        timestamp=ts,
        symbol=symbol,
        bid_price=mid - half_spread,
        bid_size=1.0,
        ask_price=mid + half_spread,
        ask_size=1.0,
    )


def _make_event(
    ts: datetime, symbol: str = "BTC-USDT", direction: EventDirection = EventDirection.DOWN
) -> Event:
    """Helper to create an Event for testing."""
    return Event(
        timestamp=ts,
        symbol=symbol,
        event_type="price_shock",
        direction=direction,
        magnitude=-2.5 if direction == EventDirection.DOWN else 2.5,
        metadata={"test": True},
    )


def _make_event_window(
    event: Event,
    pre_trades: List[Trade],
    post_trades: List[Trade],
    pre_tob: List[TopOfBook],
    post_tob: List[TopOfBook],
) -> EventWindow:
    """Helper to create an EventWindow for testing."""
    return EventWindow(
        event=event,
        pre_trades=pre_trades,
        post_trades=post_trades,
        pre_tob=pre_tob,
        post_tob=post_tob,
        pre_seconds=60,
        post_seconds=60,
    )


class TestDetectSpreadOnset:
    """Tests for spread/liquidity onset detection."""

    def test_empty_data_returns_no_onset(self) -> None:
        """Empty data should return no onset time."""
        result = detect_spread_onset([], [], k_std=2.0)

        assert result.onset_type == OnsetType.LIQUIDITY
        assert result.onset_time is None
        assert result.baseline_value is None

    def test_detects_spread_widening(self) -> None:
        """Should detect when spread widens beyond threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Pre-window: stable spread of 2.0
        pre_tob = [
            _make_tob(base_time - timedelta(seconds=30), mid=100.0, spread=2.0),
            _make_tob(base_time - timedelta(seconds=20), mid=100.0, spread=2.0),
            _make_tob(base_time - timedelta(seconds=10), mid=100.0, spread=2.0),
        ]

        # Post-window: spread widens significantly
        post_tob = [
            _make_tob(base_time, mid=99.0, spread=2.0),  # normal
            _make_tob(base_time + timedelta(seconds=10), mid=98.0, spread=5.0),  # widened
            _make_tob(base_time + timedelta(seconds=20), mid=97.0, spread=8.0),  # more widened
        ]

        result = detect_spread_onset(pre_tob, post_tob, k_std=2.0)

        assert result.onset_type == OnsetType.LIQUIDITY
        assert result.onset_time is not None
        # Should detect at +10s when spread jumps to 5.0
        assert result.onset_time == post_tob[1].timestamp
        assert result.baseline_value == 2.0

    def test_no_onset_if_spread_stays_normal(self) -> None:
        """No onset if spread doesn't exceed threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        pre_tob = [
            _make_tob(base_time - timedelta(seconds=30), mid=100.0, spread=2.0),
            _make_tob(base_time - timedelta(seconds=20), mid=100.0, spread=2.1),
            _make_tob(base_time - timedelta(seconds=10), mid=100.0, spread=1.9),
        ]

        # Post-window: spread stays within normal range
        # With baseline=2.0, std~0.08, threshold~2.16
        # Keep post spreads below that
        post_tob = [
            _make_tob(base_time, mid=99.0, spread=2.0),
            _make_tob(base_time + timedelta(seconds=10), mid=98.0, spread=2.1),
        ]

        result = detect_spread_onset(pre_tob, post_tob, k_std=2.0)

        assert result.onset_time is None  # No significant change


class TestDetectVolumeOnset:
    """Tests for volume onset detection."""

    def test_empty_data_returns_no_onset(self) -> None:
        """Empty data should return no onset time."""
        result = detect_volume_onset([], [], k_std=2.0)

        assert result.onset_type == OnsetType.VOLUME
        assert result.onset_time is None

    def test_detects_volume_spike(self) -> None:
        """Should detect when volume spikes beyond threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Pre-window: low, consistent volume
        pre_trades = [
            _make_trade(base_time - timedelta(seconds=25), 100.0, size=0.1),
            _make_trade(base_time - timedelta(seconds=20), 100.0, size=0.1),
            _make_trade(base_time - timedelta(seconds=15), 100.0, size=0.1),
            _make_trade(base_time - timedelta(seconds=10), 100.0, size=0.1),
            _make_trade(base_time - timedelta(seconds=5), 100.0, size=0.1),
        ]

        # Post-window: volume spike
        post_trades = [
            _make_trade(base_time, 99.0, size=0.1),  # normal
            _make_trade(base_time + timedelta(seconds=1), 98.0, size=1.0),  # spike
            _make_trade(base_time + timedelta(seconds=2), 97.0, size=2.0),  # more spike
        ]

        result = detect_volume_onset(pre_trades, post_trades, k_std=2.0, bucket_seconds=5.0)

        assert result.onset_type == OnsetType.VOLUME
        # Volume should exceed threshold in first post bucket


class TestDetectPriceOnset:
    """Tests for price onset detection."""

    def test_empty_data_returns_no_onset(self) -> None:
        """Empty data should return no onset time."""
        result = detect_price_onset([], [], k_std=2.0, event_direction="down")

        assert result.onset_type == OnsetType.PRICE
        assert result.onset_time is None

    def test_detects_downward_price_move(self) -> None:
        """Should detect when price moves down beyond threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Pre-window: stable price around 100
        pre_tob = [
            _make_tob(base_time - timedelta(seconds=30), mid=100.0),
            _make_tob(base_time - timedelta(seconds=20), mid=100.1),
            _make_tob(base_time - timedelta(seconds=10), mid=99.9),
        ]

        # Post-window: price drops
        post_tob = [
            _make_tob(base_time, mid=99.8),  # small drop
            _make_tob(base_time + timedelta(seconds=10), mid=98.0),  # significant drop
        ]

        result = detect_price_onset(pre_tob, post_tob, k_std=2.0, event_direction="down")

        assert result.onset_type == OnsetType.PRICE
        assert result.onset_time is not None
        assert result.baseline_value is not None
        # Threshold should be below baseline for down moves

    def test_detects_upward_price_move(self) -> None:
        """Should detect when price moves up beyond threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        pre_tob = [
            _make_tob(base_time - timedelta(seconds=30), mid=100.0),
            _make_tob(base_time - timedelta(seconds=20), mid=100.1),
            _make_tob(base_time - timedelta(seconds=10), mid=99.9),
        ]

        # Post-window: price rises
        post_tob = [
            _make_tob(base_time, mid=100.2),  # small rise
            _make_tob(base_time + timedelta(seconds=10), mid=102.0),  # significant rise
        ]

        result = detect_price_onset(pre_tob, post_tob, k_std=2.0, event_direction="up")

        assert result.onset_type == OnsetType.PRICE
        assert result.onset_time is not None


class TestDetermineOrdering:
    """Tests for ordering determination."""

    def test_all_none_returns_undetermined(self) -> None:
        """If no onsets detected, should return undetermined."""
        liquidity = OnsetDetection(
            OnsetType.LIQUIDITY, None, None, None, None, None, 2.0
        )
        volume = OnsetDetection(
            OnsetType.VOLUME, None, None, None, None, None, 2.0
        )
        price = OnsetDetection(
            OnsetType.PRICE, None, None, None, None, None, 2.0
        )

        ordering, classification = determine_ordering(liquidity, volume, price)

        assert ordering == []
        assert classification == "undetermined"

    def test_liquidity_first(self) -> None:
        """If liquidity onset is first, should classify as liquidity-first."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        liquidity = OnsetDetection(
            OnsetType.LIQUIDITY, base_time, 2.0, 0.1, 2.2, 2.5, 2.0
        )
        volume = OnsetDetection(
            OnsetType.VOLUME, base_time + timedelta(seconds=5), 0.1, 0.01, 0.12, 0.2, 2.0
        )
        price = OnsetDetection(
            OnsetType.PRICE, base_time + timedelta(seconds=10), 100.0, 0.1, 99.8, 99.5, 2.0
        )

        ordering, classification = determine_ordering(liquidity, volume, price)

        assert ordering == [OnsetType.LIQUIDITY, OnsetType.VOLUME, OnsetType.PRICE]
        assert classification == "liquidity-first"

    def test_volume_first(self) -> None:
        """If volume onset is first, should classify as volume-first."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        liquidity = OnsetDetection(
            OnsetType.LIQUIDITY, base_time + timedelta(seconds=10), 2.0, 0.1, 2.2, 2.5, 2.0
        )
        volume = OnsetDetection(
            OnsetType.VOLUME, base_time, 0.1, 0.01, 0.12, 0.2, 2.0
        )
        price = OnsetDetection(
            OnsetType.PRICE, base_time + timedelta(seconds=5), 100.0, 0.1, 99.8, 99.5, 2.0
        )

        ordering, classification = determine_ordering(liquidity, volume, price)

        assert ordering[0] == OnsetType.VOLUME
        assert classification == "volume-first"

    def test_price_first(self) -> None:
        """If price onset is first, should classify as price-first."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        liquidity = OnsetDetection(
            OnsetType.LIQUIDITY, base_time + timedelta(seconds=10), 2.0, 0.1, 2.2, 2.5, 2.0
        )
        volume = OnsetDetection(
            OnsetType.VOLUME, base_time + timedelta(seconds=5), 0.1, 0.01, 0.12, 0.2, 2.0
        )
        price = OnsetDetection(
            OnsetType.PRICE, base_time, 100.0, 0.1, 99.8, 99.5, 2.0
        )

        ordering, classification = determine_ordering(liquidity, volume, price)

        assert ordering[0] == OnsetType.PRICE
        assert classification == "price-first"

    def test_partial_onsets(self) -> None:
        """Should handle cases where only some onsets are detected."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        liquidity = OnsetDetection(
            OnsetType.LIQUIDITY, None, None, None, None, None, 2.0  # No onset
        )
        volume = OnsetDetection(
            OnsetType.VOLUME, base_time, 0.1, 0.01, 0.12, 0.2, 2.0
        )
        price = OnsetDetection(
            OnsetType.PRICE, base_time + timedelta(seconds=5), 100.0, 0.1, 99.8, 99.5, 2.0
        )

        ordering, classification = determine_ordering(liquidity, volume, price)

        assert len(ordering) == 2
        assert OnsetType.LIQUIDITY not in ordering
        assert classification == "volume-first"


class TestAnalyzeEventOrdering:
    """Tests for full event ordering analysis."""

    def test_analyzes_event_window(self) -> None:
        """Should produce complete ordering analysis."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(base_time, direction=EventDirection.DOWN)

        pre_trades = [_make_trade(base_time - timedelta(seconds=30), 100.0)]
        post_trades = [_make_trade(base_time, 98.0)]
        pre_tob = [_make_tob(base_time - timedelta(seconds=30), mid=100.0)]
        post_tob = [_make_tob(base_time, mid=98.0)]

        window = _make_event_window(event, pre_trades, post_trades, pre_tob, post_tob)
        result = analyze_event_ordering(window, k_std=2.0)

        assert result.window_id == window.window_id
        assert result.symbol == "BTC-USDT"
        assert result.event_direction == "down"
        assert result.classification in [
            "liquidity-first", "volume-first", "price-first", "undetermined"
        ]

    def test_from_config_uses_config_values(self) -> None:
        """Should use k_std from config."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])

        config = {
            "ordering_detection": {
                "threshold_std_multiplier": 3.0,
            }
        }

        result = analyze_event_ordering_from_config(window, config)
        assert result.liquidity_onset.k_std == 3.0

    def test_missing_config_raises_error(self) -> None:
        """Missing config should raise OrderingError."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])

        error_raised = False
        try:
            analyze_event_ordering_from_config(window, {})
        except OrderingError:
            error_raised = True

        assert error_raised, "Expected OrderingError for missing config"


class TestAnalyzeAllOrderings:
    """Tests for batch ordering analysis."""

    def test_empty_windows_returns_empty_list(self) -> None:
        """Empty windows should return empty orderings."""
        result = analyze_all_orderings([])
        assert result == []

    def test_analyzes_multiple_windows(self) -> None:
        """Should analyze all windows."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        windows = [
            _make_event_window(_make_event(base_time), [], [], [], []),
            _make_event_window(
                _make_event(base_time + timedelta(minutes=5)), [], [], [], []
            ),
        ]

        result = analyze_all_orderings(windows)
        assert len(result) == 2


class TestSaveOrderings:
    """Tests for ordering persistence."""

    def test_save_orderings_creates_files(self) -> None:
        """Should create JSON and CSV files."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])
        orderings = [analyze_event_ordering(window)]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = save_orderings(orderings, temp_dir)

            assert Path(paths["json"]).exists()
            assert Path(paths["csv"]).exists()

            # Verify JSON content
            with open(paths["json"]) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["symbol"] == "BTC-USDT"
        finally:
            shutil.rmtree(temp_dir)


def run_all_tests() -> None:
    """Run all tests and print results.

    This can be run standalone: PYTHONPATH=src python3 -m tests.test_ordering
    """
    test_classes = [
        TestDetectSpreadOnset,
        TestDetectVolumeOnset,
        TestDetectPriceOnset,
        TestDetermineOrdering,
        TestAnalyzeEventOrdering,
        TestAnalyzeAllOrderings,
        TestSaveOrderings,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                method = getattr(instance, method_name)
                try:
                    method()
                    print(f"  PASS: {test_class.__name__}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  FAIL: {test_class.__name__}.{method_name} - {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ERROR: {test_class.__name__}.{method_name} - {e}")
                    failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all_tests()
