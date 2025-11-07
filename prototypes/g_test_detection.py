"""
G-test / Log-Likelihood Ratio for FedSpeak Shift Detection
============================================================

Implements the G-test (log-likelihood ratio test) for detecting significant
changes in term frequency between a target document and baseline corpus.

Theory:
- More powerful than Chi-squared test for sparse data
- Particularly effective for detecting new/emerging terms
- Tests null hypothesis: term frequency in target = frequency in baseline

Reference: Dunning, T. (1993). "Accurate Methods for the Statistics of Surprise and Coincidence"
"""

import os
import re
import json
import math
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import csv


class GTestDetector:
    """
    G-test based shift detection for term frequency changes.

    Detects both emergences and removals by comparing target document
    frequencies against a historical baseline corpus.
    """

    def __init__(self, significance_threshold: float = 10.83):
        """
        Initialize G-test detector.

        Args:
            significance_threshold: G-statistic threshold for significance
                                   (10.83 corresponds to p < 0.001)
        """
        self.significance_threshold = significance_threshold

    def calculate_g_statistic(self, a: int, b: int, c: int, d: int) -> float:
        """
        Calculate G-statistic (log-likelihood ratio).

        Contingency table:
                    Term    Not-term    Total
        Target       a         b        a+b
        Baseline     c         d        c+d
        Total       a+c       b+d      a+b+c+d

        Args:
            a: Term count in target document
            b: Other words in target document
            c: Term count in baseline corpus
            d: Other words in baseline corpus

        Returns:
            G-statistic value
        """
        # Avoid division by zero
        if a + b == 0 or c + d == 0:
            return 0.0

        # Calculate expected values
        N = a + b + c + d
        E_a = (a + b) * (a + c) / N
        E_b = (a + b) * (b + d) / N
        E_c = (c + d) * (a + c) / N
        E_d = (c + d) * (b + d) / N

        # Calculate G-statistic (2 * sum of observed * log(observed/expected))
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

    def detect_shift(self, term: str, target_date: str,
                    target_count: int, target_length: int,
                    baseline_count: int, baseline_length: int,
                    prev_count: int = 0) -> Dict:
        """
        Detect if a term shows significant shift in target document.

        Args:
            term: Term being analyzed
            target_date: Date of target document
            target_count: Term occurrences in target
            target_length: Total words in target
            baseline_count: Term occurrences in baseline corpus
            baseline_length: Total words in baseline corpus
            prev_count: Term count in previous document (for shift type)

        Returns:
            Detection result dictionary
        """
        # Construct contingency table
        a = target_count
        b = target_length - target_count
        c = baseline_count
        d = baseline_length - baseline_count

        # Calculate G-statistic
        G = self.calculate_g_statistic(a, b, c, d)

        # Determine if significant
        is_significant = G >= self.significance_threshold

        # Calculate frequency rates
        target_rate = a / target_length if target_length > 0 else 0
        baseline_rate = c / baseline_length if baseline_length > 0 else 0

        # Determine shift type
        shift_type = None
        if is_significant:
            if target_count > 0 and prev_count == 0:
                shift_type = 'emergence'
            elif target_count == 0 and prev_count > 0:
                shift_type = 'removal'
            elif target_rate > baseline_rate * 1.5:  # 50% increase threshold
                shift_type = 'increase'
            elif target_rate < baseline_rate * 0.5:  # 50% decrease threshold
                shift_type = 'decrease'

        result = {
            'term': term,
            'date': target_date,
            'G_statistic': round(G, 4),
            'threshold': self.significance_threshold,
            'is_significant': is_significant,
            'shift_type': shift_type,
            'target_count': target_count,
            'target_rate': round(target_rate, 6),
            'baseline_rate': round(baseline_rate, 6),
            'rate_ratio': round(target_rate / baseline_rate, 2) if baseline_rate > 0 else float('inf'),
            'prev_count': prev_count
        }

        return result


def load_corpus_data(data_dir: str) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
    """Load all policy statements from corpus."""
    texts = {}
    doc_lengths = {}

    for filename in os.listdir(data_dir):
        if filename.startswith('policy_statement_') and filename.endswith('.txt'):
            match = re.search(r'policy_statement_(\d{8})', filename)
            if match:
                date_str = match.group(1)
                filepath = os.path.join(data_dir, filename)

                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    texts[date_str] = text
                    words = text.lower().split()
                    doc_lengths[date_str] = len(words)

    dates = sorted(texts.keys())
    return dates, texts, doc_lengths


