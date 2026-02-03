#!/usr/bin/env python3
"""Statistical tests for liquidity-first proportion in v2 results.

Runs binomial test and bootstrap confidence interval analysis on
the proportion of liquidity-first events vs null hypothesis of 33%.
"""

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).parent.absolute()
REPO_ROOT = HERE.parent


def load_summary_csv(summary_path: Path) -> List[dict]:
    """Load v2_summary.csv.

    Args:
        summary_path: Path to v2_summary.csv.

    Returns:
        List of row dictionaries.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    rows = []
    with open(summary_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def count_classifications(rows: List[dict]) -> dict:
    """Count events by classification.

    Args:
        rows: List of event rows from summary CSV.

    Returns:
        Dictionary with classification counts.
    """
    counts = {}
    for row in rows:
        cls = row.get("classification", "unknown")
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def binomial_pmf(n: int, k: int, p: float) -> float:
    """Compute binomial probability mass function P(X = k).

    Args:
        n: Number of trials.
        k: Number of successes.
        p: Probability of success.

    Returns:
        Probability P(X = k).
    """
    if k < 0 or k > n:
        return 0.0

    # Use log to avoid overflow for large n
    log_coeff = (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    )
    if p == 0:
        return 1.0 if k == 0 else 0.0
    if p == 1:
        return 1.0 if k == n else 0.0

    log_prob = log_coeff + k * math.log(p) + (n - k) * math.log(1 - p)
    return math.exp(log_prob)


def binomial_test_two_sided(k: int, n: int, p_null: float) -> float:
    """Two-sided binomial test.

    Tests whether observed proportion differs from null hypothesis.

    Args:
        k: Number of successes (liquidity-first events).
        n: Total number of trials (all events).
        p_null: Null hypothesis proportion (0.333... for 3-class uniform).

    Returns:
        Two-sided p-value.
    """
    if n == 0:
        return 1.0

    # Observed probability under null
    observed_prob = binomial_pmf(n, k, p_null)

    # Sum probabilities of all outcomes at least as extreme
    p_value = 0.0
    for i in range(n + 1):
        prob_i = binomial_pmf(n, i, p_null)
        if prob_i <= observed_prob + 1e-10:  # Small tolerance for floating point
            p_value += prob_i

    return min(p_value, 1.0)


def bootstrap_ci(
    successes: int,
    total: int,
    n_resamples: int = 1000,
    ci_level: float = 0.95,
    seed: Optional[int] = None,
) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for proportion.

    Uses percentile method.

    Args:
        successes: Number of successes.
        total: Total number of trials.
        n_resamples: Number of bootstrap resamples.
        ci_level: Confidence level (e.g., 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if total == 0:
        return (0.0, 1.0)

    if seed is not None:
        random.seed(seed)

    # Create binary data: 1 = success (liquidity-first), 0 = other
    data = [1] * successes + [0] * (total - successes)

    proportions = []
    for _ in range(n_resamples):
        # Resample with replacement
        resample = random.choices(data, k=total)
        prop = sum(resample) / total
        proportions.append(prop)

    # Sort for percentile method
    proportions.sort()

    alpha = 1 - ci_level
    lower_idx = int((alpha / 2) * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples) - 1

    lower_idx = max(0, lower_idx)
    upper_idx = min(n_resamples - 1, upper_idx)

    return (proportions[lower_idx], proportions[upper_idx])


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run statistical tests on v2 liquidity-first proportion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default summary file
  python scripts/run_statistics.py

  # Custom input/output
  python scripts/run_statistics.py --input outputs/v2_summary.csv --output outputs/v2_stats.json
        """,
    )
    parser.add_argument(
        "--input", "-i",
        default="outputs/v2_summary.csv",
        help="Path to v2_summary.csv (default: outputs/v2_summary.csv)",
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/v2_stats.json",
        help="Path to output stats JSON (default: outputs/v2_stats.json)",
    )
    parser.add_argument(
        "--null-proportion", "-p",
        type=float,
        default=1/3,
        help="Null hypothesis proportion (default: 0.333... for 3-class uniform)",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap resamples (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for bootstrap (default: 42)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress detailed output",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    # Resolve paths
    input_path = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = REPO_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)

    # Load data
    try:
        rows = load_summary_csv(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("  Run scripts/aggregate_v2_results.py first.", file=sys.stderr)
        return 1

    if not rows:
        print("ERROR: Summary file is empty", file=sys.stderr)
        return 1

    # Count classifications
    counts = count_classifications(rows)
    total = len(rows)
    liquidity_first = counts.get("liquidity-first", 0)
    observed_proportion = liquidity_first / total if total > 0 else 0

    # Run binomial test
    p_null = args.null_proportion
    p_value = binomial_test_two_sided(liquidity_first, total, p_null)

    # Run bootstrap CI
    ci_lower, ci_upper = bootstrap_ci(
        liquidity_first, total,
        n_resamples=args.n_bootstrap,
        ci_level=0.95,
        seed=args.seed,
    )

    # Prepare output
    results = {
        "total_events": total,
        "counts": counts,
        "liquidity_first_count": liquidity_first,
        "observed_proportion": round(observed_proportion, 4),
        "null_proportion": round(p_null, 4),
        "binomial_test": {
            "p_value": round(p_value, 6),
            "significant_at_05": p_value < 0.05,
            "significant_at_01": p_value < 0.01,
        },
        "bootstrap_ci": {
            "confidence_level": 0.95,
            "n_resamples": args.n_bootstrap,
            "lower": round(ci_lower, 4),
            "upper": round(ci_upper, 4),
            "seed": args.seed,
        },
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print human-readable summary
    print("=" * 60)
    print("Market Forensics v2 - Statistical Analysis")
    print("=" * 60)
    print()
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print()
    print("Event Counts:")
    print("-" * 40)
    print(f"  Total events:        {total}")
    for cls, count in sorted(counts.items()):
        pct = 100.0 * count / total if total > 0 else 0
        print(f"  {cls:20s} {count:5d} ({pct:5.1f}%)")
    print()
    print("Liquidity-First Proportion:")
    print("-" * 40)
    print(f"  Observed:            {observed_proportion:.1%} ({liquidity_first}/{total})")
    print(f"  Null (3-class):      {p_null:.1%}")
    print()
    print("Binomial Test (two-sided):")
    print("-" * 40)
    print(f"  H0: proportion = {p_null:.1%}")
    print(f"  p-value:             {p_value:.4f}")
    if p_value < 0.001:
        print(f"  Significance:        *** (p < 0.001)")
    elif p_value < 0.01:
        print(f"  Significance:        ** (p < 0.01)")
    elif p_value < 0.05:
        print(f"  Significance:        * (p < 0.05)")
    else:
        print(f"  Significance:        not significant (p >= 0.05)")
    print()
    print("Bootstrap 95% Confidence Interval:")
    print("-" * 40)
    print(f"  Method:              Percentile ({args.n_bootstrap} resamples)")
    print(f"  95% CI:              [{ci_lower:.1%}, {ci_upper:.1%}]")
    print()

    # Interpretation
    print("Interpretation:")
    print("-" * 40)
    if p_value < 0.05 and observed_proportion > p_null:
        print(f"  The liquidity-first proportion ({observed_proportion:.1%}) is")
        print(f"  SIGNIFICANTLY HIGHER than the 3-class null ({p_null:.1%}).")
        if ci_lower > p_null:
            print(f"  The 95% CI [{ci_lower:.1%}, {ci_upper:.1%}] excludes {p_null:.1%}.")
    elif p_value < 0.05 and observed_proportion < p_null:
        print(f"  The liquidity-first proportion ({observed_proportion:.1%}) is")
        print(f"  SIGNIFICANTLY LOWER than the 3-class null ({p_null:.1%}).")
    else:
        print(f"  No significant difference from 3-class null detected.")
        print(f"  Cannot reject that liquidity-first occurs at chance rate.")
    print()
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
