"""Tests for window extractor module.

Tests for extracting pre/post event windows around detected events (MF-004).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
import tempfile
import shutil

from market_forensics.data.models import (
    Event,
    EventDirection,
    Side,
    TopOfBook,
    Trade,
)
from market_forensics.windows.extractor import (
    EventWindow,
    WindowError,
    extract_window,
    extract_windows,
    extract_windows_from_config,
    save_window,
    save_windows,
)


def _make_trade(
    ts: datetime, price: float, symbol: str = "BTC-USDT"
) -> Trade:
    """Helper to create a Trade for testing."""
    return Trade(
        timestamp=ts,
        symbol=symbol,
        price=price,
        size=1.0,
        side=Side.BUY,
        trade_id=None,
    )


def _make_tob(
    ts: datetime, mid: float, spread: float = 1.0, symbol: str = "BTC-USDT"
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


class TestExtractWindowBasic:
    """Basic functionality tests for single window extraction."""

    def test_extracts_pre_and_post_trades(self) -> None:
        """Should correctly extract trades before and after event."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        # Create trades: 3 before event, 3 at/after event
        trades = [
            _make_trade(base_time - timedelta(seconds=120), 100.0),  # pre
            _make_trade(base_time - timedelta(seconds=60), 100.5),   # pre
            _make_trade(base_time - timedelta(seconds=30), 101.0),   # pre
            _make_trade(base_time, 98.0),                            # post (event time)
            _make_trade(base_time + timedelta(seconds=30), 97.5),    # post
            _make_trade(base_time + timedelta(seconds=60), 98.5),    # post
        ]

        window = extract_window(
            event=event,
            trades=trades,
            tob=[],
            pre_seconds=300,
            post_seconds=300,
        )

        assert len(window.pre_trades) == 3, f"Expected 3 pre-trades, got {len(window.pre_trades)}"
        assert len(window.post_trades) == 3, f"Expected 3 post-trades, got {len(window.post_trades)}"

    def test_extracts_pre_and_post_tob(self) -> None:
        """Should correctly extract top-of-book before and after event."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        tob = [
            _make_tob(base_time - timedelta(seconds=120), 100.0),  # pre
            _make_tob(base_time - timedelta(seconds=60), 100.5),   # pre
            _make_tob(base_time, 98.0),                            # post
            _make_tob(base_time + timedelta(seconds=60), 98.5),    # post
        ]

        window = extract_window(
            event=event,
            trades=[],
            tob=tob,
            pre_seconds=300,
            post_seconds=300,
        )

        assert len(window.pre_tob) == 2, f"Expected 2 pre-tob, got {len(window.pre_tob)}"
        assert len(window.post_tob) == 2, f"Expected 2 post-tob, got {len(window.post_tob)}"

    def test_window_boundaries_exclusive_pre(self) -> None:
        """Pre-window should exclude exact start boundary."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        # Trade at exact pre-window start (event - 60s) should NOT be included
        trades = [
            _make_trade(base_time - timedelta(seconds=60), 100.0),  # at boundary
            _make_trade(base_time - timedelta(seconds=30), 101.0),  # in window
        ]

        window = extract_window(
            event=event,
            trades=trades,
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        # Only the trade at -30s should be in pre_window
        assert len(window.pre_trades) == 1, "Expected 1 trade in pre-window (boundary excluded)"

    def test_window_boundaries_inclusive_event_time(self) -> None:
        """Post-window should include event time."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        trades = [
            _make_trade(base_time, 98.0),  # at event time
        ]

        window = extract_window(
            event=event,
            trades=trades,
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        assert len(window.post_trades) == 1, "Trade at event time should be in post-window"

    def test_filters_by_symbol(self) -> None:
        """Should only include data matching event symbol."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time, symbol="BTC-USDT")

        trades = [
            _make_trade(base_time - timedelta(seconds=30), 100.0, symbol="BTC-USDT"),
            _make_trade(base_time - timedelta(seconds=30), 3000.0, symbol="ETH-USDT"),
            _make_trade(base_time + timedelta(seconds=30), 98.0, symbol="BTC-USDT"),
            _make_trade(base_time + timedelta(seconds=30), 2900.0, symbol="ETH-USDT"),
        ]

        window = extract_window(
            event=event,
            trades=trades,
            tob=[],
            pre_seconds=300,
            post_seconds=300,
        )

        assert len(window.pre_trades) == 1, "Should only include BTC trades"
        assert len(window.post_trades) == 1, "Should only include BTC trades"
        assert window.pre_trades[0].symbol == "BTC-USDT"

    def test_window_id_generation(self) -> None:
        """Should generate deterministic window ID."""
        base_time = datetime(2024, 1, 15, 10, 5, 30, tzinfo=timezone.utc)
        event = _make_event(base_time, symbol="BTC-USDT")

        window = extract_window(
            event=event,
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        expected_id = "BTC-USDT_20240115_100530_price_shock"
        assert window.window_id == expected_id, f"Expected {expected_id}, got {window.window_id}"


class TestExtractWindowValidation:
    """Tests for input validation."""

    def test_negative_pre_seconds_raises_error(self) -> None:
        """Negative pre_seconds should raise WindowError."""
        event = _make_event(datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc))
        error_raised = False
        try:
            extract_window(event=event, trades=[], tob=[], pre_seconds=-60, post_seconds=60)
        except WindowError:
            error_raised = True
        assert error_raised, "Expected WindowError for negative pre_seconds"

    def test_negative_post_seconds_raises_error(self) -> None:
        """Negative post_seconds should raise WindowError."""
        event = _make_event(datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc))
        error_raised = False
        try:
            extract_window(event=event, trades=[], tob=[], pre_seconds=60, post_seconds=-60)
        except WindowError:
            error_raised = True
        assert error_raised, "Expected WindowError for negative post_seconds"