def count_term_occurrences(text: str, term: str) -> int:
    """Count occurrences of a term (case-insensitive, whole-word)."""
    text_lower = text.lower()
    term_lower = term.lower()
    pattern = r'\b' + re.escape(term_lower) + r'\b'
    matches = re.findall(pattern, text_lower)
    return len(matches)


def analyze_term_with_gtest(term: str, data_dir: str,
                            lookback_window: int = 12) -> Dict:
    """
    Analyze term using G-test across entire corpus.

    Uses rolling baseline: for each document, baseline is the previous
    lookback_window documents.

    Args:
        term: Term to analyze
        data_dir: Directory with policy statements
        lookback_window: Number of previous documents for baseline

    Returns:
        Analysis results
    """
    print(f"\n{'='*70}")
    print(f"G-test Analysis: '{term}'")
    print(f"{'='*70}\n")

    # Load corpus
    dates, texts, doc_lengths = load_corpus_data(data_dir)
    print(f"Loaded {len(dates)} documents")
    print(f"Lookback window: {lookback_window} documents\n")

    # Count term in all documents
    counts = {date: count_term_occurrences(texts[date], term)
              for date in dates}

    detector = GTestDetector(significance_threshold=10.83)
    detections = []

    # Analyze each document (skip first lookback_window docs for baseline)
    for i in range(lookback_window, len(dates)):
        target_date = dates[i]
        target_count = counts[target_date]
        target_length = doc_lengths[target_date]

        # Build baseline from previous documents
        baseline_start = max(0, i - lookback_window)
        baseline_dates = dates[baseline_start:i]

        baseline_count = sum(counts[d] for d in baseline_dates)
        baseline_length = sum(doc_lengths[d] for d in baseline_dates)

        # Get previous document count for shift type determination
        prev_count = counts[dates[i-1]] if i > 0 else 0

        # Detect shift
        result = detector.detect_shift(
            term, target_date, target_count, target_length,
            baseline_count, baseline_length, prev_count
        )

        detections.append(result)

        # Print significant detections
        if result['is_significant'] and result['shift_type']:
            print(f"DETECTION at {target_date}:")
            print(f"  Type: {result['shift_type'].upper()}")
            print(f"  G-statistic: {result['G_statistic']:.2f}")
            print(f"  Target count: {result['target_count']}")
            print(f"  Previous count: {result['prev_count']}")
            print(f"  Rate ratio: {result['rate_ratio']:.2f}x")
            print()

    # Summary statistics
    significant_detections = [d for d in detections if d['is_significant']]
    emergences = [d for d in significant_detections if d['shift_type'] == 'emergence']
    removals = [d for d in significant_detections if d['shift_type'] == 'removal']

    print(f"\nSummary:")
    print(f"  Total documents analyzed: {len(detections)}")
    print(f"  Significant shifts detected: {len(significant_detections)}")
    print(f"    Emergences: {len(emergences)}")
    print(f"    Removals: {len(removals)}")
    print(f"    Other changes: {len(significant_detections) - len(emergences) - len(removals)}")

    return {
        'term': term,
        'analysis_date': datetime.now().isoformat(),
        'parameters': {
            'lookback_window': lookback_window,
            'significance_threshold': detector.significance_threshold
        },
        'detections': detections,
        'summary': {
            'total_analyzed': len(detections),
            'significant_shifts': len(significant_detections),
            'emergences': len(emergences),
            'removals': len(removals)
        }
    }


def test_transitory_december_2021(data_dir: str) -> Dict:
    """
    Critical test: Detect 'transitory' removal in December 2021.
    """
    print("\n" + "="*70)
    print("CRITICAL TEST: 'transitory' Removal - December 2021")
    print("="*70)

    results = analyze_term_with_gtest('transitory', data_dir)

    # Check if December 2021 removal was detected
    dec_2021_detection = None
    for detection in results['detections']:
        if detection['date'] == '20211215':
            dec_2021_detection = detection
            break

    detected = (dec_2021_detection is not None and
                dec_2021_detection['is_significant'] and
                dec_2021_detection['shift_type'] == 'removal')

    print("\n" + "-"*70)
    print("TEST RESULT:")
    if detected:
        print(f"  SUCCESS: December 2021 removal DETECTED")
        print(f"  G-statistic: {dec_2021_detection['G_statistic']}")
        print(f"  Shift type: {dec_2021_detection['shift_type']}")
    else:
        print(f"  FAILURE: December 2021 removal NOT DETECTED")
        if dec_2021_detection:
            print(f"  (G-statistic: {dec_2021_detection['G_statistic']}, " +
                  f"Significant: {dec_2021_detection['is_significant']})")
    print("-"*70)

    return {
        'test_name': 'transitory_december_2021_removal',
        'detected': detected,
        'detection_details': dec_2021_detection,
        'all_detections': results['detections']
    }


