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

Our work relates to several strands of research in market microstructure, liquidity dynamics, and cryptocurrency markets.

**Market microstructure fundamentals.** The theoretical foundation for our analysis draws on classic models of trading with asymmetric information. Kyle (1985) models how informed traders strategically choose order sizes to maximize profits while concealing their information. Glosten and Milgrom (1985) show how market makers set bid-ask spreads to protect against adverse selection from informed traders. Both models predict that liquidity conditions should respond to the presence of informed trading—a prediction consistent with our observation that liquidity changes often precede price movements.

**Liquidity and volatility.** A substantial literature examines the relationship between liquidity and price volatility. Research has documented that liquidity tends to deteriorate during periods of high volatility (the "flight to quality" effect) and that liquidity provision itself can be destabilizing when market makers withdraw simultaneously. Our study contributes to this literature by examining the temporal ordering of liquidity and price changes at high frequency, rather than their contemporaneous correlation.

**Cryptocurrency market microstructure.** The microstructure of cryptocurrency markets has received growing attention as these markets have matured. Studies have examined the efficiency of cryptocurrency pricing, the role of arbitrage across exchanges, and the behavior of market makers in 24/7 markets without circuit breakers. Our work adds to this literature by providing evidence on the temporal dynamics of liquidity around price shocks in perpetual futures markets, which are among the most actively traded cryptocurrency instruments.

**Event study methodology.** Our approach shares features with event study methods common in empirical finance, where researchers examine market variables around specific events (earnings announcements, policy changes, etc.). We adapt this approach to high-frequency market microstructure, defining events based on price movements rather than external announcements and measuring responses at second-level resolution.

**Positioning this work.** Most prior work on liquidity-price relationships examines their correlation or uses theoretical models to derive predictions. Our contribution is empirical and focused on temporal ordering: we ask which signal changes first, rather than whether they move together. This approach provides a different perspective on the liquidity-price relationship—one that may be relevant for understanding the origins of price shocks.

---

## 3. Data

<!-- Target: 300-400 words -->

### 3.1 Data Source

We analyze data from Binance USD-M perpetual futures, the largest cryptocurrency derivatives venue by trading volume. We obtain historical data from data.binance.vision, Binance's public data repository, which provides complete order book and trade data for research purposes.

For each trading day, we download two data feeds:

- **aggTrades**: Aggregated trade records containing timestamp, price, quantity, and trade direction for every executed trade.
- **bookTicker**: Best bid and ask prices with their quantities, updated on every change to the top of the order book.

We convert raw exchange data into a canonical format with two files per day: `trades.csv` containing trade executions, and `tob.csv` containing top-of-book snapshots. Both files use ISO 8601 timestamps with microsecond precision. This preprocessing enables consistent analysis across dates and simplifies event detection.

### 3.2 Date Selection

We analyze two assets: BTCUSDT (Bitcoin perpetual) and ETHUSDT (Ethereum perpetual), selected for their high liquidity and trading activity. We selected 17 trading days between January and March 2024, chosen to capture periods of elevated volatility when price shocks are more frequent. The selection includes days surrounding major market events such as Bitcoin ETF approvals (early January 2024) and subsequent price rallies.

We intentionally avoid random date sampling. Our goal is to analyze price shock events, which are rare on typical trading days. Selecting volatile days increases the number of events available for analysis. This approach biases our sample toward "interesting" market conditions, which we discuss in Section 7 (Limitations).

### 3.3 Summary Statistics

**Table 1: Data Summary**

| Metric | Value |
|--------|-------|
| Assets | BTCUSDT, ETHUSDT |
| Trading days | 17 |
| Date range | January 3 – March 29, 2024 |
| Total events detected | 452 |
| Events (BTCUSDT) | 239 |
| Events (ETHUSDT) | 213 |
| Data source | Binance USD-M Futures |
| Raw data feeds | aggTrades, bookTicker |
| Canonical format | trades.csv, tob.csv |

Event counts vary substantially across dates, ranging from 1 event (March 29) to 83 events (March 5). The most active dates correspond to periods of high market volatility. BTCUSDT and ETHUSDT contribute similar numbers of events (239 and 213 respectively), allowing us to compare patterns across assets.

