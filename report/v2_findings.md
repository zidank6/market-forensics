# Market Forensics v2: Multi-Asset Event Ordering Analysis

**Version:** 2.0
**Status:** Results template (run pipeline to populate)
**Date:** 2026-02

---

## Summary

This document reports the findings from the Market Forensics v2 analysis, which examines the temporal ordering of liquidity, volume, and price changes during market stress events across multiple assets and dates.

**Key Question:** Does liquidity withdrawal (spread widening) systematically precede price movements during stress events, or does the ordering occur at chance rates?

**Approach:**
1. Detect price shock events (>0.5% moves within 60s windows)
2. Extract pre/post event windows (300s each)
3. Determine onset times for liquidity, volume, and price signals
4. Classify events by which signal moves first
5. Test statistical significance vs. null hypothesis (33% for 3-class uniform)

**Results Summary:**
- See `outputs/v2_stats.json` for detailed statistics
- See `outputs/figures/` for visualizations

To generate results, run:
```bash
python scripts/run_v2_analysis.py
python scripts/aggregate_v2_results.py
python scripts/run_statistics.py
python scripts/generate_v2_figures.py
```

---

## Data

### Data Source

- **Exchange:** Binance USD-M Futures
- **Data Types:** Aggregated trades (`aggTrades`), Best bid/ask (`bookTicker`)
- **Source:** data.binance.vision (public historical data)

### Assets Analyzed

| Asset | Dates | Notes |
|-------|-------|-------|
| BTCUSDT | 17 days | Jan 2024 - Mar 2024 |
| ETHUSDT | 14 days | Jan 2024 - Mar 2024 |

### Key Dates

Dates were selected for high expected volatility:

- **2024-01-10:** BTC ETF approval day
- **2024-01-11:** First ETF trading day
- **2024-03-05:** BTC all-time-high run
- **2024-03-14:** BTC ATH ($73k)

Full date manifest: `config/dates.json`

### Data Volume

- Total canonical data: ~60GB
- Format: CSV files with `trades.csv` and `tob.csv` per date
- Location: `data/binance/futures_um/{ASSET}/canonical/{DATE}/`

---

## Methods

### Event Detection

Price shock events are detected when midprice moves by at least `threshold_pct` within a rolling window:

- **Default threshold:** 0.5%
- **Rolling window:** 60 seconds
- **Deduplication:** Keep largest magnitude event within window period

### Window Extraction

For each event, extract:
- **Pre-window:** 300 seconds before event
- **Post-window:** 300 seconds after event

Overlapping events are filtered using "keep_first" strategy.

### Onset Detection

For each signal type (liquidity, volume, price), onset is detected when the signal exceeds:

```
onset_threshold = baseline_mean + k * baseline_std
```

Where:
- `baseline_mean`, `baseline_std` computed from pre-window data
- `k = 2.0` (configurable via `threshold_std_multiplier`)

**Signal definitions:**
- **Liquidity:** Bid-ask spread (widening = threshold crossing)
- **Volume:** Trade volume in 5-second buckets
- **Price:** Midprice (direction-aware threshold)

### Classification

Events are classified based on which signal has the earliest onset time:

| Classification | Meaning |
|----------------|---------|
| liquidity-first | Spread widened before volume/price |
| volume-first | Volume spiked before spread/price |
| price-first | Price moved before spread/volume |
| undetermined | Insufficient data or no crossings |

---

## Results

### Event Counts

After running the v2 pipeline:

```
python scripts/run_v2_analysis.py
python scripts/aggregate_v2_results.py
```

Results are aggregated in `outputs/v2_summary.csv`:

| Column | Description |
|--------|-------------|
| date | Event date |
| asset | BTCUSDT or ETHUSDT |
| event_id | Unique event identifier |
| classification | Ordering classification |
| onset_liquidity_sec | Liquidity onset (seconds from event) |
| onset_price_sec | Price onset (seconds from event) |
| onset_volume_sec | Volume onset (seconds from event) |
| onset_delta | onset_liquidity - onset_price |

### Statistical Analysis

Run statistical tests:
```bash
python scripts/run_statistics.py
```

Results in `outputs/v2_stats.json`:

**Null Hypothesis:** If ordering is random (3-class uniform), each classification should occur ~33.3% of the time.

**Test:** Two-sided binomial test of liquidity-first proportion vs. 33%.

**Confidence Interval:** Bootstrap 95% CI (1000 resamples, percentile method).

### Figures

Run figure generation:
```bash
python scripts/generate_v2_figures.py
```

