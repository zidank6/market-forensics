"""Tests for price-shock event detector.

These are unit-like checks for edge cases as required by MF-003.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from market_forensics.data.models import (
    Event,
    EventDirection,
    Side,
    TopOfBook,
    Trade,
)
from market_forensics.events.detector import (
    DetectorError,
    detect_price_shocks,
    detect_price_shocks_from_config,
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


class TestDetectPriceShocksEdgeCases:
    """Tests for edge cases: empty data, constant price, duplicated timestamps."""

    def test_empty_data_returns_empty_list(self) -> None:
        """Empty data should return an empty list of events."""
        result = detect_price_shocks([], threshold_pct=1.0, window_seconds=60)
        assert result == [], "Expected empty list for empty input"

    def test_single_data_point_returns_empty_list(self) -> None:
        """A single data point cannot have a price shock."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [_make_trade(base_time, 100.0)]
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        assert result == [], "Expected empty list for single data point"

    def test_constant_price_returns_empty_list(self) -> None:
        """Constant price (no movement) should return no events."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time + timedelta(seconds=i * 10), 100.0)
            for i in range(10)
        ]
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        assert result == [], "Expected no events for constant price"

    def test_duplicated_timestamps_allowed(self) -> None:
        """Duplicated timestamps should be processed (not fail)."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        # Two trades at exact same timestamp
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time, 100.0),  # duplicate timestamp
            _make_trade(base_time + timedelta(seconds=30), 102.0),  # 2% move
        ]
        # Should not raise, duplicates are allowed
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        # 2% move should trigger at least one event
        assert len(result) >= 1, "Expected at least one event for 2% price move"

    def test_unsorted_timestamps_raises_error(self) -> None:
        """Timestamps not in ascending order should raise DetectorError."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time + timedelta(seconds=30), 100.0),
            _make_trade(base_time, 101.0),  # earlier timestamp = unsorted
        ]
        error_raised = False
        try:
            detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        except DetectorError:
            error_raised = True
        assert error_raised, "Expected DetectorError for unsorted timestamps"


class TestDetectPriceShocksBasic:
    """Basic functionality tests."""

    def test_detects_upward_shock(self) -> None:
        """Should detect upward price shock."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time + timedelta(seconds=30), 102.0),  # 2% up
        ]
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        assert len(result) == 1, "Expected one event"
        assert result[0].direction == EventDirection.UP, "Expected UP direction"
        assert result[0].event_type == "price_shock"
        assert result[0].magnitude >= 1.0, "Expected magnitude >= threshold"

    def test_detects_downward_shock(self) -> None:
        """Should detect downward price shock."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time + timedelta(seconds=30), 98.0),  # 2% down
        ]
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        assert len(result) == 1, "Expected one event"
        assert result[0].direction == EventDirection.DOWN, "Expected DOWN direction"
        assert result[0].magnitude <= -1.0, "Expected negative magnitude >= threshold"

    def test_below_threshold_no_event(self) -> None:
        """Price move below threshold should not trigger event."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time + timedelta(seconds=30), 100.5),  # 0.5% up
        ]
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        assert result == [], "Expected no events below threshold"

    def test_outside_window_no_event(self) -> None:
        """Price move outside rolling window should not trigger event."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time + timedelta(seconds=120), 102.0),  # 2% but 120s later
        ]
        # Window is 60 seconds, so the 100.0 reference is outside
        result = detect_price_shocks(trades, threshold_pct=1.0, window_seconds=60)
        # When the second trade is processed, the first trade is outside the window
        # so no shock is detected (the reference would be itself)
        assert result == [], "Expected no events when move is outside window"

    def test_works_with_top_of_book(self) -> None:
        """Should work with TopOfBook data using mid_price."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        tob_data = [
            _make_tob(base_time, 100.0),
            _make_tob(base_time + timedelta(seconds=30), 102.0),  # 2% mid move
        ]
        result = detect_price_shocks(tob_data, threshold_pct=1.0, window_seconds=60)
        assert len(result) == 1, "Expected one event from TOB data"
        assert result[0].direction == EventDirection.UP


class TestDetectPriceShocksConfig:
    """Tests for config-driven detection."""

    def test_from_config_works(self) -> None:
        """Should use config values correctly."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            _make_trade(base_time, 100.0),
            _make_trade(base_time + timedelta(seconds=30), 102.0),
        ]
        config = {
            "event_detection": {
                "price_shock_threshold_pct": 1.0,
                "rolling_window_seconds": 60,
            }
        }
        result = detect_price_shocks_from_config(trades, config)
        assert len(result) == 1

    def test_missing_config_raises_error(self) -> None:
        """Missing config keys should raise DetectorError."""
        trades: List[Trade] = []
        error_raised = False
        try:
            detect_price_shocks_from_config(trades, {})
        except DetectorError:
            error_raised = True
        assert error_raised, "Expected DetectorError for missing config"


class TestDetectPriceShocksValidation:
    """Tests for input validation."""

    def test_negative_threshold_raises_error(self) -> None:
        """Negative threshold should raise DetectorError."""
        error_raised = False
        try:
            detect_price_shocks([], threshold_pct=-1.0, window_seconds=60)
        except DetectorError:
            error_raised = True
        assert error_raised, "Expected DetectorError for negative threshold"

    def test_zero_threshold_raises_error(self) -> None:
        """Zero threshold should raise DetectorError."""
        error_raised = False
        try:
            detect_price_shocks([], threshold_pct=0.0, window_seconds=60)
        except DetectorError:
            error_raised = True
        assert error_raised, "Expected DetectorError for zero threshold"

    def test_negative_window_raises_error(self) -> None:
        """Negative window should raise DetectorError."""
        error_raised = False
        try:
            detect_price_shocks([], threshold_pct=1.0, window_seconds=-60)
        except DetectorError:
            error_raised = True
        assert error_raised, "Expected DetectorError for negative window"


def run_all_tests() -> None:
    """Run all tests and print results.

    This can be run standalone: python -m tests.test_detector
    """
    test_classes = [
        TestDetectPriceShocksEdgeCases,
        TestDetectPriceShocksBasic,
        TestDetectPriceShocksConfig,
        TestDetectPriceShocksValidation,
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
