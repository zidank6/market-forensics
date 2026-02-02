"""Tests for plot generation module.

Tests for generating visualizations (MF-007).
Note: Plotting tests are skipped when matplotlib is not installed.
"""

from __future__ import annotations

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
)
from market_forensics.plots.generator import (
    MATPLOTLIB_AVAILABLE,
    PlotError,
    check_matplotlib,
    generate_all_plots,
    generate_summary_table,
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


def _make_ordering(
    ts: datetime,
    classification: str,
    symbol: str = "BTC-USDT",
) -> EventOrdering:
    """Helper to create an EventOrdering for testing."""
    return EventOrdering(
        window_id=f"{symbol}_{ts.strftime('%Y%m%d_%H%M%S')}_price_shock",
        symbol=symbol,
        event_timestamp=ts.isoformat(),
        event_direction="down",
        liquidity_onset=OnsetDetection(
            OnsetType.LIQUIDITY, None, None, None, None, None, 2.0
        ),
        volume_onset=OnsetDetection(
            OnsetType.VOLUME, None, None, None, None, None, 2.0
        ),
        price_onset=OnsetDetection(
            OnsetType.PRICE, None, None, None, None, None, 2.0
        ),
        ordering=[],
        classification=classification,
    )


class TestCheckMatplotlib:
    """Tests for matplotlib availability check."""

    def test_check_matplotlib_when_available(self) -> None:
        """Should not raise when matplotlib is available."""
        if MATPLOTLIB_AVAILABLE:
            # Should not raise
            check_matplotlib()
        else:
            # Should raise PlotError
            error_raised = False
            try:
                check_matplotlib()
            except PlotError:
                error_raised = True
            assert error_raised, "Expected PlotError when matplotlib not available"


class TestGenerateSummaryTable:
    """Tests for summary table generation (no matplotlib required)."""

    def test_generates_csv(self) -> None:
        """Should generate CSV summary table."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        orderings = [
            _make_ordering(base_time, "liquidity-first"),
            _make_ordering(base_time + timedelta(minutes=5), "volume-first"),
            _make_ordering(base_time + timedelta(minutes=10), "liquidity-first"),
        ]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = generate_summary_table(orderings, temp_dir / "summary.csv")

            assert Path(path).exists(), "CSV file not created"

            with open(path) as f:
                lines = f.readlines()

            # Header + 1 symbol + total
            assert len(lines) == 3
            assert "symbol" in lines[0]
            assert "BTC-USDT" in lines[1]
            assert "TOTAL" in lines[2]
        finally:
            shutil.rmtree(temp_dir)

    def test_handles_multiple_symbols(self) -> None:
        """Should handle multiple symbols."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        orderings = [
            _make_ordering(base_time, "liquidity-first", "BTC-USDT"),
            _make_ordering(base_time, "volume-first", "ETH-USDT"),
            _make_ordering(base_time, "price-first", "BTC-USDT"),
        ]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = generate_summary_table(orderings, temp_dir / "summary.csv")

            with open(path) as f:
                content = f.read()

            assert "BTC-USDT" in content
            assert "ETH-USDT" in content
            assert "TOTAL" in content
        finally:
            shutil.rmtree(temp_dir)

    def test_empty_orderings(self) -> None:
        """Should handle empty orderings list."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = generate_summary_table([], temp_dir / "summary.csv")

            assert Path(path).exists(), "CSV file not created"

            with open(path) as f:
                lines = f.readlines()

            # Only header and total row
            assert len(lines) == 2
        finally:
            shutil.rmtree(temp_dir)


class TestGenerateAllPlots:
    """Tests for full plot generation."""

    def test_generates_summary_table_without_matplotlib(self) -> None:
        """Should generate summary table even without matplotlib."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        orderings = [
            _make_ordering(base_time, "liquidity-first"),
        ]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = generate_all_plots([], orderings, temp_dir)

            # Summary table should always be generated
            assert result['summary_table'] is not None
            assert Path(result['summary_table']).exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_returns_structure(self) -> None:
        """Should return expected structure."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = generate_all_plots([], [], temp_dir)

            assert 'event_plots' in result
            assert 'summary_plots' in result
            assert 'summary_table' in result
        finally:
            shutil.rmtree(temp_dir)


class TestPlotEventWhenMatplotlibAvailable:
    """Tests that only run when matplotlib is available."""

    def test_plot_event_creates_files(self) -> None:
        """Should create plot files when matplotlib is available."""
        if not MATPLOTLIB_AVAILABLE:
            # Skip test
            return

        from market_forensics.plots.generator import plot_event

        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(base_time)

        pre_trades = [_make_trade(base_time - timedelta(seconds=30), 100.0)]
        post_trades = [_make_trade(base_time, 98.0)]
        pre_tob = [_make_tob(base_time - timedelta(seconds=30), 100.0)]
        post_tob = [_make_tob(base_time, 98.0)]

        window = _make_event_window(event, pre_trades, post_trades, pre_tob, post_tob)

        temp_dir = Path(tempfile.mkdtemp())
        try:
            paths = plot_event(window, temp_dir)

            assert Path(paths.price_plot).exists(), "Price plot not created"
            assert Path(paths.spread_plot).exists(), "Spread plot not created"
            assert Path(paths.volume_plot).exists(), "Volume plot not created"
        finally:
            shutil.rmtree(temp_dir)

    def test_plot_ordering_distribution(self) -> None:
        """Should create ordering distribution plot."""
        if not MATPLOTLIB_AVAILABLE:
            return

        from market_forensics.plots.generator import plot_ordering_distribution

        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        orderings = [
            _make_ordering(base_time, "liquidity-first"),
            _make_ordering(base_time + timedelta(minutes=5), "volume-first"),
        ]

        temp_dir = Path(tempfile.mkdtemp())
        try:
            path = plot_ordering_distribution(orderings, temp_dir / "dist.png")
            assert Path(path).exists(), "Distribution plot not created"
        finally:
            shutil.rmtree(temp_dir)


def run_all_tests() -> None:
    """Run all tests and print results.

    This can be run standalone: PYTHONPATH=src python3 -m tests.test_plots
    """
    test_classes = [
        TestCheckMatplotlib,
        TestGenerateSummaryTable,
        TestGenerateAllPlots,
        TestPlotEventWhenMatplotlibAvailable,
    ]

    passed = 0
    failed = 0
    skipped = 0

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
