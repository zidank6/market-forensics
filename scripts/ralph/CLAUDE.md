# Ralph Agent Instructions (market-forensics / Python)

You are an autonomous coding agent working on the `market-forensics` repository.

## Project Context (Read First)

market-forensics is a research/forensics pipeline for crypto market microstructure stress events.

Primary goal:
- Reconstruct short event windows around sudden moves and determine the sequence of changes:
  liquidity (spread / top-of-book), trading behavior (trades/volume), and price (mid/last).

Non-goals (do NOT implement):
- No trading strategies, alpha signals, or predictions
- No real-time streaming in v1
- No dashboards or UI in v1
- No simulations / synthetic market data generation
- No news/sentiment ingestion in v1

Guiding principle:
- Prefer boring-but-real over clever-but-fragile. Fail loudly on bad inputs.

## Your Task

1. Read the PRD task list at `./prd.json` (repo root)
2. Read the progress log at `./progress.txt` (repo root). Check `## Codebase Patterns` first if present.
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from `main`.
4. Pick the **highest priority** user story where `passes: false`
5. Implement that single user story (and only that story)
6. Run the required quality checks (see below)
7. If you discover reusable patterns/gotchas, update:
   - `## Codebase Patterns` at the TOP of `progress.txt` (consolidated, reusable only)
   - and/or nearby `CLAUDE.md` files if there is genuinely reusable module-specific guidance
8. If checks pass, commit ALL changes with message: `feat: [Story ID] - [Story Title]`
9. Update `prd.json` to set `passes: true` for the completed story
10. Append a progress entry to `progress.txt`

Work on ONE story per iteration. Keep changes minimal and focused.

## Repo Conventions

- Python-only v1. Keep it simple, reproducible, and config-driven.
- Prefer small modules with clear names:
  - `src/market_forensics/data/`
  - `src/market_forensics/events/`
  - `src/market_forensics/windows/`
  - `src/market_forensics/metrics/`
  - `src/market_forensics/plots/`
- Deterministic outputs:
  - Same input + same config must produce the same files in `outputs/`.
- Config-driven:
  - thresholds/window sizes live in a config file (JSON/YAML), not hard-coded.
- Fail loudly:
  - validate inputs; raise exceptions with clear error messages.
- Avoid “research theater”:
  - no big theory claims in code/docs; focus on measurable definitions.

## Quality Checks (Required)

Run these before committing (must pass):

1) Python syntax / import sanity:
```bash
python -m compileall .
```

2) If pytest exists (only run if `pytest` is installed and tests directory exists):
```bash
python -m pytest -q
```

3) If ruff exists (only run if configured):
```bash
ruff check .
```

If any of these tools are not installed/configured yet, do NOT add heavy setup unless the current story requires it.
However, **the compileall check is mandatory**.

## Progress Report Format

APPEND to `progress.txt` (never replace, always append):

```text
## [YYYY-MM-DD HH:MM] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (general + reusable)
  - Gotchas encountered (general + reusable)
  - Useful context (where things live, how to run)
---
```

## Consolidate Patterns

If you discover a **reusable pattern** that future iterations should know, add it to the
`## Codebase Patterns` section at the TOP of `progress.txt` (create it if it doesn't exist).

Example:

```text
## Codebase Patterns
- Keep pipeline outputs deterministic under outputs/
- Config values must be in config/*.json (no hardcoded thresholds)
- Data loaders validate required columns and fail loudly
```

Only add patterns that are general and reusable (not story-specific).

## Update CLAUDE.md Files

Before committing, check if any edited directories have learnings worth preserving in a nearby CLAUDE.md.

Add only genuinely reusable knowledge:
- conventions, gotchas, cross-file dependencies, testing approaches, env requirements

Do NOT add:
- story-specific implementation details
- temporary debugging notes
- things already captured in progress.txt

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>