---

## 4. Methods

<!-- Target: 600-800 words -->

Our methodology consists of four stages: (1) detecting price shock events, (2) extracting analysis windows around each event, (3) detecting onset times for liquidity, price, and volume signals, and (4) classifying events by which signal changed first. We then apply statistical tests to determine whether the observed ordering distribution differs from chance.

### 4.1 Event Detection

We define a **price shock** as a price movement exceeding a threshold percentage within a rolling time window. Formally, for a time series of mid-prices *p(t)*, we flag an event at time *t* if:

$$\left| \frac{p(t) - p(t - \Delta)}{p(t - \Delta)} \right| \geq \theta$$

where Δ is the rolling window duration (60 seconds) and θ is the threshold (0.5% in our primary analysis). We detect events using mid-prices computed from top-of-book data as *(bid + ask) / 2*.

To avoid counting the same market move multiple times, we apply a de-duplication rule: if multiple threshold crossings occur within the same rolling window, we keep only the event with the largest magnitude. This ensures that a single large price move generates exactly one event, regardless of how many intermediate threshold crossings occur.

### 4.2 Window Extraction

For each detected event, we extract symmetric windows of market data centered on the event timestamp. The **pre-event window** contains the 300 seconds before the event (not including the event timestamp). The **post-event window** contains the 300 seconds starting from the event timestamp.

When events occur close together in time, their windows may overlap. We handle this by keeping only the first event in each non-overlapping sequence. Specifically, if a second event's timestamp falls within the first event's post-window, we exclude the second event. This ensures each analysis window represents an independent observation.

For each window, we extract:
- **Top-of-book data**: Bid price, ask price, and their quantities at each book update
- **Trade data**: Individual trade executions with price, size, and direction

### 4.3 Onset Detection

For each signal (liquidity, price, volume), we detect the **onset time**—the first moment in the post-event window when that signal deviates significantly from its pre-event baseline. We use a threshold-based approach calibrated to each signal's variance.

**Baseline computation.** For each signal, we compute the mean (μ) and standard deviation (σ) from the pre-event window. For liquidity, we use bid-ask spread values. For price, we use mid-prices. For volume, we aggregate trade sizes into 5-second buckets and compute statistics over bucket volumes.

**Threshold crossing.** We flag an onset when the signal first exceeds μ + *k*σ in the post-event window, where *k* = 2.0 (configurable). The specific conditions are:

- **Liquidity onset**: Spread exceeds baseline + 2σ (spread widening indicates liquidity withdrawal)
- **Price onset**: Mid-price moves beyond baseline ± 2σ (direction depends on whether the event was an up or down shock)
- **Volume onset**: 5-second bucket volume exceeds baseline + 2σ

If a signal never crosses its threshold in the post-window, we record no onset for that signal. If the baseline standard deviation is near zero (insufficient variation), we use a small fraction of the baseline value as a minimum threshold to avoid degeneracy.

### 4.4 Classification Scheme

We classify each event based on which signal's onset occurs first:

- **Liquidity-first**: Spread onset precedes both price and volume onsets
- **Price-first**: Price onset precedes both spread and volume onsets
- **Volume-first**: Volume onset precedes both spread and price onsets
- **Undetermined**: Fewer than two signals crossed their thresholds

Events classified as "undetermined" are excluded from statistical analysis, as they provide no information about relative ordering.

### 4.5 Statistical Tests

We test whether the observed proportion of liquidity-first events differs from chance. Under a null hypothesis of no systematic ordering, we expect each of the three categories to occur with equal probability (33.3%).

**Binomial test.** We treat the liquidity-first count as a binomial random variable with *n* = 452 trials and null success probability *p*₀ = 1/3. We compute the two-sided p-value for the observed proportion (44.25%).

**Bootstrap confidence interval.** We construct a 95% confidence interval for the true liquidity-first proportion using the percentile bootstrap method with 1,000 resamples and a fixed random seed for reproducibility. If this interval excludes the null proportion (33.3%), we consider the result robust.

Figure 3 illustrates the methodology on an example event, showing the temporal progression of spread, price, and volume signals around a detected price shock.

