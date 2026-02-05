# Product Requirements Document (PRD)

## Project Title
**Market Forensics v3: Research Paper on Liquidity Precedence**

## Version
v3.0

## Status
Ready for Implementation

## Owner
Zidan Kazi

---

## 1. What v2 Proved

Market Forensics v2 demonstrated that:

> When sharp price shocks occur in cryptocurrency futures, **liquidity deterioration (spread widening) precedes price movements** at a statistically significant rate.

### v2 Results Summary

| Metric | Value |
|--------|-------|
| Total events analyzed | 452 |
| Liquidity-first events | 200 (44.25%) |
| Price-first events | 186 (41.15%) |
| Volume-first events | 66 (14.60%) |
| Binomial p-value | 2×10⁻⁶ |
| 95% Bootstrap CI | [39.6%, 48.7%] |
| Null hypothesis (3-class uniform) | 33.3% |

**The 95% confidence interval excludes 33%, and the p-value is highly significant (p < 0.001).**

This is a publishable finding.

---

## 2. v3 Goal

**Transform empirical findings into a publication-quality research paper.**

v3 answers one question:

> Can we communicate this finding with the clarity, rigor, and intellectual honesty characteristic of top-tier AI safety and market microstructure research?

Target style: **Anthropic technical reports** (claude model cards, constitutional AI papers, etc.)
- Clear problem statements
- Honest limitations
- Reproducible methodology
- Visual clarity
- Meaningful contributions stated upfront

---

## 3. Practical Constraints

**Single-author academic paper** — needs to be defensible, not oversold.

### Scoping Decision
- **One core claim**: Liquidity changes precede price shocks at above-chance rates
- **No causal claims**: Correlation only, stated explicitly
- **Reproducibility focus**: All code and data sources documented
- **Honest limitations section**: As important as findings

---

## 4. Non-Goals

The paper explicitly does **not** attempt to:
- Claim causality or prediction capability
- Propose trading strategies or alpha signals
- Generalize beyond the specific assets/dates analyzed
- Make market efficiency claims
- Recommend policy interventions

---

## 5. Success Criteria

v3 succeeds if the paper:

| Criterion | Target |
|-----------|--------|
| Length | 8-15 pages (excluding appendix) |
| Figures | 3-5 publication-quality visualizations |
| Abstract | <250 words, states contribution clearly |
| Limitations | Comprehensive and honest |
| Reproducibility | Full methodology documented |
| Style | Matches Anthropic technical report quality |

---

## 6. Paper Structure

### Target Outline

1. **Abstract** (~200 words)
   - Problem: Price shocks cause losses; understanding their genesis matters
   - Method: Event detection + onset timing across 452 events
   - Result: Liquidity precedes price 44% vs 33% null (p < 10⁻⁵)
   - Implication: Suggests informed traders' footprint in order book

2. **Introduction** (~1 page)
   - Market microstructure during stress events
   - Why temporal ordering matters
   - Paper contributions (3 bullet points max)

3. **Related Work** (~0.5 page)
   - Prior work on liquidity-volatility relationships
   - Event study methodology in finance
   - Crypto market microstructure research

4. **Data** (~1 page)
   - Source: Binance USD-M Futures
   - Assets: BTCUSDT, ETHUSDT
   - Date selection: High-volatility days (ETF approval, ATH runs)
   - Data volume: 31 days, ~60GB canonical data

5. **Methods** (~2 pages)
   - Event detection algorithm
   - Window extraction
   - Onset detection (k×std threshold crossing)
   - Classification scheme
   - Statistical tests (binomial, bootstrap)

6. **Results** (~2 pages)
   - Main finding: 44.25% liquidity-first
   - Statistical significance
   - Asset comparison (BTC vs ETH)
   - Threshold sensitivity analysis

7. **Discussion** (~1 page)
   - Interpretation: What does liquidity-first ordering suggest?
   - Alternative explanations
   - Connection to market maker behavior

8. **Limitations** (~1 page)
   - Single exchange
   - Top-of-book only
   - Threshold sensitivity
   - Date selection bias
   - Timestamp precision
   - No causal identification

9. **Conclusion** (~0.5 page)
   - Summary of contribution
   - Future work directions

10. **Appendix**
    - Full date list
    - Additional figures
    - Sensitivity tables
    - Code availability statement

---

## 7. Functional Requirements

### FR-1: Create paper skeleton
- Create `paper/main.md` with full section structure
- Include placeholder sections with target word counts
- Add figure placeholders with captions

### FR-2: Write Abstract
- Draft compelling 200-word abstract
- State problem, method, result, implication
- Follow Anthropic style (clear, direct, no hype)

### FR-3: Write Introduction
- Motivate the problem (price shocks, market fragility)
- State the research question clearly
- List contributions (max 3)
- End with paper roadmap

### FR-4: Write Data Section
- Document data sources completely
- Explain date selection rationale
- Include data summary table
- Reference canonical format

### FR-5: Write Methods Section
- Event detection algorithm (pseudo-code or equations)
- Onset detection formalization
- Classification scheme
- Statistical test specifications
- Figure: example event window

### FR-6: Write Results Section
- Present main findings with statistics
- Include key visualizations:
  - Ordering proportions bar chart
  - Onset delta histogram
  - BTC vs ETH comparison
- Threshold sensitivity analysis

### FR-7: Write Discussion Section
- Interpret findings carefully
- Address alternative explanations
- Connect to market microstructure theory
- Avoid overclaiming

### FR-8: Write Limitations Section
- Comprehensive and honest
- Address each limitation directly
- Explain what would strengthen claims
- Match Anthropic's "we're not sure about X" style

### FR-9: Write Conclusion
- Restate contribution
- Future work directions
- Closing thought

### FR-10: Write Related Work
- Market microstructure literature
- Liquidity-volatility relationships
- Crypto market research
- Event study methodology

### FR-11: Create publication-quality figures
- Regenerate figures with publication styling
- Add proper axis labels, legends, captions
- Ensure figures are self-contained
- Export as high-res PNGs

### FR-12: Final editing pass
- Check consistency throughout
- Verify all statistics match outputs
- Proofread and polish
- Add references placeholders

---

## 8. Deliverables

| Deliverable | Description |
|-------------|-------------|
| `paper/main.md` | Full paper in markdown |
| `paper/figures/` | Publication-quality figures |
| `paper/references.md` | Bibliography/references |
| `paper/appendix.md` | Supplementary materials |

---

## 9. Style Guide

### Anthropic-Style Writing Principles

1. **Clarity over cleverness**
   - Simple sentence structure
   - Define terms before using them
   - Avoid jargon unless necessary

2. **Intellectual honesty**
   - State what you don't know
   - Quantify uncertainty
   - Avoid overclaiming

3. **Structured presentation**
   - Use numbered lists for contributions
   - Use tables for comparisons
   - Use figures for visual concepts

4. **Direct language**
   - "We find X" not "X was found"
   - "This suggests Y" not "It might be possible that Y"
   - "We don't know Z" not "Further research is needed to determine Z"

5. **Results-first framing**
   - Lead with findings
   - Explain methodology second
   - Discuss implications third

---

## 10. Guiding Principle

> *Understate the contribution; let the data speak.*

A paper that honestly reports a small, well-supported finding is more valuable than one that overclaims a larger effect with weaker evidence.
