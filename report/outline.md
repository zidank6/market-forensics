# Market Microstructure Event Analysis: A Forensic Approach

**Status:** Methodology draft (not empirical claims)

---

## 1. Introduction

This document describes a methodology for analyzing market microstructure around sudden price
movements ("stress events" or "price shocks"). The goal is to characterize the temporal sequence
of changes in liquidity, trading activity, and price during these events.

### 1.1 Research Question

When a sudden price movement occurs, what changes first—liquidity (spread widening), trading
volume (activity surge), or the price itself? Understanding this ordering may provide insight
into the microstructure dynamics of stress events.

### 1.2 Scope

- **In scope:** Detecting price shocks, extracting data windows, computing metrics, and
  classifying the ordering of changes.
- **Out of scope:** Causal inference, predictive modeling, real-time alerting, or trading
  strategies.

---

## 2. Data

### 2.1 Data Sources

The pipeline accepts two types of market data:

1. **Trade data:** Individual trade executions with timestamp, price, size, and side.
2. **Top-of-book (TOB) data:** Best bid/ask prices and sizes at each timestamp.

Data can be loaded from CSV or JSONL files. See `data/sample/` for example format.

### 2.2 Data Schema

**Trade record:**
| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | UTC timestamp of trade |
| symbol | string | Trading pair (e.g., "BTC-USDT") |
| price | float | Execution price |
| size | float | Trade size in base currency |
| side | enum | Buy or sell |

**Top-of-book record:**
| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | UTC timestamp of snapshot |
| symbol | string | Trading pair |
| bid_price | float | Best bid price |
| bid_size | float | Size at best bid |
| ask_price | float | Best ask price |
| ask_size | float | Size at best ask |

### 2.3 Sample Data

A sample dataset is provided in `data/sample/` containing 25 trades and 25 TOB snapshots
for BTC-USDT over a 2-minute period with a price decline.

---

## 3. Method

### 3.1 Event Detection

Price shock events are detected using a rolling window approach:

1. For each data point, compute the percentage price change from the earliest price within
   the rolling window.
2. If the change exceeds the configured threshold, flag an event.
3. Deduplicate nearby events by keeping the largest magnitude within each window period.

**Parameters (configurable):**
- `price_shock_threshold_pct`: Minimum percentage move to trigger (default: 0.5%)
- `rolling_window_seconds`: Look-back window duration (default: 60s)

### 3.2 Window Extraction

For each detected event, extract standardized time windows:

- **Pre-window:** Data from `(event_time - pre_seconds, event_time)`
- **Post-window:** Data from `[event_time, event_time + post_seconds)`

**Parameters:**
- `pre_event_seconds`: Duration before event (default: 300s)
- `post_event_seconds`: Duration after event (default: 300s)

**Overlap handling:** When events occur close together, the "keep_first" strategy retains
the first event and skips subsequent events whose timestamp falls within the first event's
post-window.

### 3.3 Metrics Computation

For each window (pre and post), compute:

**Trade-based metrics:**
- Trade count
- Total trade volume
- Average trade size
- VWAP (volume-weighted average price)
- Realized volatility (standard deviation of log returns)
- Min/max price

**Quote-based metrics:**
- Average spread (ask - bid)
- Average spread in basis points
- Average midprice

---

## 4. Metrics

### 4.1 Output Files

Metrics are saved to `outputs/metrics/` in both JSON and CSV formats:

- `event_metrics.json` / `event_metrics.csv`: Full metrics per window
- `event_orderings.json` / `event_orderings.csv`: Ordering classifications

### 4.2 Metric Definitions

| Metric | Formula | Notes |
|--------|---------|-------|
| VWAP | Σ(price × size) / Σ(size) | Volume-weighted average |
| Realized volatility | std(log returns) | Needs ≥2 data points |
| Spread (bps) | (spread / midprice) × 10,000 | Normalized spread |

---

## 5. Event Definition

### 5.1 Price Shock Definition

A price shock is defined operationally as: a moment when the price moves by at least
`threshold_pct` percent from its reference value within a rolling window of `window_seconds`.

This definition:
- Is purely statistical (no market structure assumptions)
- Is symmetric (detects both up and down moves)
- Is configurable via the config file

### 5.2 Change Onset Definition

