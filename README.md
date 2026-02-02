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
- `ordering_detection.threshold_std_multiplier`: Number of standard deviations for onset detection

## Change Ordering Detection: Assumptions & Limitations

The ordering detection module (`src/market_forensics/events/ordering.py`) attempts to determine
"what changes first" within each event window. This section documents the operational rules,
assumptions, and known limitations.

### Operational Rule for Change Onset

A signal is considered to have "onset" when it first exceeds a threshold defined as:

```
threshold = baseline_value + k * baseline_std
```

Where:
- `baseline_value`: Mean of the signal in the pre-event window
- `baseline_std`: Standard deviation in the pre-event window
- `k`: Configurable multiplier (default 2.0), set via `ordering_detection.threshold_std_multiplier`

### Signals Tracked

1. **Liquidity (spread)**: Spread widening detected when `spread >= baseline + k*std`
2. **Volume**: Trade volume (bucketed by time) exceeding `baseline + k*std`
3. **Price**: Midprice moving beyond `baseline ± k*std` (direction-dependent)

### Classification

Events are classified based on which signal first crosses its threshold:
- `liquidity-first`: Spread widens before volume or price changes
- `volume-first`: Volume spikes before spread or price changes
- `price-first`: Price moves before spread or volume changes
- `undetermined`: No signal crossed threshold, or insufficient data

### Assumptions

1. **Stationarity of baseline**: The pre-event window is assumed to represent "normal" conditions.
   If the pre-event period is itself unusual, thresholds may be miscalibrated.

2. **Independence of signals**: Each signal is analyzed independently. Cross-correlations
   or lead-lag relationships between signals are not modeled.

3. **Threshold appropriateness**: Using k*std assumes roughly normal distributions. For highly
   skewed or fat-tailed data, this threshold may trigger too early or too late.

4. **Data granularity**: Detection precision is limited by data timestamp resolution.
   Simultaneous onsets (within the same timestamp) cannot be ordered.

5. **Volume bucketing**: Volume is aggregated into fixed time buckets (default 5s). Events
   within a bucket are summed, potentially obscuring sub-bucket dynamics.

### Limitations

1. **No causality claims**: Temporal ordering does not imply causation. A signal changing
   first does not mean it caused subsequent changes.

2. **Sparse data sensitivity**: With few data points in the pre-window, baseline statistics
   are unreliable. A minimum std floor is used but may be inappropriate.

3. **Single threshold**: Uses one threshold across all events. Different market conditions
   may warrant different sensitivities.

4. **No latency adjustment**: Does not account for potential differences in data feed latencies
   between trade and quote streams.

5. **Limited to detected events**: Only analyzes windows around events that were detected
   by the price-shock detector. Events missed by that detector are not analyzed.

### Running Tests

```bash
# Run tests (when available)
python -m pytest -q
```

## License

MIT
