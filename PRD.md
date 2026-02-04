# Product Requirements Document (PRD)

## Project Title
**Market Forensics v2: Validating the Liquidity-First Hypothesis**

## Version
v2.0

## Status
Ready for Implementation

## Owner
Zidan Kazi

---

## 1. What v1 Proved

Market Forensics v1 demonstrated that:

> When sharp price shocks occur in BTCUSDT futures, **liquidity deterioration precedes price movements** in approximately 60% of detected events.

This finding held across 3 trading days and was robust to threshold variations (0.4%–0.6%).

**But v1 is underpowered.** 15 events over 3 days is a proof-of-concept, not a defensible empirical claim.

---

## 2. v2 Goal

**Turn "this looks real" into "this is hard to dismiss."**

v2 answers one question:

> Is the liquidity-first ordering **systematic and robust** across a larger sample, multiple assets, and different market regimes?

---

## 3. Practical Constraints

**Laptop-based development** — cannot store 100GB+ of raw data.

### Scoping Decision
- **10-15 trading days** per asset (not 60+)
- **2 assets**: BTCUSDT + ETHUSDT
- **Target: 50-100 events** (enough for statistical tests)
- Canonicalized data only (~1GB/day max)

This is an honest scope that balances rigor with practicality.

---

## 4. Non-Goals

The system explicitly does **not** attempt to:
- Predict future prices or generate alpha
- Claim causality (temporal ordering ≠ causation)
- Add ML models or fancy metrics
- Store raw tick data long-term

---

## 5. Success Criteria

v2 succeeds if:

| Criterion | Target |
|-----------|--------|
| Trading days analyzed | 10-15 per asset |
| Non-overlapping events | 50-100 total |
| Assets | BTCUSDT + ETHUSDT |
| Statistical significance | p < 0.05 on liquidity-first proportion |
| Storage footprint | < 25GB total |

---

## 6. Scope

### In Scope
- 10-15 trading days of BTCUSDT futures (canonicalized)
- 10-15 trading days of ETHUSDT futures (canonicalized)
- Formal statistical tests (binomial, bootstrap CI)
- Event-study visualizations
- Sensitivity analysis on thresholds
- Clean summary tables for research writeup

### Out of Scope (v2)
- Full order book depth
- 60+ days of data
- Causal inference methods
- Real-time streaming

---

## 7. Data Strategy

### Data Source
- **Exchange**: Binance USD-M Futures
- **Assets**: BTCUSDT, ETHUSDT
- **Data Types**: 
  - `aggTrades` → canonical `trades.csv`
  - `bookTicker` → canonical `tob.csv`
- **Source**: https://data.binance.vision

### Target Volume
| Asset | Days | Storage Est. | Expected Events |
|-------|------|--------------|-----------------|
| BTCUSDT | 10-15 | ~8-12GB | 20-50 |
| ETHUSDT | 10-15 | ~8-12GB | 20-50 |
| **Total** | — | **~20GB** | **50-100** |

### Date Selection Strategy
Pick dates with **known volatility** to maximize events per day:
- Major news days (ETF announcements, Fed meetings)
- High-vol weeks (late 2024, early 2025)
- Avoid weekends (lower activity)

---

## 8. Functional Requirements

### FR-1: Canonicalize 10-15 days per asset
- Run canonicalize_binance_um_day.py for selected dates
- Store in data/binance/futures_um/{ASSET}/canonical/{date}/
- Create config/dates.json manifest

### FR-2: Multi-asset pipeline runner
- Run existing pipeline on both assets
- Output to outputs/v2/{asset}/{date}/
- No modifications to src/market_forensics/

### FR-3: Aggregate results
- Collect all event-level ordering results
- Produce outputs/v2_summary.csv

### FR-4: Statistical tests
- Binomial test on liquidity-first proportion
- Bootstrap 95% CI
- Per-asset and pooled results

### FR-5: Visualizations
- Onset delta histogram
- Ordering proportions bar chart
- Event-study mean paths (if time permits)

### FR-6: Research summary
- report/v2_findings.md with methodology and results

---

## 9. Deliverables

| Deliverable | Description |
|-------------|-------------|
| `config/dates.json` | Manifest of dates to process |
| `outputs/v2_summary.csv` | Aggregated event-level results |
| `outputs/v2_stats.json` | Statistical test outputs |
| `outputs/figures/` | Key visualizations |
| `report/v2_findings.md` | Structured writeup |

---

## 10. Guiding Principle

> *Honest scoping beats ambitious failure.*

50 well-analyzed events across 2 assets is more valuable than a half-finished 300-event analysis that never runs.