def backtest_ground_truth(data_dir: str, ground_truth_file: str,
                         lookback_window: int = 12) -> Dict:
    """
    Backtest G-test detector on all 130 ground truth shifts.

    Args:
        data_dir: Directory with policy statements
        ground_truth_file: Path to GROUND_TRUTH_SHIFTS.csv
        lookback_window: Baseline window size

    Returns:
        Backtesting results with precision/recall metrics
    """
    print("\n" + "="*70)
    print("BACKTESTING G-TEST ON 130 GROUND TRUTH SHIFTS")
    print("="*70 + "\n")

    # Load ground truth
    ground_truth = []
    with open(ground_truth_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth.append({
                'date': row['Date'],
                'type': row['Type'],
                'term': row['Term']
            })

    print(f"Loaded {len(ground_truth)} ground truth shifts")

    # Get unique terms
    terms = set(shift['term'] for shift in ground_truth)
    print(f"Analyzing {len(terms)} unique terms\n")

    # Load corpus
    dates, texts, doc_lengths = load_corpus_data(data_dir)

    # Analyze each term
    all_detections = {}
    detector = GTestDetector(significance_threshold=10.83)

    for term in terms:
        print(f"Analyzing '{term}'...")

        # Count term in all documents
        counts = {date: count_term_occurrences(texts[date], term)
                  for date in dates}

        term_detections = []

        for i in range(lookback_window, len(dates)):
            target_date = dates[i]
            target_count = counts[target_date]
            target_length = doc_lengths[target_date]

            baseline_start = max(0, i - lookback_window)
            baseline_dates = dates[baseline_start:i]

            baseline_count = sum(counts[d] for d in baseline_dates)
            baseline_length = sum(doc_lengths[d] for d in baseline_dates)

            prev_count = counts[dates[i-1]] if i > 0 else 0

            result = detector.detect_shift(
                term, target_date, target_count, target_length,
                baseline_count, baseline_length, prev_count
            )

            if result['is_significant'] and result['shift_type'] in ['emergence', 'removal']:
                term_detections.append(result)

        all_detections[term] = term_detections

    # Compare against ground truth
    true_positives = []
    false_positives = []
    false_negatives = []

    # Check each ground truth shift
    for gt_shift in ground_truth:
        detected = False

        term = gt_shift['term']
        if term in all_detections:
            for detection in all_detections[term]:
                if (detection['date'] == gt_shift['date'] and
                    detection['shift_type'] == gt_shift['type']):
                    detected = True
                    true_positives.append({
                        'ground_truth': gt_shift,
                        'detection': detection
                    })
                    break

        if not detected:
            false_negatives.append(gt_shift)

    # Find false positives (detections not in ground truth)
    for term, detections in all_detections.items():
        for detection in detections:
            is_false_positive = True
            for gt_shift in ground_truth:
                if (gt_shift['term'] == term and
                    gt_shift['date'] == detection['date'] and
                    gt_shift['type'] == detection['shift_type']):
                    is_false_positive = False
                    break

            if is_false_positive:
                false_positives.append(detection)

    # Calculate metrics
    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "="*70)
    print("BACKTESTING RESULTS:")
    print("="*70)
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"\nPrecision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    print("="*70)

    return {
        'test_name': 'ground_truth_backtest',
        'method': 'g_test',
        'parameters': {
            'lookback_window': lookback_window,
            'significance_threshold': detector.significance_threshold
        },
        'metrics': {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3)
        },
        'true_positives': true_positives[:10],  # Sample
        'false_positives': false_positives[:10],  # Sample
        'false_negatives': false_negatives[:10]   # Sample
    }


if __name__ == "__main__":
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"
    GROUND_TRUTH = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Test 1: Critical transitory test
    transitory_results = test_transitory_december_2021(DATA_DIR)
    with open(f"{OUTPUT_DIR}/gtest_transitory_test.json", 'w') as f:
        json.dump(transitory_results, f, indent=2)

    # Test 2: Full backtest on 130 ground truth shifts
    print("\n\n")
    backtest_results = backtest_ground_truth(DATA_DIR, GROUND_TRUTH)
    with open(f"{OUTPUT_DIR}/gtest_backtest_results.json", 'w') as f:
        json.dump(backtest_results, f, indent=2)
