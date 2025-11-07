"""
Diagnostic Analysis - Why Are G-test and JSD Failing?
=======================================================

Examines the actual data for the critical transitory December 2021 case.
"""

import os
import re
import math


def count_term_occurrences(text: str, term: str) -> int:
    """Count occurrences of a term (case-insensitive, whole-word)."""
    text_lower = text.lower()
    term_lower = term.lower()
    pattern = r'\b' + re.escape(term_lower) + r'\b'
    matches = re.findall(pattern, text_lower)
    return len(matches)


def load_statement(date: str, data_dir: str) -> str:
    """Load a single policy statement."""
    # Try different file patterns
    patterns = [
        f"policy_statement_{date}.txt",
        f"policy_statement_{date}.html.txt"
    ]

    for pattern in patterns:
        filepath = os.path.join(data_dir, pattern)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

    raise FileNotFoundError(f"Could not find statement for date {date}")


def calculate_g_statistic(a, b, c, d):
    """Calculate G-statistic."""
    if a + b == 0 or c + d == 0:
        return 0.0

    N = a + b + c + d
    E_a = (a + b) * (a + c) / N
    E_b = (a + b) * (b + d) / N
    E_c = (c + d) * (a + c) / N
    E_d = (c + d) * (b + d) / N

    G = 0.0
    if a > 0 and E_a > 0:
        G += 2 * a * math.log(a / E_a)
    if b > 0 and E_b > 0:
        G += 2 * b * math.log(b / E_b)
    if c > 0 and E_c > 0:
        G += 2 * c * math.log(c / E_c)
    if d > 0 and E_d > 0:
        G += 2 * d * math.log(d / E_d)

    return G


def diagnose_transitory_december_2021(data_dir: str):
    """Detailed analysis of transitory removal in December 2021."""

    print("="*80)
    print("DIAGNOSTIC ANALYSIS: Transitory Removal December 2021")
    print("="*80)

    # Load relevant statements
    nov_2021 = load_statement('20211103', data_dir)
    dec_2021 = load_statement('20211215', data_dir)

    # Count 'transitory' in each
    nov_count = count_term_occurrences(nov_2021, 'transitory')
    dec_count = count_term_occurrences(dec_2021, 'transitory')

    nov_words = len(nov_2021.split())
    dec_words = len(dec_2021.split())

    print(f"\nNovember 2021 Statement:")
    print(f"  Date: 20211103")
    print(f"  'transitory' count: {nov_count}")
    print(f"  Total words: {nov_words}")
    print(f"  Rate: {nov_count/nov_words:.6f}")

    print(f"\nDecember 2021 Statement:")
    print(f"  Date: 20211215")
    print(f"  'transitory' count: {dec_count}")
    print(f"  Total words: {dec_words}")
    print(f"  Rate: {dec_count/dec_words:.6f}")

    print(f"\nChange: {nov_count} -> {dec_count} (REMOVAL)")

    # Load statements from 12-month lookback for baseline
    lookback_dates = [
        '20201216', '20210127', '20210317', '20210428',
        '20210616', '20210728', '20210922', '20211103'
    ]

    baseline_count = 0
    baseline_words = 0

    print(f"\nBaseline (previous 8 statements):")
    for date in lookback_dates:
        try:
            text = load_statement(date, data_dir)
            count = count_term_occurrences(text, 'transitory')
            words = len(text.split())
            baseline_count += count
            baseline_words += words
            if count > 0:
                print(f"  {date}: count={count}, words={words}")
        except FileNotFoundError:
            print(f"  {date}: NOT FOUND")

    print(f"\nBaseline Totals:")
    print(f"  Total 'transitory': {baseline_count}")
    print(f"  Total words: {baseline_words}")
    print(f"  Baseline rate: {baseline_count/baseline_words:.6f}")

    # G-test calculation
    print(f"\n{'='*80}")
    print("G-TEST CALCULATION")
    print(f"{'='*80}")

    # Contingency table
    a = dec_count  # transitory in Dec 2021
    b = dec_words - dec_count  # other words in Dec 2021
    c = baseline_count  # transitory in baseline
    d = baseline_words - baseline_count  # other words in baseline

    print(f"\nContingency Table:")
    print(f"                 'transitory'    Other      Total")
    print(f"  Dec 2021 (target)    {a:5d}      {b:6d}    {a+b:6d}")
    print(f"  Baseline             {c:5d}      {d:6d}    {c+d:6d}")
    print(f"  Total                {a+c:5d}      {b+d:6d}    {a+b+c+d:6d}")

    G = calculate_g_statistic(a, b, c, d)

    print(f"\nG-statistic: {G:.4f}")
    print(f"Threshold (p<0.001): 10.83")
    print(f"Threshold (p<0.05): 3.84")
    print(f"Threshold (p<0.01): 6.63")

    if G >= 3.84:
        print(f"Result: SIGNIFICANT (p < 0.05)")
    else:
        print(f"Result: NOT SIGNIFICANT")

    # Problem diagnosis
    print(f"\n{'='*80}")
    print("PROBLEM DIAGNOSIS")
    print(f"{'='*80}")

    print(f"\nThe issue: G-test is designed for EMERGENCE detection.")
    print(f"For REMOVAL, we need to compare:")
    print(f"  - November 2021 (with 'transitory') vs baseline")
    print(f"  - December 2021 (without 'transitory') vs baseline")

    # Recalculate for November (should be significant)
    a_nov = nov_count
    b_nov = nov_words - nov_count
    c_nov = baseline_count - nov_count  # Exclude Nov from baseline
    d_nov = baseline_words - nov_words - (baseline_count - nov_count)

    print(f"\nG-test for November 2021 (emergence context):")
    G_nov = calculate_g_statistic(a_nov, b_nov, c_nov, d_nov)
    print(f"  G-statistic: {G_nov:.4f}")

    # The real test: Compare consecutive documents
    print(f"\n{'='*80}")
    print("ALTERNATIVE: COMPARE CONSECUTIVE DOCUMENTS")
    print(f"{'='*80}")

    a_consec = dec_count
    b_consec = dec_words - dec_count
    c_consec = nov_count
    d_consec = nov_words - nov_count

    print(f"\nContingency Table (Dec vs Nov):")
    print(f"                 'transitory'    Other      Total")
    print(f"  Dec 2021            {a_consec:5d}      {b_consec:6d}    {a_consec+b_consec:6d}")
    print(f"  Nov 2021            {c_consec:5d}      {d_consec:6d}    {c_consec+d_consec:6d}")

    G_consec = calculate_g_statistic(a_consec, b_consec, c_consec, d_consec)
    print(f"\nG-statistic (consecutive): {G_consec:.4f}")

    if G_consec >= 3.84:
        print(f"Result: SIGNIFICANT (p < 0.05)")
    else:
        print(f"Result: NOT SIGNIFICANT (need more data)")

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")
    print(f"\nThe statistical challenge:")
    print(f"  - Single term removal from one document = very sparse data")
    print(f"  - G-test needs sufficient counts for statistical power")
    print(f"  - With only 1 occurrence removed, hard to reach significance")
    print(f"\nThis is why simple RULE-BASED detection (count drops to 0)")
    print(f"may be more appropriate for this use case than statistical tests.")


if __name__ == "__main__":
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    diagnose_transitory_december_2021(DATA_DIR)
