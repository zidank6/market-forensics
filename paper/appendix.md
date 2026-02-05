# Appendix

## A. Complete List of Analysis Dates

We analyzed 17 trading days between January and March 2024. The following table lists each date with the number of detected events per asset.

**Table A1: Events by Date and Asset**

| Date | BTCUSDT Events | ETHUSDT Events | Total Events |
|------|----------------|----------------|--------------|
| 2024-01-03 | 16 | 12 | 28 |
| 2024-01-08 | 12 | 10 | 22 |
| 2024-01-09 | 8 | 7 | 15 |
| 2024-01-10 | 18 | 14 | 32 |
| 2024-01-11 | 22 | 20 | 42 |
| 2024-01-12 | 10 | 8 | 18 |
| 2024-02-12 | 14 | 12 | 26 |
| 2024-02-26 | 16 | 15 | 31 |
| 2024-02-28 | 20 | 18 | 38 |
| 2024-03-04 | 25 | 22 | 47 |
| 2024-03-05 | 45 | 38 | 83 |
| 2024-03-11 | 12 | 10 | 22 |
| 2024-03-12 | 8 | 7 | 15 |
| 2024-03-13 | 6 | 8 | 14 |
| 2024-03-14 | 5 | 7 | 12 |
| 2024-03-27 | 1 | 4 | 5 |
| 2024-03-29 | 1 | 1 | 2 |
| **Total** | **239** | **213** | **452** |

*Note: March 5, 2024 had the highest event count (83 events), corresponding to a period of significant Bitcoin price volatility.*

## B. Parameter Configuration

The following parameters were used for event detection and classification:

**Table A2: Analysis Parameters**

| Parameter | Value | Description |
|-----------|-------|-------------|
| Price shock threshold | 0.5% | Minimum price change to trigger event |
| Rolling window | 60 seconds | Window for computing price change |
| Pre-event window | 300 seconds | Baseline computation window |
| Post-event window | 300 seconds | Onset detection window |
| Onset threshold multiplier | 2.0$\sigma$ | Standard deviations above baseline |
| Volume bucket size | 5 seconds | Aggregation window for volume signal |
| Bootstrap resamples | 1,000 | For confidence interval estimation |
| Bootstrap seed | 42 | For reproducibility |

## C. Per-Asset Detailed Results

**Table A3: Full Classification Breakdown by Asset**

| Classification | BTCUSDT | % | ETHUSDT | % | Total | % |
|----------------|---------|---|---------|---|-------|---|
| Liquidity-first | 110 | 46.0% | 90 | 42.3% | 200 | 44.25% |
| Price-first | 94 | 39.3% | 92 | 43.2% | 186 | 41.15% |
| Volume-first | 35 | 14.6% | 31 | 14.6% | 66 | 14.60% |
| **Total** | **239** | 100% | **213** | 100% | **452** | 100% |

## D. Statistical Test Details

**Binomial Test**

- Null hypothesis: H$_0$: $p_0 = 1/3$ (uniform distribution across three categories)
- Alternative hypothesis: H$_1$: $p \neq 1/3$
- Test statistic: Observed proportion = 200/452 = 0.4425
- p-value: $2 \times 10^{-6}$ (two-sided)
- Conclusion: Reject H$_0$ at $\alpha = 0.01$

**Bootstrap Confidence Interval**

- Method: Percentile bootstrap
- Number of resamples: 1,000
- Random seed: 42
- 95% CI: [39.6%, 48.7%]
- Interpretation: The confidence interval excludes the null proportion of 33.3%, providing additional evidence that the observed liquidity-first rate is significantly above chance.

## E. Data Source Details

All data was obtained from Binance's public data repository:

- **URL**: https://data.binance.vision/data/futures/um/daily/
- **Feed types**: aggTrades (trade executions), bookTicker (best bid/ask)
- **Assets**: BTCUSDT, ETHUSDT (USD-M perpetual futures)
- **Format**: CSV files compressed as ZIP archives
- **Timestamp precision**: Milliseconds (Unix epoch)

Data was canonicalized into a standard format:
- `trades.csv`: timestamp, price, quantity, side
- `tob.csv`: timestamp, bid_price, bid_qty, ask_price, ask_qty

All timestamps were converted to ISO 8601 format with microsecond precision for analysis.
