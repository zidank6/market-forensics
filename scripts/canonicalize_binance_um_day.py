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

if __name__ == "__main__":
    symbol = "BTCUSDT"

    base = os.path.join(HERE, "..", "data", "binance", "futures_um", "BTCUSDT")
    raw_trades = os.path.join(base, "BTCUSDT-aggTrades-2024-03-28.csv")
    raw_tob = os.path.join(base, "BTCUSDT-bookTicker-2024-03-28.csv")

    out_dir = os.path.join(base, "canonical", "2024-03-28")
    os.makedirs(out_dir, exist_ok=True)

    out_trades = os.path.join(out_dir, "trades.csv")
    out_tob = os.path.join(out_dir, "tob.csv")

    canonicalize_aggtrades(raw_trades, out_trades, symbol)
    canonicalize_bookticker(raw_tob, out_tob, symbol)

    print("Wrote:")
    print(" -", out_trades)
    print(" -", out_tob)
