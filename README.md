# market-forensics

Research/forensics pipeline for crypto market microstructure stress events.

## Overview

This project reconstructs short event windows around sudden price moves and determines the sequence of changes in:
- **Liquidity** (spread / top-of-book)
- **Trading behavior** (trades/volume)
- **Price** (mid/last)

## Project Structure

```
market-forensics/
├── config/              # Configuration files (thresholds, window sizes)
│   └── default.json     # Default configuration
├── data/
│   └── sample/          # Sample datasets for testing
├── outputs/             # Pipeline outputs (deterministic)
│   ├── windows/         # Extracted event windows
│   ├── metrics/         # Computed metrics
│   └── plots/           # Generated visualizations
├── src/market_forensics/
│   ├── data/            # Data loading and validation
│   ├── events/          # Event detection
│   ├── windows/         # Window extraction
│   ├── metrics/         # Metrics computation
│   └── plots/           # Visualization
└── scripts/             # Runner scripts
```

## How to Run

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd market-forensics

# (Optional) Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode (once setup.py/pyproject.toml is added)
# pip install -e .
```

### Running the Pipeline

```bash
# Run full pipeline with default config
python -m market_forensics.run --config config/default.json

# Run with custom config
python -m market_forensics.run --config path/to/config.json
```

### Configuration

Edit `config/default.json` to customize:
- `exchange`: Target exchange
- `symbols`: List of trading pairs to analyze
- `event_detection.price_shock_threshold_pct`: Price move threshold (%)
- `event_detection.rolling_window_seconds`: Window for detecting moves
- `windows.pre_event_seconds`: Time before event to extract
- `windows.post_event_seconds`: Time after event to extract

### Running Tests

```bash
# Run tests (when available)
python -m pytest -q
```

## License

MIT
