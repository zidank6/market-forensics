#!/usr/bin/env python3
"""Script to load and validate sample market data.

This script demonstrates the data loading pipeline and validates
that the sample data can be loaded successfully.

Usage:
    python3 scripts/load_sample_data.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from market_forensics.config import get_default_config_path, load_config
from market_forensics.data import (
    DataLoadError,
    TopOfBook,
    Trade,
    load_tob,
    load_trades,
)


def main() -> int:
    """Load and validate sample data, printing summary statistics."""
    # Load config
    config_path = get_default_config_path()
    print(f"Loading config from: {config_path}")
    config = load_config(config_path)

    data_dir = Path(__file__).parent.parent / config["paths"]["data_dir"]
    print(f"Data directory: {data_dir}")

    # Load trades
    trades_file = data_dir / "trades.csv"
    print(f"\nLoading trades from: {trades_file}")
    try:
        trades = load_trades(trades_file)
        print(f"  Loaded {len(trades)} trades")
        if trades:
            print(f"  Time range: {trades[0].timestamp} to {trades[-1].timestamp}")
            print(f"  Symbols: {set(t.symbol for t in trades)}")
            prices = [t.price for t in trades]
            print(f"  Price range: {min(prices):.2f} to {max(prices):.2f}")
            total_volume = sum(t.size for t in trades)
            print(f"  Total volume: {total_volume:.4f}")
    except DataLoadError as e:
        print(f"  ERROR: {e}")
        return 1

    # Load top-of-book
    tob_file = data_dir / "tob.csv"
    print(f"\nLoading top-of-book from: {tob_file}")
    try:
        tob_list = load_tob(tob_file)
        print(f"  Loaded {len(tob_list)} snapshots")
        if tob_list:
            print(f"  Time range: {tob_list[0].timestamp} to {tob_list[-1].timestamp}")
            print(f"  Symbols: {set(t.symbol for t in tob_list)}")
            spreads = [t.spread for t in tob_list]
            print(f"  Spread range: {min(spreads):.2f} to {max(spreads):.2f}")
            spread_bps = [t.spread_bps for t in tob_list]
            print(f"  Spread (bps) range: {min(spread_bps):.2f} to {max(spread_bps):.2f}")
    except DataLoadError as e:
        print(f"  ERROR: {e}")
        return 1

    print("\n✓ All sample data loaded and validated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