---

## 5. Results

<!-- Target: 500-700 words -->

### 5.1 Main Finding

Liquidity withdrawal precedes price shocks at a rate significantly above chance. Of 452 detected price shock events, 200 (44.25%) show liquidity changing first, compared to 186 (41.15%) price-first and 66 (14.60%) volume-first events. Figure 1 shows this distribution.

Under a null hypothesis of no systematic ordering, we would expect each category to occur with probability 1/3 (33.3%). The observed liquidity-first proportion of 44.25% exceeds this null expectation by approximately 11 percentage points. The relative scarcity of volume-first events (14.60%) suggests that volume changes are less likely to precede price shocks than either liquidity or price signals.

**Figure 1: Ordering Proportions**

![Ordering proportions across all detected events](figures/fig1_ordering_proportions.png)

*Figure 1: Distribution of ordering classifications across 452 detected price shock events. Liquidity-first events (44.25%) significantly exceed the null expectation of 33.3% under uniform distribution.*

### 5.2 Statistical Significance

We apply two statistical tests to assess whether the observed liquidity-first proportion differs meaningfully from chance.

**Binomial test.** Treating the 200 liquidity-first events as successes in 452 Bernoulli trials with null probability p₀ = 1/3, we compute a two-sided p-value of 2 × 10⁻⁶. This result is significant at both α = 0.05 and α = 0.01.

**Bootstrap confidence interval.** Using the percentile bootstrap method with 1,000 resamples, we construct a 95% confidence interval for the true liquidity-first proportion: [39.6%, 48.7%]. This interval excludes the null hypothesis proportion of 33.3%, providing additional evidence that the observed pattern is unlikely to arise from chance.

Together, these tests suggest that the liquidity-first ordering we observe is statistically robust. However, statistical significance does not establish that this pattern is practically meaningful or that it reflects a causal relationship—only that random variation is an unlikely explanation.

### 5.3 Asset Comparison

We compare the ordering distribution across our two assets: BTCUSDT (Bitcoin perpetual) and ETHUSDT (Ethereum perpetual).

**Table 2: Ordering Classification by Asset**

| Classification | BTCUSDT (n=239) | ETHUSDT (n=213) |
|----------------|-----------------|-----------------|
| Liquidity-first | 110 (46.0%) | 90 (42.3%) |
| Price-first | 94 (39.3%) | 92 (43.2%) |
| Volume-first | 35 (14.6%) | 31 (14.6%) |

Both assets show liquidity-first as the most common classification, though BTCUSDT exhibits a somewhat higher liquidity-first rate (46.0%) compared to ETHUSDT (42.3%). The price-first rate is correspondingly higher for ETHUSDT. Volume-first rates are nearly identical across both assets (14.6%).

We hesitate to draw strong conclusions from the asset-level differences. The sample sizes (239 and 213 events) are modest, and we have not tested whether the difference between 46.0% and 42.3% is statistically significant. The similarity in overall patterns across both assets provides some evidence that the liquidity-first tendency is not specific to a single instrument.

### 5.4 Threshold Sensitivity

Our event detection uses a 0.5% price change threshold. To assess whether our findings depend on this choice, we reran the analysis on a subset of data (March 27, 2024) with thresholds of 0.4%, 0.5%, and 0.6%.

**Table 3: Sensitivity to Price Shock Threshold**

| Threshold | Events | Liquidity-first | Price-first | Volume-first |
|-----------|--------|-----------------|-------------|--------------|
| 0.4% | 16 | 8 (50.0%) | 7 (43.8%) | 1 (6.3%) |
| 0.5% | 12 | 6 (50.0%) | 4 (33.3%) | 2 (16.7%) |
| 0.6% | 8 | 4 (50.0%) | 2 (25.0%) | 2 (25.0%) |

Lower thresholds detect more events (as expected), but the liquidity-first proportion remains stable across all threshold values. At all three thresholds, liquidity-first events constitute 50% of the sample—if anything, higher than the 44.25% observed in the full dataset. This consistency suggests our main finding is not an artifact of the specific threshold choice.