**Figure 1: Ordering Proportions**
- File: `outputs/figures/ordering_proportions.png`
- Bar chart showing percentage of each classification
- Red dashed line indicates 33% null hypothesis

**Figure 2: Onset Delta Distribution**
- File: `outputs/figures/onset_deltas.png`
- Histogram of (t_liquidity - t_price) in seconds
- Negative values = liquidity leads price

---

## Robustness

### Threshold Sensitivity Analysis

Run sensitivity analysis:
```bash
python scripts/run_v2_sensitivity.py
```

Tests thresholds: 0.3%, 0.4%, 0.5%, 0.6%, 0.7%

Results in `outputs/sensitivity.csv`:

| threshold | n_events | pct_liquidity_first |
|-----------|----------|---------------------|
| 0.3 | ? | ? |
| 0.4 | ? | ? |
| 0.5 | ? | ? |
| 0.6 | ? | ? |
| 0.7 | ? | ? |

**Interpretation guidance:**
- If `pct_liquidity_first` is stable across thresholds (e.g., 40-50%), the finding is robust.
- If it varies widely (e.g., 20-60%), the finding is threshold-sensitive.

### Parameter Sensitivity

Key parameters that may affect results:

| Parameter | Default | Effect of Increase |
|-----------|---------|-------------------|
| `price_shock_threshold_pct` | 0.5% | Fewer, larger events |
| `rolling_window_seconds` | 60s | Longer event windows |
| `threshold_std_multiplier` | 2.0 | Later onset detection |
| `pre_event_seconds` | 300s | Longer baseline period |

---

## Limitations

### Methodological Limitations

1. **Temporal ≠ Causal:** The signal that changes first is not necessarily the cause of subsequent changes. This analysis describes correlation, not causation.

2. **Threshold Arbitrariness:** The k×std onset threshold assumes roughly normal distributions. Market data often exhibits fat tails and outliers.

3. **Single Exchange:** Data is from Binance only. Cross-exchange arbitrage and information flow are not captured.

4. **Latency Effects:** Data feed latencies between trade and quote streams may introduce artificial ordering artifacts at millisecond scales.

### Data Limitations

1. **Top-of-Book Only:** Full order book depth would provide richer liquidity signals (e.g., depth changes beyond BBO).

2. **Timestamp Precision:** Detection precision is limited by data granularity (typically 100ms for bookTicker).

3. **Date Selection Bias:** Dates were selected for high volatility, which may not represent typical market conditions.

### Scope Limitations

1. **No External Catalysts:** News, social media, or on-chain events are not incorporated.

2. **No Cross-Asset Modeling:** Each asset is analyzed independently. Lead-lag relationships between BTC and ETH are not examined.

3. **No Prediction:** This is forensic analysis of historical patterns, not forward-looking prediction.

---

## Conclusion

**To determine whether liquidity-first ordering is systematic:**

1. Run the full pipeline: `python scripts/run_v2_analysis.py`
2. Aggregate results: `python scripts/aggregate_v2_results.py`
3. Run statistics: `python scripts/run_statistics.py`
4. Check the output:

If the binomial test p-value < 0.05 and the observed liquidity-first proportion exceeds 33%, we can conclude that liquidity changes precede price changes at a rate significantly higher than chance.

If the bootstrap 95% CI excludes 33%, this provides additional confidence in the finding.

Check `outputs/v2_stats.json` for the actual results after running the pipeline.

---

## Appendix: Pipeline Execution Guide

### Full V2 Analysis

```bash
# 1. Run pipeline on all (asset, date) pairs
python scripts/run_v2_analysis.py

# 2. Aggregate results
python scripts/aggregate_v2_results.py

# 3. Run statistical tests
python scripts/run_statistics.py

# 4. Generate figures
python scripts/generate_v2_figures.py

# 5. (Optional) Run sensitivity analysis
python scripts/run_v2_sensitivity.py
```

### Output Files

```
outputs/
├── v2/
│   ├── BTCUSDT/
│   │   └── {date}/
│   │       ├── metrics/event_orderings.csv
│   │       └── ...
│   └── ETHUSDT/
│       └── {date}/
│           └── ...
├── v2_summary.csv          # Aggregated event data
├── v2_stats.json           # Statistical test results
├── sensitivity.csv         # Threshold sensitivity results
└── figures/
    ├── ordering_proportions.png
    ├── ordering_proportions.csv
    ├── onset_deltas.png
    └── onset_deltas.csv
```

---

*This document serves as a template for v2 findings. Populate with actual statistics after running the analysis pipeline on production data.*
