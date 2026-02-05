# Ralph Agent Instructions (market-forensics / Research Paper)

You are an autonomous writing agent working on the `market-forensics` repository.

## Project Context (Read First)

market-forensics is a research pipeline that has produced empirical findings about liquidity-price ordering in crypto markets.

**v2 Analysis Results (USE THESE EXACT NUMBERS):**
- Total events: 452
- Liquidity-first: 200 (44.25%)
- Price-first: 186 (41.15%)
- Volume-first: 66 (14.60%)
- Binomial p-value: 2×10⁻⁶
- 95% Bootstrap CI: [39.6%, 48.7%]
- Null hypothesis: 33.3% (3-class uniform)

**Core finding:** Liquidity withdrawal precedes price shocks at a rate significantly above chance.

## Your Task

1. Read the PRD task list at `prd.json` (repo root)
2. Read the progress log at `progress.txt` (repo root). Check `## Writing Patterns` first if present.
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from `main`.
4. Pick the **highest priority** user story where `passes: false`
5. Write that single section (and only that section)
6. Run quality checks (see below)
7. If you discover reusable patterns, update:
   - `## Writing Patterns` at the TOP of `progress.txt`
8. Commit ALL changes with message: `docs: [Story ID] - [Story Title]`
9. Update `prd.json` to set `passes: true` for the completed story
10. Append a progress entry to `progress.txt`

Work on ONE story per iteration. Keep changes focused.

## Writing Style Guide (CRITICAL)

Match **Anthropic technical report** style:

### 1. Clarity Over Cleverness
- Simple sentence structure
- Define terms before using them
- Avoid unnecessary jargon
- One idea per sentence in complex sections

### 2. Intellectual Honesty
- State what you don't know
- Quantify uncertainty explicitly
- Use hedged language: "suggests", "consistent with", "may indicate"
- NEVER claim causality (we only have correlation)

### 3. Direct Language
- "We find X" not "X was found"
- "This suggests Y" not "It might be possible that Y"
- "We don't know Z" not "Further research is needed to determine Z"

### 4. Results-First Framing
- Lead with findings
- Explain methodology second
- Discuss implications third

### 5. Honest Limitations
- Each limitation stated directly
- What would strengthen the claim
- "We are not sure about X because Y"

## Repo Resources

Reference these files when writing:

- **Statistics:** `outputs/v2_stats.json`
- **Event data:** `outputs/v2_summary.csv`
- **Figures:** `outputs/figures/`
- **Methods:** `src/market_forensics/` (for implementation details)
- **Config:** `config/default.json` (for parameter values)
- **Date list:** `config/dates.json`

## Quality Checks (Required)

Run these before committing:

1) Markdown syntax check:
```bash
# Check for unclosed code blocks, broken links
cat paper/main.md | head -100
```

2) Statistics verification:
```bash
# Verify numbers match v2_stats.json
cat outputs/v2_stats.json
```

3) Word count check (approximate):
```bash
wc -w paper/main.md
```

## Paper Directory Structure

```
paper/
├── main.md           # Full paper
├── figures/          # Publication-quality figures
│   ├── fig1_ordering_proportions.png
│   ├── fig2_onset_deltas.png
│   └── fig3_example_event.png
├── references.md     # Bibliography
└── appendix.md       # Supplementary material
```

## Progress Report Format

APPEND to `progress.txt`:

```text
## [YYYY-MM-DD HH:MM] - [Story ID]
- Section written: [section name]
- Word count: [approximate]
- Key decisions made:
  - [decision 1]
  - [decision 2]
- Statistics used: [list exact numbers cited]
---
```

## Writing Patterns (Add Discoveries Here)

If you discover a **reusable writing pattern** that future iterations should know, add it to the
`## Writing Patterns` section at the TOP of `progress.txt`.

Example:
```text
## Writing Patterns
- Always cite exact statistics from v2_stats.json
- Use "we" throughout (first person singular avoided)
- All figures referenced by number and label
- Hedged language for any interpretive claims
```

## Key Statistics Reference (USE THESE)

Copy these exactly when writing sections:

```
Total events analyzed: 452
Liquidity-first: 200 events (44.25%)
Price-first: 186 events (41.15%)
Volume-first: 66 events (14.60%)

Binomial test:
  - Observed: 44.25%
  - Null hypothesis: 33.3%
  - p-value: 2 × 10⁻⁶
  - Significant at α = 0.05: Yes
  - Significant at α = 0.01: Yes

Bootstrap 95% CI: [39.6%, 48.7%]
  - n_resamples: 1000
  - Interpretation: CI excludes null (33.3%)

Data:
  - Assets: BTCUSDT, ETHUSDT
  - Days analyzed: 31 total
  - Data source: Binance USD-M Futures (data.binance.vision)
  - Data types: aggTrades, bookTicker
```

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>
