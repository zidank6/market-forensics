"""Data loaders for trades and top-of-book data.

Loaders read CSV or JSONL files and convert them to canonical types.
All loaders validate required fields and fail loudly with clear errors.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set, Union

from .models import Event, EventDirection, Side, TopOfBook, Trade

# Required columns for each data type
TRADE_REQUIRED_COLUMNS = {"timestamp", "symbol", "price", "size", "side"}
TOB_REQUIRED_COLUMNS = {
    "timestamp",
    "symbol",
    "bid_price",
    "bid_size",
    "ask_price",
    "ask_size",
}


class DataLoadError(Exception):
    """Raised when data loading fails due to validation or parsing errors."""

    pass


def _parse_timestamp(value: str) -> datetime:
    """Parse a timestamp string to datetime.

    Supports ISO 8601 format and Unix timestamps (seconds or milliseconds).
    """
    # Try ISO format first
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    # Try Unix timestamp (seconds or milliseconds)
    try:
        ts = float(value)
        # Heuristic: if > 1e12, assume milliseconds
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except ValueError:
        pass

    raise DataLoadError(f"Cannot parse timestamp: {value}")


def _parse_side(value: str) -> Side:
    """Parse trade side from string."""
    value_lower = value.lower().strip()
    if value_lower in ("buy", "b", "bid"):
        return Side.BUY
    elif value_lower in ("sell", "s", "ask"):
        return Side.SELL
    else:
        raise DataLoadError(f"Invalid trade side: {value}")


def _validate_columns(actual: Set[str], required: Set[str], file_path: Path) -> None:
    """Validate that all required columns are present."""
    missing = required - actual
    if missing:
        raise DataLoadError(
            f"Missing required columns in {file_path}: {sorted(missing)}. "
            f"Found columns: {sorted(actual)}"
        )


def load_trades_csv(file_path: Union[Path, str]) -> List[Trade]:
    """Load trades from a CSV file.

    Expected columns: timestamp, symbol, price, size, side
    Optional columns: trade_id

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of Trade objects sorted by timestamp.

    Raises:
        DataLoadError: If file is missing, has invalid data, or missing columns.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise DataLoadError(f"Trades file not found: {file_path}")

    trades = []
    try:
        with open(file_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise DataLoadError(f"CSV file is empty or has no header: {file_path}")

            _validate_columns(
                set(reader.fieldnames), TRADE_REQUIRED_COLUMNS, file_path
            )

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                try:
                    trade = Trade(
                        timestamp=_parse_timestamp(row["timestamp"]),
                        symbol=row["symbol"].strip(),
                        price=float(row["price"]),
                        size=float(row["size"]),
                        side=_parse_side(row["side"]),
                        trade_id=row.get("trade_id"),
                    )
                    trades.append(trade)
                except (ValueError, KeyError) as e:
                    raise DataLoadError(
                        f"Error parsing trade at row {row_num} in {file_path}: {e}"
                    ) from e

    except csv.Error as e:
        raise DataLoadError(f"CSV parsing error in {file_path}: {e}") from e

    return sorted(trades, key=lambda t: t.timestamp)


def load_trades_jsonl(file_path: Union[Path, str]) -> List[Trade]:
    """Load trades from a JSONL file.

    Each line must be a JSON object with: timestamp, symbol, price, size, side
    Optional: trade_id

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of Trade objects sorted by timestamp.

    Raises:
        DataLoadError: If file is missing, has invalid data, or missing fields.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise DataLoadError(f"Trades file not found: {file_path}")

    trades = []
    with open(file_path, "r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise DataLoadError(
                    f"Invalid JSON at line {line_num} in {file_path}: {e}"
                ) from e

            missing = TRADE_REQUIRED_COLUMNS - set(data.keys())
            if missing:
                raise DataLoadError(
                    f"Missing required fields at line {line_num} in {file_path}: {sorted(missing)}"
                )

            try:
                trade = Trade(
                    timestamp=_parse_timestamp(str(data["timestamp"])),
                    symbol=str(data["symbol"]).strip(),
                    price=float(data["price"]),
                    size=float(data["size"]),
                    side=_parse_side(str(data["side"])),
                    trade_id=data.get("trade_id"),
                )
                trades.append(trade)
            except (ValueError, KeyError) as e:
                raise DataLoadError(
                    f"Error parsing trade at line {line_num} in {file_path}: {e}"
                ) from e

    return sorted(trades, key=lambda t: t.timestamp)


def load_tob_csv(file_path: Union[Path, str]) -> List[TopOfBook]:
    """Load top-of-book snapshots from a CSV file.

    Expected columns: timestamp, symbol, bid_price, bid_size, ask_price, ask_size

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of TopOfBook objects sorted by timestamp.

    Raises:
        DataLoadError: If file is missing, has invalid data, or missing columns.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise DataLoadError(f"Top-of-book file not found: {file_path}")

    tob_list = []
    try:
        with open(file_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise DataLoadError(f"CSV file is empty or has no header: {file_path}")

            _validate_columns(set(reader.fieldnames), TOB_REQUIRED_COLUMNS, file_path)

            for row_num, row in enumerate(reader, start=2):
                try:
                    tob = TopOfBook(
                        timestamp=_parse_timestamp(row["timestamp"]),
                        symbol=row["symbol"].strip(),
                        bid_price=float(row["bid_price"]),
                        bid_size=float(row["bid_size"]),
                        ask_price=float(row["ask_price"]),
                        ask_size=float(row["ask_size"]),
                    )
                    tob_list.append(tob)
                except (ValueError, KeyError) as e:
                    raise DataLoadError(
                        f"Error parsing top-of-book at row {row_num} in {file_path}: {e}"
                    ) from e

    except csv.Error as e:
        raise DataLoadError(f"CSV parsing error in {file_path}: {e}") from e

    return sorted(tob_list, key=lambda t: t.timestamp)


def load_tob_jsonl(file_path: Union[Path, str]) -> List[TopOfBook]:
    """Load top-of-book snapshots from a JSONL file.

    Each line must be a JSON object with: timestamp, symbol, bid_price, bid_size, ask_price, ask_size

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of TopOfBook objects sorted by timestamp.

    Raises:
        DataLoadError: If file is missing, has invalid data, or missing fields.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise DataLoadError(f"Top-of-book file not found: {file_path}")

    tob_list = []
    with open(file_path, "r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise DataLoadError(
                    f"Invalid JSON at line {line_num} in {file_path}: {e}"
                ) from e

            missing = TOB_REQUIRED_COLUMNS - set(data.keys())
            if missing:
                raise DataLoadError(
                    f"Missing required fields at line {line_num} in {file_path}: {sorted(missing)}"
                )

            try:
                tob = TopOfBook(
                    timestamp=_parse_timestamp(str(data["timestamp"])),
                    symbol=str(data["symbol"]).strip(),
                    bid_price=float(data["bid_price"]),
                    bid_size=float(data["bid_size"]),
                    ask_price=float(data["ask_price"]),
                    ask_size=float(data["ask_size"]),
                )
                tob_list.append(tob)
            except (ValueError, KeyError) as e:
                raise DataLoadError(
                    f"Error parsing top-of-book at line {line_num} in {file_path}: {e}"
                ) from e

    return sorted(tob_list, key=lambda t: t.timestamp)


def load_trades(file_path: Union[Path, str]) -> List[Trade]:
    """Load trades from a file, auto-detecting format from extension.

    Supports: .csv, .jsonl

    Args:
        file_path: Path to the trades file.

    Returns:
        List of Trade objects sorted by timestamp.

    Raises:
        DataLoadError: If format is unsupported or data is invalid.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return load_trades_csv(file_path)
    elif suffix == ".jsonl":
        return load_trades_jsonl(file_path)
    else:
        raise DataLoadError(
            f"Unsupported file format '{suffix}' for trades. Supported: .csv, .jsonl"
        )


def load_tob(file_path: Union[Path, str]) -> List[TopOfBook]:
    """Load top-of-book from a file, auto-detecting format from extension.

    Supports: .csv, .jsonl

    Args:
        file_path: Path to the top-of-book file.

    Returns:
        List of TopOfBook objects sorted by timestamp.

    Raises:
        DataLoadError: If format is unsupported or data is invalid.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return load_tob_csv(file_path)
    elif suffix == ".jsonl":
        return load_tob_jsonl(file_path)
    else:
        raise DataLoadError(
            f"Unsupported file format '{suffix}' for top-of-book. Supported: .csv, .jsonl"
        )
