import csv
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

def ms_to_iso(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return dt.isoformat()

def canonicalize_aggtrades(in_path: str, out_path: str, symbol: str) -> None:
    with open(in_path, "r", newline="") as f_in, open(out_path, "w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["timestamp", "symbol", "price", "size", "side", "trade_id"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ms = int(row["transact_time"])
            # Binance futures aggTrades: is_buyer_maker == true means the buyer was maker
            # Common convention: if buyer is maker -> trade was initiated by seller (sell aggressor)
            side = "sell" if row["is_buyer_maker"].lower() == "true" else "buy"
            writer.writerow({
                "timestamp": ms_to_iso(ms),
                "symbol": symbol,
                "price": float(row["price"]),
                "size": float(row["quantity"]),
                "side": side,
                "trade_id": int(row["agg_trade_id"]),
            })

def canonicalize_bookticker(in_path: str, out_path: str, symbol: str) -> None:
    with open(in_path, "r", newline="") as f_in, open(out_path, "w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["timestamp", "symbol", "bid_price", "bid_size", "ask_price", "ask_size"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Use event_time as the best “when this book update happened”
            ms = int(row["event_time"])
            writer.writerow({
                "timestamp": ms_to_iso(ms),
                "symbol": symbol,
                "bid_price": float(row["best_bid_price"]),
                "bid_size": float(row["best_bid_qty"]),
                "ask_price": float(row["best_ask_price"]),
                "ask_size": float(row["best_ask_qty"]),
            })

def canonicalize_day(date: str, symbol: str = "BTCUSDT") -> None:
    """Canonicalize raw Binance data for a given date.

    Args:
        date: Date in YYYY-MM-DD format
        symbol: Trading pair symbol (default: BTCUSDT)
    """
    base = os.path.join(HERE, "..", "data", "binance", "futures_um", symbol)
    raw_trades = os.path.join(base, f"{symbol}-aggTrades-{date}.csv")
    raw_tob = os.path.join(base, f"{symbol}-bookTicker-{date}.csv")

    # Validate inputs exist
    if not os.path.exists(raw_trades):
        raise FileNotFoundError(f"Raw trades file not found: {raw_trades}")
    if not os.path.exists(raw_tob):
        raise FileNotFoundError(f"Raw TOB file not found: {raw_tob}")

    out_dir = os.path.join(base, "canonical", date)
    os.makedirs(out_dir, exist_ok=True)

    out_trades = os.path.join(out_dir, "trades.csv")
    out_tob = os.path.join(out_dir, "tob.csv")

    canonicalize_aggtrades(raw_trades, out_trades, symbol)
    canonicalize_bookticker(raw_tob, out_tob, symbol)

    print("Wrote:")
    print(" -", out_trades)
    print(" -", out_tob)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Canonicalize Binance UM data for a specific date")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol (default: BTCUSDT)")
    args = parser.parse_args()

    canonicalize_day(args.date, args.symbol)