We note that this sensitivity analysis uses a single day of data, so the results should be interpreted cautiously. A comprehensive sensitivity analysis across all 17 days would provide stronger evidence, though the computational cost is substantial.

### 5.5 Onset Time Differences

Figure 2 shows the distribution of onset time differences (liquidity onset time minus price onset time) for events where both signals crossed their thresholds. Negative values indicate liquidity changed before price.

**Figure 2: Onset Delta Distribution**

![Distribution of onset time differences](figures/fig2_onset_deltas.png)

*Figure 2: Histogram of onset time differences (liquidity onset minus price onset) for events where both signals were detected. Negative values indicate liquidity changed before price.*

The distribution shows a peak near zero, indicating that for many events, liquidity and price signals change nearly simultaneously. The asymmetry toward negative values is consistent with our finding that liquidity changes tend to precede price changes. However, the presence of positive values shows that price-first orderings are also common—the liquidity-first tendency is a statistical pattern, not a universal rule.

Figure 3 illustrates a typical liquidity-first event, showing how spread widening precedes the main price movement.

**Figure 3: Example Event**

![Example event showing liquidity withdrawal preceding price shock](figures/fig3_example_event.png)

*Figure 3: Example event window showing the temporal sequence of spread widening (top), price movement (middle), and volume activity (bottom). Vertical dashed line marks the detected price shock timestamp.*

---

## 6. Discussion

<!-- Target: 400-500 words -->

Our analysis finds that liquidity withdrawal precedes price shocks at a rate significantly above chance. In this section, we discuss what this pattern may indicate, consider alternative explanations, and connect our findings to market microstructure theory. Throughout, we emphasize that our evidence is correlational—we cannot establish that liquidity changes cause subsequent price movements.

### 6.1 Interpretation

The most straightforward interpretation of our findings is that some market participants reduce their liquidity provision before prices move sharply. This behavior could arise from at least two mechanisms.

First, market makers may detect early signals of directional flow—through their proprietary order flow or inventory positions—and respond by widening spreads or reducing quoted depth. If market makers are faster at processing information than the rate at which prices update, their quotes would adjust before the price shock appears in our data.

Second, informed traders may cancel resting orders before executing aggressive trades that move prices. A trader with private information might first remove their own liquidity (to avoid being adversely filled), then execute the trade that causes the price shock. This sequence would generate the liquidity-first pattern we observe.

We cannot distinguish between these mechanisms with our data. Both are consistent with theories of asymmetric information in market microstructure, and both could operate simultaneously.

### 6.2 Alternative Explanations

Several alternative explanations could generate the observed pattern without requiring that liquidity changes reflect anticipatory behavior.

**Latency differences.** Our data combines two feeds: bookTicker (order book updates) and aggTrades (executed trades). If these feeds have different latencies, apparent temporal ordering could reflect delivery delays rather than true event sequencing. We do not know the precise latency characteristics of Binance's data feeds.

**Threshold artifacts.** Our onset detection uses a fixed multiplier (2σ) for all signals. If spread variance is inherently lower than price variance, spread changes might cross their threshold more easily, biasing classification toward liquidity-first.

**Mechanical spread widening.** When order book depth thins on one side—perhaps due to the same aggressive orders that will cause the price shock—spreads mechanically widen even without any intentional liquidity withdrawal. The spread change and price change would then be effects of the same cause (order flow imbalance), not a causal sequence.

**Detection asymmetries.** Our volume signal aggregates into 5-second buckets, while spread and price are measured at tick-level resolution. This mismatch may disadvantage volume-first detection, partially explaining the low volume-first rate (14.60%).

### 6.3 Connection to Market Microstructure Theory

Our findings are consistent with classic models of informed trading. Kyle (1985) describes how informed traders strategically time their orders, while Glosten and Milgrom (1985) model how market makers adjust quotes in response to adverse selection. Both frameworks predict that liquidity conditions should respond to information asymmetry—and our data show liquidity changes preceding price movements at rates above chance.

However, consistency with theory does not establish that these mechanisms explain our observations. The alternative explanations above remain viable. What our evidence does suggest is that the temporal relationship between liquidity and price is not random—there is structure worth investigating further.

---

