"""Tests for microstructure metrics computation.

Tests for computing metrics from trade and top-of-book data (MF-005).
"""

from __future__ import annotations

import json
import math
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
from market_forensics.metrics.calculator import (
    EventMetrics,
    WindowMetrics,
    compute_all_metrics,
    compute_event_metrics,
    compute_tob_metrics,
    compute_trade_metrics,
    compute_window_metrics,
    save_metrics,
    save_metrics_csv,
    save_metrics_json,
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


class TestComputeTradeMetrics:
    """Tests for trade-based metrics computation."""

    def test_empty_trades_returns_zeros(self) -> None:
        """Empty trade list should return zeros/Nones."""
        result = compute_trade_metrics([])
        (trade_count, trade_volume, avg_size, vwap, vol, min_p, max_p) = result

        assert trade_count == 0
        assert trade_volume == 0.0
        assert avg_size is None
        assert vwap is None
        assert vol is None
        assert min_p is None
        assert max_p is None

    def test_single_trade_metrics(self) -> None:
        """Single trade should compute basic metrics."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        trades = [_make_trade(base_time, 100.0, 2.0)]

        result = compute_trade_metrics(trades)
        (trade_count, trade_volume, avg_size, vwap, vol, min_p, max_p) = result

        assert trade_count == 1
        assert trade_volume == 2.0
        assert avg_size == 2.0
        assert vwap == 100.0
        assert vol is None  # Need at least 2 trades for volatility
        assert min_p == 100.0
        assert max_p == 100.0

    def test_multiple_trades_metrics(self) -> None:
        """Multiple trades should compute correct metrics."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        trades = [
            _make_trade(base_time, 100.0, 1.0),
            _make_trade(base_time + timedelta(seconds=10), 102.0, 2.0),
            _make_trade(base_time + timedelta(seconds=20), 98.0, 1.0),
        ]

        result = compute_trade_metrics(trades)
        (trade_count, trade_volume, avg_size, vwap, vol, min_p, max_p) = result

        assert trade_count == 3
        assert trade_volume == 4.0
        assert avg_size == 4.0 / 3.0

        # VWAP = (100*1 + 102*2 + 98*1) / 4 = 402/4 = 100.5
        assert abs(vwap - 100.5) < 0.001

        assert min_p == 98.0
        assert max_p == 102.0

        # Volatility should be computed (at least 2 trades)
        assert vol is not None
        assert vol > 0

    def test_vwap_calculation(self) -> None:
        """VWAP should weight prices by volume."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        # High volume at 100, low volume at 200 -> VWAP closer to 100
        trades = [
            _make_trade(base_time, 100.0, 9.0),
            _make_trade(base_time + timedelta(seconds=10), 200.0, 1.0),
        ]

        result = compute_trade_metrics(trades)
        vwap = result[3]

        # VWAP = (100*9 + 200*1) / 10 = 1100/10 = 110
        assert abs(vwap - 110.0) < 0.001


class TestComputeTobMetrics:
    """Tests for top-of-book metrics computation."""

    def test_empty_tob_returns_nones(self) -> None:
        """Empty TOB list should return Nones."""
        result = compute_tob_metrics([])
        assert result == (None, None, None)

    def test_single_tob_metrics(self) -> None:
        """Single TOB snapshot should compute metrics."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        tob = [_make_tob(base_time, mid=100.0, spread=2.0)]

        (avg_spread, avg_spread_bps, avg_midprice) = compute_tob_metrics(tob)

        assert abs(avg_spread - 2.0) < 0.001
        assert avg_midprice == 100.0
        # Spread bps = (2/100) * 10000 = 200 bps
        assert abs(avg_spread_bps - 200.0) < 0.001

    def test_multiple_tob_metrics(self) -> None:
        """Multiple TOB snapshots should compute averages."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        tob = [
            _make_tob(base_time, mid=100.0, spread=2.0),
            _make_tob(base_time + timedelta(seconds=10), mid=102.0, spread=4.0),
        ]

        (avg_spread, avg_spread_bps, avg_midprice) = compute_tob_metrics(tob)

        assert abs(avg_spread - 3.0) < 0.001  # (2+4)/2
        assert abs(avg_midprice - 101.0) < 0.001  # (100+102)/2


class TestComputeWindowMetrics:
    """Tests for combined window metrics."""

    def test_empty_window_metrics(self) -> None:
        """Empty window should have appropriate zeros/Nones."""
        metrics = compute_window_metrics([], [])

        assert metrics.trade_count == 0
        assert metrics.trade_volume == 0.0
        assert metrics.avg_trade_size is None
        assert metrics.avg_spread is None
        assert metrics.avg_midprice is None

    def test_combined_metrics(self) -> None:
        """Should combine trade and TOB metrics."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        trades = [_make_trade(base_time, 100.0, 2.0)]
        tob = [_make_tob(base_time, mid=100.0, spread=2.0)]

        metrics = compute_window_metrics(trades, tob)

        # Trade metrics
        assert metrics.trade_count == 1
        assert metrics.trade_volume == 2.0

        # TOB metrics
        assert metrics.avg_spread == 2.0
        assert metrics.avg_midprice == 100.0


