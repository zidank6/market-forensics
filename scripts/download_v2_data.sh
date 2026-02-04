#!/bin/bash
# Download more Q1 2024 dates (bookTicker available)
set -e

DATA_DIR="$(dirname "$0")/../data/binance/futures_um"

# Additional Q1 2024 dates with high volatility
# January: BTC ETF period
# February: Post-ETF consolidation and breakout
# March: ATH run

BTCUSDT_DATES=(
    "2024-01-03"  # Pre-ETF anticipation
    "2024-01-08"  # ETF week start
    "2024-01-09"  # Day before ETF
    "2024-01-12"  # Post-ETF trading
    "2024-02-12"  # Feb volatility
    "2024-02-26"  # Late Feb breakout
    "2024-02-28"  # Month end vol
    "2024-03-04"  # Pre-ATH run
    "2024-03-11"  # ATH week
    "2024-03-12"  # ATH week
)

ETHUSDT_DATES=(
    "2024-01-03"  
    "2024-01-08"  
    "2024-01-09"  
    "2024-01-12"  
    "2024-02-12"  
    "2024-02-26"  
    "2024-02-28"  
    "2024-03-04"  
    "2024-03-11"  
    "2024-03-12"  
)

download_and_extract() {
    local symbol=$1
    local date=$2
    local out_dir="$DATA_DIR/$symbol"
    mkdir -p "$out_dir"
    
    local trades_url="https://data.binance.vision/data/futures/um/daily/aggTrades/$symbol/$symbol-aggTrades-$date.zip"
    local book_url="https://data.binance.vision/data/futures/um/daily/bookTicker/$symbol/$symbol-bookTicker-$date.zip"
    
    # Skip if already have both files
    if [ -f "$out_dir/$symbol-aggTrades-$date.csv" ] && [ -f "$out_dir/$symbol-bookTicker-$date.csv" ]; then
        echo "  $symbol $date: already complete, skipping"
        return 0
    fi
    
    echo "=== Downloading $symbol $date ==="
    
    # Download aggTrades
    if [ ! -f "$out_dir/$symbol-aggTrades-$date.csv" ]; then
        echo "  Downloading aggTrades..."
        if curl -sfL "$trades_url" -o "/tmp/$symbol-aggTrades-$date.zip"; then
            unzip -o -q "/tmp/$symbol-aggTrades-$date.zip" -d "$out_dir/"
            rm "/tmp/$symbol-aggTrades-$date.zip"
        else
            echo "  WARNING: aggTrades not available"
            return 1
        fi
    fi
    
    # Download bookTicker
    if [ ! -f "$out_dir/$symbol-bookTicker-$date.csv" ]; then
        echo "  Downloading bookTicker..."
        if curl -sfL "$book_url" -o "/tmp/$symbol-bookTicker-$date.zip"; then
            unzip -o -q "/tmp/$symbol-bookTicker-$date.zip" -d "$out_dir/"
            rm "/tmp/$symbol-bookTicker-$date.zip"
        else
            echo "  WARNING: bookTicker not available"
            return 1
        fi
    fi
    
    echo "  Done: $symbol $date"
}

echo "Downloading additional Q1 2024 dates..."
echo ""

for date in "${BTCUSDT_DATES[@]}"; do
    download_and_extract "BTCUSDT" "$date" || echo "  Skipping"
done

for date in "${ETHUSDT_DATES[@]}"; do
    download_and_extract "ETHUSDT" "$date" || echo "  Skipping"
done

echo ""
echo "=== Download complete ==="