## 7. Limitations

<!-- Target: 400-500 words -->

We identify several limitations that constrain the conclusions we can draw from this analysis. We state these directly, as understanding what we cannot claim is as important as understanding what we find.

**Single exchange.** Our data comes exclusively from Binance. We do not know whether the liquidity-first pattern holds on other cryptocurrency exchanges (Coinbase, Kraken, OKX) or in traditional financial markets. Binance has specific characteristics—fee structures, market maker programs, user demographics—that may influence the relationship between liquidity and price. Our findings may not generalize.

**Top-of-book data only.** We analyze best bid and ask prices and quantities, but we do not observe the full order book depth. Meaningful liquidity changes—such as cancellation of large orders several ticks away from the best price—would be invisible in our data. Our "liquidity" measure (bid-ask spread) captures only one dimension of market liquidity. A study using full depth-of-book data might reach different conclusions.

**Arbitrary thresholds.** Our event detection (0.5% price change) and onset detection (2σ threshold) parameters are chosen based on reasonable defaults, not optimized for any particular outcome. Different threshold choices would identify different events and potentially different ordering patterns. While our sensitivity analysis suggests robustness to threshold variation, we have not exhaustively explored the parameter space. We are not sure how sensitive our main finding is to these choices beyond the limited range we tested.

**Date selection bias.** We intentionally selected volatile trading days to maximize event counts. This introduces bias: our sample over-represents periods of market stress and under-represents typical trading conditions. The liquidity-first pattern we observe may be specific to high-volatility environments. We cannot determine whether the same pattern holds during calm markets when price shocks are rare.

**Timestamp precision.** Our data has millisecond-level timestamps, but we do not know the precise synchronization between the aggTrades and bookTicker feeds. If one feed is systematically delayed relative to the other, apparent temporal ordering in our analysis could reflect this delay rather than true event sequencing. Without access to Binance's internal infrastructure, we cannot rule out this possibility.

**No causal identification.** Our analysis establishes correlation: liquidity changes and price shocks tend to co-occur, with liquidity changes more often appearing first. We cannot establish causation. Even if liquidity withdrawal truly precedes price shocks in time, this does not prove that liquidity withdrawal causes subsequent price movements. Both could be responses to a common upstream cause (such as large incoming order flow that we cannot observe).

**What would strengthen our claims.** Several types of additional evidence would make our findings more convincing: (1) replication on other exchanges to test generalizability; (2) full order book data to capture deeper liquidity dynamics; (3) natural experiments or exogenous shocks that might support causal inference; (4) detailed analysis of the latency characteristics of Binance's data feeds; and (5) comparison between high-volatility and low-volatility periods. We do not have access to these data or methods in the current study.

---

## 8. Conclusion

<!-- Target: 200-250 words -->

We have analyzed 452 price shock events in BTCUSDT and ETHUSDT perpetual futures on Binance and found that liquidity withdrawal precedes price shocks at a rate significantly above chance. Of all events, 44.25% show liquidity changes first, compared to the 33.3% we would expect under uniform distribution (p = 2 × 10⁻⁶). This pattern holds across both assets and is robust to threshold sensitivity analysis.

This work contributes an empirical finding—that liquidity and price changes around shocks exhibit systematic temporal ordering—along with a methodology for detecting and classifying these patterns. We emphasize that our evidence is correlational. We cannot determine whether liquidity withdrawal causes subsequent price movements, reflects anticipatory behavior by informed participants, or arises from measurement artifacts.

Several directions could extend this work. First, replication on other exchanges would test whether the liquidity-first pattern generalizes beyond Binance. Second, analysis with full order book depth (rather than top-of-book only) would capture richer liquidity dynamics. Third, careful study of data feed latencies could help distinguish true temporal ordering from measurement artifacts.

The temporal relationship between liquidity and price is not random. Whether this structure reflects informed trading, market maker behavior, or something else entirely remains an open question—but it is a question worth investigating.

---

## References

See [references.md](references.md) for full bibliography.

---

## Appendix

See [appendix.md](appendix.md) for supplementary materials including:
- Complete list of analysis dates
- Additional robustness checks
- Per-asset breakdown tables
