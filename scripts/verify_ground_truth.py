#!/usr/bin/env python3
"""
Verify ground truth for Document 03 test cases.
Check for target words in extracted documents and create labeled dataset.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd


def check_word_occurrence(text, word):
    """Check if word appears in text (case-insensitive)."""
    return word.lower() in text.lower()


def count_word_occurrences(text, word):
    """Count occurrences of word in text (case-insensitive)."""
    return len(re.findall(rf'\b{word}\b', text, re.IGNORECASE))


def verify_transitory_shift():
    """
    Test Case 1: Verify "transitory" shift in 2021.
    Expected: Appears April 2021, peaks mid-2021, removed December 2021.
    """
    print("\n" + "=" * 70)
    print("TEST CASE 1: TRANSITORY SHIFT VERIFICATION")
    print("=" * 70)

    # Get all policy statements from 2020-2022
    processed_dir = Path("data/processed")
    results = []

    # Define date range for transitory shift
    dates_to_check = [
        # 2020 baseline
        ('20200129', 'Jan 2020', 'before'),
        ('20200318', 'Mar 2020', 'before'),
        ('20200610', 'Jun 2020', 'before'),
        ('20200916', 'Sep 2020', 'before'),
        ('20201105', 'Nov 2020', 'before'),
        ('20201216', 'Dec 2020', 'before'),
        # Early 2021 pre-transitory
        ('20210127', 'Jan 2021', 'before'),
        ('20210317', 'Mar 2021', 'before'),
        # Transitory period
        ('20210428', 'Apr 2021', 'during - FIRST'),
        ('20210616', 'Jun 2021', 'during'),
        ('20210728', 'Jul 2021', 'during - minutes'),
        ('20210922', 'Sep 2021', 'during'),
        ('20211103', 'Nov 2021', 'during'),
        ('20211215', 'Dec 2021', 'after - REMOVED'),
        # Post-transitory
        ('20220126', 'Jan 2022', 'after'),
        ('20220316', 'Mar 2022', 'after'),
        ('20220504', 'May 2022', 'after'),
        ('20220615', 'Jun 2022', 'after'),
    ]

    for date, label, expected in dates_to_check:
        # Check both policy statements and minutes
        for doc_type in ['policy_statement', 'fomc_minutes']:
            filepath = processed_dir / f"{doc_type}_{date}.html.txt"

            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()

                count = count_word_occurrences(text, 'transitory')
                present = count > 0

                results.append({
                    'date': date,
                    'label': label,
                    'doc_type': doc_type,
                    'word': 'transitory',
                    'count': count,
                    'present': present,
                    'expected_status': expected,
                    'filepath': str(filepath)
                })

                status_symbol = "✓" if present else "✗"
                print(f"{label:15} ({doc_type:20}): {status_symbol} {'Present' if present else 'Absent':10} (count={count:2}) - Expected: {expected}")

    return results


def verify_accommodative_shift():
    """
    Test Case 2: Verify "accommodative" removal in September 2018.
    Expected: Present 2017-mid 2018, removed September 2018.
    """
    print("\n" + "=" * 70)
    print("TEST CASE 2: ACCOMMODATIVE REMOVAL VERIFICATION")
    print("=" * 70)

    processed_dir = Path("data/processed")
    results = []

    # Define date range for accommodative shift
    dates_to_check = [
        # 2017 baseline with accommodative
        ('20170201', 'Feb 2017', 'before'),
        ('20170614', 'Jun 2017', 'before'),
        ('20170920', 'Sep 2017', 'before'),
        ('20171213', 'Dec 2017', 'before'),
        # 2018 pre-removal
        ('20180131', 'Jan 2018', 'before'),
        ('20180321', 'Mar 2018', 'before'),
        ('20180613', 'Jun 2018', 'before'),
        # Removal
        ('20180926', 'Sep 2018', 'after - REMOVED'),
        ('20181219', 'Dec 2018', 'after'),
        # 2019 post-removal
        ('20190130', 'Jan 2019', 'after'),
        ('20190320', 'Mar 2019', 'after'),
        ('20190619', 'Jun 2019', 'after'),
        ('20190918', 'Sep 2019', 'after'),
        ('20191211', 'Dec 2019', 'after'),
    ]

    for date, label, expected in dates_to_check:
        # Check both policy statements and minutes
        for doc_type in ['policy_statement', 'fomc_minutes']:
            filepath = processed_dir / f"{doc_type}_{date}.html.txt"

            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()

                count = count_word_occurrences(text, 'accommodative')
                present = count > 0

                results.append({
                    'date': date,
                    'label': label,
                    'doc_type': doc_type,
                    'word': 'accommodative',
                    'count': count,
                    'present': present,
                    'expected_status': expected,
                    'filepath': str(filepath)
                })

                status_symbol = "✓" if present else "✗"
                print(f"{label:15} ({doc_type:20}): {status_symbol} {'Present' if present else 'Absent':10} (count={count:2}) - Expected: {expected}")

    return results


def create_labeled_dataset(transitory_results, accommodative_results):
    """
    Create labeled dataset combining both test cases.
    """
    # Combine all results
    all_results = transitory_results + accommodative_results

    # Create DataFrame
    df = pd.DataFrame(all_results)

    # Add derived columns
    df['datetime'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['year_month'] = df['datetime'].dt.to_period('M')

    # Determine shift status
    def determine_shift_status(row):
        if 'before' in row['expected_status']:
            return 'before'
        elif 'during' in row['expected_status']:
            return 'during'
        elif 'after' in row['expected_status']:
            return 'after'
        return 'unknown'

    df['shift_status'] = df.apply(determine_shift_status, axis=1)

    # Save to CSV
    output_file = "data/processed/ground_truth_labels.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Ground truth labels saved to {output_file}")

    return df


def main():
    """Main execution."""
    print("FedSpeak Document 03: Ground Truth Verification")
    print("=" * 70)

    # Run verifications
    transitory_results = verify_transitory_shift()
    accommodative_results = verify_accommodative_shift()

    # Create labeled dataset
    df = create_labeled_dataset(transitory_results, accommodative_results)

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    print("\nTransitory Shift:")
    trans_df = df[df['word'] == 'transitory']
    print(f"  Documents checked: {len(trans_df)}")
    print(f"  Documents with 'transitory': {trans_df['present'].sum()}")
    print(f"  Date range: {trans_df['date'].min()} to {trans_df['date'].max()}")

    print("\nAccommodative Shift:")
    accom_df = df[df['word'] == 'accommodative']
    print(f"  Documents checked: {len(accom_df)}")
    print(f"  Documents with 'accommodative': {accom_df['present'].sum()}")
    print(f"  Date range: {accom_df['date'].min()} to {accom_df['date'].max()}")

    print("\n✓ Ground truth verification complete!")
    print("\nNext step: Implement detection approaches using this labeled dataset")


if __name__ == "__main__":
    main()