class TestComputeEventMetrics:
    """Tests for event-level metrics."""

    def test_event_metrics_structure(self) -> None:
        """Should compute metrics for both pre and post windows."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        pre_trades = [_make_trade(base_time - timedelta(seconds=30), 100.0)]
        post_trades = [_make_trade(base_time, 98.0)]
        pre_tob = [_make_tob(base_time - timedelta(seconds=30), 100.0)]
        post_tob = [_make_tob(base_time, 98.0)]

        window = _make_event_window(event, pre_trades, post_trades, pre_tob, post_tob)
        metrics = compute_event_metrics(window)

        assert metrics.window_id == window.window_id
        assert metrics.symbol == "BTC-USDT"
        assert metrics.event_direction == "down"

        # Pre and post should have their own metrics
        assert metrics.pre_metrics.trade_count == 1
        assert metrics.post_metrics.trade_count == 1

    def test_to_dict_flattens_structure(self) -> None:
        """to_dict should flatten pre/post metrics."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])

        metrics = compute_event_metrics(window)
        d = metrics.to_dict()

        # Should have prefixed columns
        assert "pre_trade_count" in d
        assert "post_trade_count" in d
        assert "pre_avg_spread" in d
        assert "post_avg_spread" in d


class TestComputeAllMetrics:
    """Tests for batch metrics computation."""

    def test_empty_windows_returns_empty_list(self) -> None:
        """Empty windows list should return empty metrics list."""
        result = compute_all_metrics([])
        assert result == []

    def test_multiple_windows(self) -> None:
        """Should compute metrics for all windows."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        windows = [
            _make_event_window(
                _make_event(base_time), [], [], [], []
            ),
            _make_event_window(
                _make_event(base_time + timedelta(minutes=5)), [], [], [], []
            ),
        ]

        result = compute_all_metrics(windows)
        assert len(result) == 2


class TestSaveMetrics:
    """Tests for metrics persistence."""

    def test_save_metrics_json(self) -> None:
        """Should save metrics as valid JSON."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])
        metrics = [compute_event_metrics(window)]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = save_metrics_json(metrics, temp_dir / "test.json")

            # Should be valid JSON
            with open(path) as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["symbol"] == "BTC-USDT"
        finally:
            shutil.rmtree(temp_dir)

    def test_save_metrics_csv(self) -> None:
        """Should save metrics as CSV with headers."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])
        metrics = [compute_event_metrics(window)]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = save_metrics_csv(metrics, temp_dir / "test.csv")

            with open(path) as f:
                lines = f.readlines()

            # Header + 1 data row
            assert len(lines) == 2
            assert "window_id" in lines[0]
            assert "pre_trade_count" in lines[0]
        finally:
            shutil.rmtree(temp_dir)

    def test_save_empty_metrics(self) -> None:
        """Should handle empty metrics list."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = save_metrics([], temp_dir)

            assert Path(paths["json"]).exists()
            assert Path(paths["csv"]).exists()

            # JSON should be empty array
            with open(paths["json"]) as f:
                data = json.load(f)
            assert data == []
        finally:
            shutil.rmtree(temp_dir)

    def test_save_metrics_creates_both_formats(self) -> None:
        """save_metrics should create both JSON and CSV."""
        base_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)
        window = _make_event_window(event, [], [], [], [])
        metrics = [compute_event_metrics(window)]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = save_metrics(metrics, temp_dir, basename="my_metrics")

            assert Path(paths["json"]).exists()
            assert Path(paths["csv"]).exists()
            assert "my_metrics.json" in paths["json"]
            assert "my_metrics.csv" in paths["csv"]
        finally:
            shutil.rmtree(temp_dir)


def run_all_tests() -> None:
    """Run all tests and print results.

    This can be run standalone: PYTHONPATH=src python3 -m tests.test_metrics
    """
    test_classes = [
        TestComputeTradeMetrics,
        TestComputeTobMetrics,
        TestComputeWindowMetrics,
        TestComputeEventMetrics,
        TestComputeAllMetrics,
        TestSaveMetrics,
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