class TestExtractWindowsOverlap:
    """Tests for overlapping event handling."""

    def test_empty_events_returns_empty_list(self) -> None:
        """Empty events list should return empty windows list."""
        result = extract_windows(
            events=[],
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )
        assert result == [], "Expected empty list for empty events"

    def test_single_event_returns_one_window(self) -> None:
        """Single event should produce one window."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        events = [_make_event(base_time)]

        result = extract_windows(
            events=events,
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        assert len(result) == 1, "Expected one window"

    def test_keep_first_strategy_skips_overlapping(self) -> None:
        """With keep_first strategy, overlapping events should be skipped."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)

        # Two events 30 seconds apart, with 60-second post-window
        # Second event falls within first event's post-window
        events = [
            _make_event(base_time),
            _make_event(base_time + timedelta(seconds=30)),  # overlaps
        ]

        result = extract_windows(
            events=events,
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
            overlap_strategy="keep_first",
        )

        assert len(result) == 1, "Expected only first event (overlapping skipped)"
        assert result[0].event.timestamp == base_time

    def test_non_overlapping_events_all_kept(self) -> None:
        """Non-overlapping events should all produce windows."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Two events 5 minutes apart, with 60-second windows
        events = [
            _make_event(base_time),
            _make_event(base_time + timedelta(minutes=5)),  # no overlap
        ]

        result = extract_windows(
            events=events,
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        assert len(result) == 2, "Expected two windows (no overlap)"

    def test_unsorted_events_are_sorted(self) -> None:
        """Events should be processed in timestamp order regardless of input order."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Events in reverse order
        events = [
            _make_event(base_time + timedelta(minutes=5)),  # later
            _make_event(base_time),                         # earlier
        ]

        result = extract_windows(
            events=events,
            trades=[],
            tob=[],
            pre_seconds=60,
            post_seconds=60,
        )

        # Should process in chronological order
        assert result[0].event.timestamp == base_time, "First window should be earlier event"
        assert result[1].event.timestamp == base_time + timedelta(minutes=5)

    def test_unknown_overlap_strategy_raises_error(self) -> None:
        """Unknown overlap strategy should raise WindowError."""
        events = [_make_event(datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc))]
        error_raised = False
        try:
            extract_windows(
                events=events,
                trades=[],
                tob=[],
                pre_seconds=60,
                post_seconds=60,
                overlap_strategy="invalid",
            )
        except WindowError:
            error_raised = True
        assert error_raised, "Expected WindowError for unknown strategy"


class TestExtractWindowsFromConfig:
    """Tests for config-driven window extraction."""

    def test_from_config_works(self) -> None:
        """Should use config values correctly."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        events = [_make_event(base_time)]
        config = {
            "windows": {
                "pre_event_seconds": 300,
                "post_event_seconds": 300,
            }
        }

        result = extract_windows_from_config(events, [], [], config)

        assert len(result) == 1
        assert result[0].pre_seconds == 300
        assert result[0].post_seconds == 300

    def test_missing_config_raises_error(self) -> None:
        """Missing config keys should raise WindowError."""
        events: List[Event] = []
        error_raised = False
        try:
            extract_windows_from_config(events, [], [], {})
        except WindowError:
            error_raised = True
        assert error_raised, "Expected WindowError for missing config"


class TestSaveWindow:
    """Tests for window persistence."""

    def test_save_window_creates_files(self) -> None:
        """Should create expected output files."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        trades = [
            _make_trade(base_time - timedelta(seconds=30), 100.0),
            _make_trade(base_time + timedelta(seconds=30), 98.0),
        ]

        tob = [
            _make_tob(base_time - timedelta(seconds=30), 100.0),
            _make_tob(base_time + timedelta(seconds=30), 98.0),
        ]

        window = extract_window(event, trades, tob, 60, 60)

        # Use temp directory for test
        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = save_window(window, temp_dir)

            # Check all files were created
            assert Path(paths["event"]).exists(), "Event JSON not created"
            assert Path(paths["pre_trades"]).exists(), "Pre-trades CSV not created"
            assert Path(paths["post_trades"]).exists(), "Post-trades CSV not created"
            assert Path(paths["pre_tob"]).exists(), "Pre-TOB CSV not created"
            assert Path(paths["post_tob"]).exists(), "Post-TOB CSV not created"

            # Check event JSON contains expected fields
            import json
            with open(paths["event"]) as f:
                event_data = json.load(f)
            assert event_data["symbol"] == "BTC-USDT"
            assert event_data["pre_trades_count"] == 1
            assert event_data["post_trades_count"] == 1
        finally:
            shutil.rmtree(temp_dir)

    def test_save_empty_windows_creates_valid_csvs(self) -> None:
        """Should create valid CSVs even with no data."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        window = extract_window(event, [], [], 60, 60)

        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = save_window(window, temp_dir)

            # CSV should have header only
            with open(paths["pre_trades"]) as f:
                lines = f.readlines()
            assert len(lines) == 1, "Expected only header row"
            assert "timestamp" in lines[0]
        finally:
            shutil.rmtree(temp_dir)


def run_all_tests() -> None:
    """Run all tests and print results.

    This can be run standalone: PYTHONPATH=src python3 -m tests.test_windows
    """
    test_classes = [
        TestExtractWindowBasic,
        TestExtractWindowValidation,
        TestExtractWindowsOverlap,
        TestExtractWindowsFromConfig,
        TestSaveWindow,
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
