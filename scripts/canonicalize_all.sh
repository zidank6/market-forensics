#!/bin/bash
# Canonicalize all downloaded dates for v2

set -e

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR/.."

# BTCUSDT dates
BTCUSDT_DATES=(
    "2024-01-03" "2024-01-08" "2024-01-09" "2024-01-10" "2024-01-11" "2024-01-12"
    "2024-02-12" "2024-02-26" "2024-02-28"
    "2024-03-04" "2024-03-05" "2024-03-11" "2024-03-12" "2024-03-14"
)

# ETHUSDT dates
ETHUSDT_DATES=(
    "2024-01-03" "2024-01-08" "2024-01-09" "2024-01-10" "2024-01-11" "2024-01-12"
    "2024-02-12" "2024-02-26" "2024-02-28"
    "2024-03-04" "2024-03-05" "2024-03-11" "2024-03-12" "2024-03-13"
)

echo "Canonicalizing BTCUSDT..."
for date in "${BTCUSDT_DATES[@]}"; do
    echo "  $date..."
    python3 scripts/canonicalize_binance_um_day.py --date "$date" --symbol BTCUSDT 2>&1 || echo "  Failed: $date"
done

echo ""
echo "Canonicalizing ETHUSDT..."
for date in "${ETHUSDT_DATES[@]}"; do
    echo "  $date..."
    python3 scripts/canonicalize_binance_um_day.py --date "$date" --symbol ETHUSDT 2>&1 || echo "  Failed: $date"
done

echo ""
echo "=== Canonicalization complete ==="
