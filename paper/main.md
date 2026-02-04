# Liquidity Withdrawal Precedes Price Shocks: Evidence from Cryptocurrency Futures

**Authors:** [Author names to be added]

**Date:** February 2026

---

## Abstract

<!-- Target: 200-250 words -->

Understanding how price shocks originate in financial markets has implications for market design, risk management, and trading strategies. We study whether observable market signals change before rapid price movements occur, focusing on the temporal ordering of liquidity, price, and volume changes around price shock events.

We analyze 452 price shock events across BTCUSDT and ETHUSDT perpetual futures on Binance over 17 trading days. For each event, we detect when liquidity (bid-ask spread), price, and volume first deviate from baseline behavior, then classify events by which signal changed first.

We find that liquidity withdrawal precedes price shocks at a rate significantly above chance. Of 452 events, 200 (44.25%) show liquidity changes first, compared to 186 (41.15%) price-first and 66 (14.60%) volume-first events. A binomial test against a uniform null hypothesis of 33.3% yields p = 2 × 10⁻⁶, and a bootstrap 95% confidence interval of [39.6%, 48.7%] excludes the null proportion.

This finding is consistent with theories of informed trading where market makers or informed participants withdraw liquidity before price-moving events. However, we emphasize that our analysis establishes correlation, not causation. The observed ordering may reflect detection artifacts, latency differences between data feeds, or threshold sensitivities. We discuss these limitations and suggest directions for more robust causal identification.

---

## 1. Introduction

<!-- Target: 400-500 words -->

Rapid price movements in financial markets can have significant consequences. Flash crashes erode market confidence, trigger margin calls, and cause substantial losses for participants caught on the wrong side. Understanding how these events begin—whether they are preceded by detectable warning signals—matters for market design, risk management, and our understanding of price formation.

A central question in market microstructure is whether liquidity conditions change before prices move, or whether price changes drive liquidity responses. If informed traders or market makers systematically withdraw liquidity before price shocks, this signal could in principle be observed and acted upon. Conversely, if prices simply gap without warning and liquidity follows, early detection becomes more difficult.

In this paper, we study the temporal ordering of liquidity, price, and volume changes around price shock events in cryptocurrency futures markets. We ask a specific empirical question: **When a large price movement occurs, does liquidity (measured by bid-ask spread) typically change first, or does price move first?**

We analyze 452 price shock events across BTCUSDT and ETHUSDT perpetual futures on Binance, covering 17 trading days selected for their volatility. For each event, we detect when liquidity, price, and volume first deviate significantly from their baseline behavior using a standardized threshold approach. We then classify each event by which signal changed first.

Our main finding is that liquidity withdrawal precedes price shocks at a rate significantly above what we would expect by chance. Of the 452 events we analyze, 200 (44.25%) show liquidity changing first, compared to 186 (41.15%) price-first and 66 (14.60%) volume-first events. A binomial test against a null hypothesis of 33.3% (uniform across three categories) yields p = 2 × 10⁻⁶, and the bootstrap 95% confidence interval [39.6%, 48.7%] excludes the null proportion.

This paper makes three contributions:

1. **An empirical finding.** We document that liquidity withdrawal precedes price shocks at statistically significant rates in cryptocurrency perpetual futures. This pattern is consistent across both assets in our sample and robust to threshold sensitivity analysis.

2. **A methodology for temporal ordering analysis.** We develop a simple, reproducible approach for detecting signal onset times and classifying events by ordering. The method is transparent and can be applied to other markets and asset classes.

3. **A curated dataset.** We construct a dataset of labeled price shock events with precise onset timestamps, enabling future research on event dynamics.

We emphasize that our analysis establishes correlation, not causation. The observed ordering could reflect threshold artifacts, latency differences, or other confounds. We discuss these limitations in detail and suggest what additional evidence would strengthen or weaken our interpretation.

The remainder of this paper is organized as follows. Section 2 reviews related work. Section 3 describes our data. Section 4 details our methodology. Section 5 presents results. Section 6 discusses interpretation and alternative explanations. Section 7 addresses limitations. Section 8 concludes.

---

## 2. Related Work

<!-- Target: 300-400 words -->
<!-- TODO: MF-V3-009 -->

[Related work placeholder - to be written]

---

## 3. Data

<!-- Target: 300-400 words -->
<!-- TODO: MF-V3-004 -->

[Data section placeholder - to be written]

### 3.1 Data Source

### 3.2 Date Selection

### 3.3 Summary Statistics

**Table 1: Data Summary**

| Metric | Value |
|--------|-------|
| Assets | BTCUSDT, ETHUSDT |
| Trading days | 17 |
| Total events detected | 452 |
| Data source | Binance USD-M Futures |
| Data types | aggTrades, bookTicker |

---

## 4. Methods

<!-- Target: 600-800 words -->
<!-- TODO: MF-V3-005 -->

[Methods section placeholder - to be written]

### 4.1 Event Detection

### 4.2 Window Extraction

### 4.3 Onset Detection

### 4.4 Classification Scheme

### 4.5 Statistical Tests

---

## 5. Results

<!-- Target: 500-700 words -->
<!-- TODO: MF-V3-006 -->

[Results section placeholder - to be written]

### 5.1 Main Finding

### 5.2 Statistical Significance

### 5.3 Asset Comparison

### 5.4 Threshold Sensitivity

**Figure 1: Ordering Proportions**

![Ordering proportions across all detected events](figures/fig1_ordering_proportions.png)

*Figure 1: Distribution of ordering classifications across 452 detected price shock events. Liquidity-first events (44.25%) significantly exceed the null expectation of 33.3% under uniform distribution (p < 0.001).*

**Figure 2: Onset Delta Distribution**

![Distribution of onset time differences](figures/fig2_onset_deltas.png)

*Figure 2: Histogram of onset time differences (liquidity onset minus price onset) for events where both signals were detected. Negative values indicate liquidity changed before price.*

**Figure 3: Example Event**

![Example event showing liquidity withdrawal preceding price shock](figures/fig3_example_event.png)

*Figure 3: Example event window showing the temporal sequence of spread widening (top), price movement (middle), and volume activity (bottom). Vertical dashed line marks the detected price shock timestamp.*

---

## 6. Discussion

<!-- Target: 400-500 words -->
<!-- TODO: MF-V3-007 -->

[Discussion section placeholder - to be written]

### 6.1 Interpretation

### 6.2 Alternative Explanations

### 6.3 Connection to Market Microstructure Theory

---

## 7. Limitations

<!-- Target: 400-500 words -->
<!-- TODO: MF-V3-008 -->

[Limitations section placeholder - to be written]

---

## 8. Conclusion

<!-- Target: 200-250 words -->
<!-- TODO: MF-V3-010 -->

[Conclusion placeholder - to be written]

---

## References

See [references.md](references.md) for full bibliography.

---

## Appendix

See [appendix.md](appendix.md) for supplementary materials including:
- Complete list of analysis dates
- Additional robustness checks
- Per-asset breakdown tables
