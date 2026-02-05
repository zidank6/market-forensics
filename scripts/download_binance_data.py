#!/usr/bin/env python3
"""Download Binance USDT-M futures data from data.binance.vision.

Downloads aggTrades and bookTicker data for a specified symbol and date range.

URL pattern:
https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{DATE}.zip
https://data.binance.vision/data/futures/um/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-{DATE}.zip
"""

import argparse
import os
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path


HERE = Path(__file__).parent.absolute()
DATA_DIR = HERE.parent / "data" / "binance" / "futures_um"

BASE_URL = "https://data.binance.vision/data/futures/um/daily"


def date_range(start_date: str, end_date: str) -> list[str]:
    """Generate list of dates between start and end (inclusive)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to destination path.

    Returns True if download succeeded, False if file not found (404).
    Raises exception for other errors.
    """
    if dest.exists():
        print(f"  Already exists: {dest.name}")
        return True

    try:
        print(f"  Downloading: {dest.name}")
        urllib.request.urlretrieve(url, dest)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  Not found (404): {dest.name}")
            return False
        raise


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """Extract a zip file to destination directory."""
    csv_name = zip_path.stem + ".csv"
    csv_path = dest_dir / csv_name

    if csv_path.exists():
        print(f"  Already extracted: {csv_name}")
        return

    print(f"  Extracting: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


def download_day(symbol: str, date: str, keep_zip: bool = True) -> bool:
    """Download and extract data for a single day.

    Returns True if both aggTrades and bookTicker were downloaded successfully.
    """
    symbol_dir = DATA_DIR / symbol
    symbol_dir.mkdir(parents=True, exist_ok=True)

    success = True

    for data_type in ["aggTrades", "bookTicker"]:
        filename = f"{symbol}-{data_type}-{date}.zip"
        url = f"{BASE_URL}/{data_type}/{symbol}/{filename}"
        zip_path = symbol_dir / filename

        if download_file(url, zip_path):
            extract_zip(zip_path, symbol_dir)
            if not keep_zip and zip_path.exists():
                zip_path.unlink()
        else:
            success = False

    return success


def download_range(symbol: str, start_date: str, end_date: str, keep_zip: bool = True) -> list[str]:
    """Download data for a date range.

    Returns list of dates that were successfully downloaded.
    """
    dates = date_range(start_date, end_date)
    successful_dates = []

    print(f"Downloading {symbol} data from {start_date} to {end_date}")
    print(f"Total days to process: {len(dates)}")
    print()

    for i, date in enumerate(dates, 1):
        print(f"[{i}/{len(dates)}] {date}")
        if download_day(symbol, date, keep_zip):
            successful_dates.append(date)
        print()

    print(f"Successfully downloaded {len(successful_dates)}/{len(dates)} days")
    return successful_dates


def main():
    parser = argparse.ArgumentParser(
        description="Download Binance USDT-M futures data"
    )
    parser.add_argument(
        "--symbol",
        default="BTCUSDT",
        help="Trading pair symbol (default: BTCUSDT)"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--delete-zip",
        action="store_true",
        help="Delete zip files after extraction"
    )

    args = parser.parse_args()

    successful = download_range(
        args.symbol,
        args.start_date,
        args.end_date,
        keep_zip=not args.delete_zip
    )

    if not successful:
        print("No data was downloaded successfully.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