For ordering analysis, "onset" of a signal (liquidity, volume, price) is defined as the
first timestamp when the signal exceeds:

```
threshold = baseline_mean + k × baseline_std
```

Where `baseline_mean` and `baseline_std` are computed from the pre-event window, and `k`
is a configurable multiplier (default: 2.0).

---

## 6. Results

### 6.1 Per-Event Plots

For each detected event, the pipeline generates:

- **Price plot:** `outputs/plots/events/{window_id}_price.png`
  - Shows midprice trajectory and trade prices around the event
- **Spread plot:** `outputs/plots/events/{window_id}_spread.png`
  - Shows bid-ask spread evolution
- **Volume plot:** `outputs/plots/events/{window_id}_volume.png`
  - Shows trade volume in time buckets

### 6.2 Aggregate Summary

- **Ordering distribution:** `outputs/plots/ordering_distribution.png`
  - Bar chart of classification counts
- **By-symbol breakdown:** `outputs/plots/ordering_by_symbol.png`
  - Grouped bar chart per trading pair
- **Summary table:** `outputs/plots/ordering_summary.csv`
  - Counts of each classification by symbol

### 6.3 Classification Types

| Classification | Interpretation |
|----------------|----------------|
| liquidity-first | Spread widened before volume spike or price move |
| volume-first | Volume spiked before spread widened or price moved |
| price-first | Price moved before spread or volume changed |
| undetermined | Insufficient data or no threshold crossings |

---

## 7. Robustness

### 7.1 Sensitivity to Parameters

Key parameters that affect results:

| Parameter | Higher value effect | Lower value effect |
|-----------|--------------------|--------------------|
| price_shock_threshold_pct | Fewer, larger events | More, smaller events |
| rolling_window_seconds | Events can span longer periods | More localized events |
| threshold_std_multiplier (k) | Later onset detection | Earlier onset detection |

### 7.2 Recommended Checks

1. **Vary threshold:** Run with ±50% threshold to assess event count sensitivity.
2. **Vary k:** Try k=1.5, 2.0, 2.5 to assess ordering classification stability.
3. **Check sparse windows:** Events with few pre-window data points have unreliable baselines.

---

## 8. Limitations

### 8.1 Methodological Limitations

1. **No causality:** Temporal ordering does not imply causation. The signal that changes
   first is not necessarily the cause of subsequent changes.

2. **Threshold arbitrariness:** Using k×std assumes roughly normal distributions. Market
   data often exhibits heavy tails.

3. **Single-asset focus:** Each event is analyzed independently per symbol. Cross-asset
   effects are not modeled.

4. **Latency ignored:** Data feed latencies between trade and quote streams may introduce
   artificial ordering artifacts.

### 8.2 Data Limitations

1. **Sample data:** The included sample is synthetic and brief. Real analysis requires
   production market data.

2. **Timestamp resolution:** Detection precision is limited by data granularity. Sub-second
   dynamics require sub-second data.

3. **Quote depth:** Only top-of-book is used. Full order book would provide richer liquidity
   signals.

### 8.3 Scope Limitations

1. **No news/sentiment:** External catalysts are not incorporated.
2. **No cross-venue:** Single-exchange data; cross-venue arbitrage effects not captured.
3. **No simulation:** Results describe historical patterns, not forward-looking predictions.

---

## Appendix: Pipeline Outputs Reference

```
outputs/
├── run_summary.json           # Manifest of all generated files
├── windows/
│   ├── {window_id}_event.json
│   ├── {window_id}_pre_trades.csv
│   ├── {window_id}_post_trades.csv
│   ├── {window_id}_pre_tob.csv
│   └── {window_id}_post_tob.csv
├── metrics/
│   ├── event_metrics.json
│   ├── event_metrics.csv
│   ├── event_orderings.json
│   └── event_orderings.csv
└── plots/
    ├── events/
    │   ├── {window_id}_price.png
    │   ├── {window_id}_spread.png
    │   └── {window_id}_volume.png
    ├── ordering_distribution.png
    ├── ordering_by_symbol.png
    └── ordering_summary.csv
```

---

*This report scaffold describes methodology only. Empirical findings should not be inferred
until the pipeline is run on representative production data with appropriate statistical
analysis.*
