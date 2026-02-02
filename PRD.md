# Product Requirements Document (PRD)

## Project Title
**Crypto Market Microstructure Event Analysis System**

## Version
v1.0 (Concept Lock)

## Status
Definition / Research Design Phase

## Owner
Zidan Kazi

---

## 1. Problem Statement

Crypto markets frequently experience sudden, sharp price movements. These events are typically discussed in terms of *price* and *volatility*, but price alone does not explain **what actually broke first** inside the market.

Existing analysis often answers *what happened*, not *how it unfolded mechanically*. Two identical price crashes can be driven by very different underlying mechanisms:
- liquidity withdrawal
- aggressive trading
- reflexive feedback loops

Without reconstructing the **temporal sequence** of internal market changes, it is impossible to distinguish between these failure modes.

This project aims to systematically reconstruct and analyze the **order in which market components change** during short-term stress events in crypto markets.

---

## 2. Goal

Build a **reproducible, defensible research system** that answers the question:

> *When crypto markets move suddenly, what changes first: liquidity, trading behavior, or price?*

The system will analyze real historical data to identify stress events and reconstruct their microstructure evolution.

The goal is **understanding**, not prediction or trading performance.

---

## 3. Non-Goals

The system explicitly does **not** attempt to:
- predict future prices
- generate trading signals or strategies
- optimize execution or profitability
- simulate agents or synthetic markets
- explain macroeconomic or news causality

This is an **observational and forensic** analysis tool.

---

## 4. Scope

### In Scope
- One centralized exchange
- Real historical data
- Short event windows (seconds to minutes)
- BTC, ETH, SOL as primary assets
- Event-based analysis (not continuous forecasting)

### Out of Scope (v1)
- Cross-exchange arbitrage
- Full L2/L3 order book reconstruction
- News or sentiment ingestion
- Real-time streaming
- User-facing dashboards

---

## 5. Core Concept

Markets are composed of a small number of mechanical components:
- **Liquidity** (standing orders / spread)
- **Trading behavior** (trade frequency, size, aggressiveness)
- **Price** (last executed trade)

During stress events, these components do not necessarily change simultaneously.

This system identifies **which component reacts first**, and how the others follow.

---

## 6. Key Definitions

### Stress Event
A short time interval where price changes rapidly relative to recent history (e.g. X% within Y seconds).

### Event Window
A fixed time slice surrounding a stress event:
- Pre-event window (e.g. 1–5 minutes)
- Post-event window (e.g. 1–5 minutes)

### Reaction Sequence
The observed ordering in time of:
1. Liquidity changes
2. Trading behavior changes
3. Price movement

---

## 7. Functional Requirements

### FR-1: Data Ingestion
- Load historical trade data
- Load best bid / best ask (top-of-book) data
- Support BTC, ETH, SOL for a single exchange

### FR-2: Event Detection
- Scan historical data to identify sudden price moves
- Parameterized thresholds (configurable)
- Produce a list of event timestamps

### FR-3: Window Extraction
- Extract standardized pre- and post-event windows
- Ensure consistent time alignment
- Handle overlapping events deterministically

### FR-4: Metric Computation
Compute simple, interpretable metrics:
- Trade count
- Trade volume
- Average trade size
- Bid–ask spread
- Price volatility

### FR-5: Temporal Ordering Analysis
- Determine which metrics change first relative to event onset
- Compare timing across assets
- Aggregate patterns across many events

### FR-6: Output Artifacts
- Reproducible plots
- Tables summarizing reaction sequences
- Saved intermediate datasets

---

## 8. Non-Functional Requirements

### Reproducibility
- Deterministic runs
- Config-driven experiment definitions
- Clear data provenance

### Interpretability
- No black-box models
- Metrics must have clear physical meaning

### Transparency
- Explicit assumptions
- Documented limitations

---

## 9. Data Strategy

### Initial Data Types
- Trades (timestamp, price, size)
- Best bid / best ask (timestamp, prices)

### Constraints
- Prefer free or publicly accessible datasets
- Accept reduced depth in exchange for broader time coverage

---

## 10. Validation Strategy

Results will be validated through:
- Sensitivity analysis (varying thresholds, window sizes)
- Cross-asset comparison
- Manual inspection of representative events

---

## 11. Success Criteria

The project is successful if:
- A consistent methodology is implemented
- Clear reaction sequences are observed
- Results can be explained in plain language
- A serious technical reader can reproduce and critique findings

---

## 12. Final Deliverables

At least one of the following:
- A research-style writeup (PDF or markdown)
- A public reproducible repository
- A structured technical report with figures and tables

---

## 13. Guiding Principle

> *This system exists to see clearly, not to impress.*

If a result is boring but real, it is preferred over a clever but fragile claim.
