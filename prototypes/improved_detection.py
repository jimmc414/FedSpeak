"""
Improved Detection Methods - Adapted for Sparse FedSpeak Data
==============================================================

The original statistical methods failed because they assume denser data.
For FedSpeak's sparse term usage, we need:
1. Lower thresholds adapted to small counts
2. Combination of statistical + rule-based approaches
3. Focus on PRESENCE/ABSENCE rather than frequency changes
"""

import os
import re
import json
import math
import csv
from collections import defaultdict, Counter
from typing import List, Dict, Tuple


class ImprovedDetector:
    """
    Hybrid detection combining statistical tests with rule-based logic,
    optimized for sparse data like FedSpeak corpus.
    """

    def __init__(self):
        pass

    def detect_shift(self, term: str, dates: List[str], texts: Dict[str, str],
                    lookback: int = 3) -> List[Dict]:
        """
        Detect shifts using multiple signals combined.

        Args:
            term: Term to track
            dates: Chronologically sorted dates
            texts: Dict mapping date to text
            lookback: Number of previous docs for context

        Returns:
            List of detected shifts
        """
        detections = []

        # Count term in each document
        counts = {date: self._count_term(texts[date], term) for date in dates}

        for i in range(lookback, len(dates)):
            curr_date = dates[i]
            curr_count = counts[curr_date]

            # Look at previous documents
            prev_dates = dates[max(0, i-lookback):i]
            prev_counts = [counts[d] for d in prev_dates]
            prev_avg = sum(prev_counts) / len(prev_counts) if prev_counts else 0

            # Signal 1: Absolute presence/absence change
            prev_had_term = any(c > 0 for c in prev_counts)
            curr_has_term = curr_count > 0

            # Signal 2: Significant count change
            if prev_avg > 0:
                relative_change = abs(curr_count - prev_avg) / prev_avg
            else:
                relative_change = 1.0 if curr_count > 0 else 0

            # Signal 3: Fisher's exact test (better for small counts)
            p_value = self._fishers_exact_test(
                curr_count,
                len(texts[curr_date].split()) - curr_count,
                int(prev_avg * len(prev_dates)),
                sum(len(texts[d].split()) for d in prev_dates) - int(prev_avg * len(prev_dates))
            )

            # Detection logic
            shift_type = None
            confidence = 'low'

            # EMERGENCE: Term appears after being absent
            if curr_has_term and not prev_had_term:
                shift_type = 'emergence'
                confidence = 'high' if curr_count > 1 else 'medium'

            # REMOVAL: Term disappears after being present
            elif not curr_has_term and prev_had_term:
                shift_type = 'removal'
                confidence = 'high'  # Complete absence is strong signal

            # INCREASE: Significant count increase
            elif curr_count > prev_avg * 2 and curr_count > 1:
                shift_type = 'increase'
                confidence = 'medium' if p_value < 0.05 else 'low'

            # DECREASE: Significant count decrease
            elif curr_count < prev_avg * 0.5 and prev_avg > 1:
                shift_type = 'decrease'
                confidence = 'medium' if p_value < 0.05 else 'low'

            if shift_type:
                detections.append({
                    'date': curr_date,
                    'term': term,
                    'shift_type': shift_type,
                    'confidence': confidence,
                    'curr_count': curr_count,
                    'prev_avg': round(prev_avg, 2),
                    'relative_change': round(relative_change, 2),
                    'p_value': round(p_value, 4) if p_value else None
                })

        return detections

    def _count_term(self, text: str, term: str) -> int:
        """Count term occurrences (case-insensitive, whole-word)."""
        text_lower = text.lower()
        term_lower = term.lower()
        pattern = r'\b' + re.escape(term_lower) + r'\b'
        return len(re.findall(pattern, text_lower))

    def _fishers_exact_test(self, a: int, b: int, c: int, d: int) -> float:
        """
        Simplified Fisher's exact test approximation.
        For small counts, provides better p-value than G-test.

        Uses chi-squared approximation with Yates' correction.
        """
        n = a + b + c + d
        if n == 0:
            return 1.0

        # Expected values
        E_a = (a + b) * (a + c) / n
        E_b = (a + b) * (b + d) / n
        E_c = (c + d) * (a + c) / n
        E_d = (c + d) * (b + d) / n

        # Chi-squared with Yates' correction for continuity
        chi_sq = 0
        for observed, expected in [(a, E_a), (b, E_b), (c, E_c), (d, E_d)]:
            if expected > 0:
                diff = abs(observed - expected) - 0.5  # Yates' correction
                diff = max(0, diff)
                chi_sq += (diff ** 2) / expected

        # Approximate p-value (df=1)
        # Using simplified approximation
        if chi_sq < 0.001:
            p_value = 1.0
        elif chi_sq < 1:
            p_value = 0.3
        elif chi_sq < 3.84:
            p_value = 0.1
        elif chi_sq < 6.63:
            p_value = 0.01
        else:
            p_value = 0.001

        return p_value


def load_corpus_data(data_dir: str) -> Tuple[List[str], Dict[str, str]]:
    """Load all policy statements."""
    texts = {}

    for filename in os.listdir(data_dir):
        if filename.startswith('policy_statement_') and filename.endswith('.txt'):
            match = re.search(r'policy_statement_(\d{8})', filename)
            if match:
                date_str = match.group(1)
                filepath = os.path.join(data_dir, filename)

                with open(filepath, 'r', encoding='utf-8') as f:
                    texts[date_str] = f.read()

    dates = sorted(texts.keys())
    return dates, texts


def test_improved_detector(data_dir: str, ground_truth_file: str) -> Dict:
    """Test improved detector on ground truth."""

    print("="*80)
    print("IMPROVED DETECTOR - Optimized for Sparse Data")
    print("="*80)

    # Load corpus
    dates, texts = load_corpus_data(data_dir)
    print(f"\nLoaded {len(dates)} policy statements")

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
    terms = list(set(shift['term'] for shift in ground_truth))
    print(f"Analyzing {len(terms)} unique terms\n")

    # Run detection for each term
    detector = ImprovedDetector()
    all_detections = []

    for term in terms:
        print(f"Analyzing '{term}'...")
        detections = detector.detect_shift(term, dates, texts, lookback=3)

        # Filter to medium/high confidence
        significant = [d for d in detections if d['confidence'] in ['medium', 'high']]
        all_detections.extend(significant)

        print(f"  Found {len(significant)} significant shifts")

    # Compare against ground truth
    true_positives = []
    false_positives = []
    false_negatives = []

    for gt in ground_truth:
        detected = False
        for det in all_detections:
            if (det['term'] == gt['term'] and
                det['date'] == gt['date'] and
                det['shift_type'] == gt['type']):
                detected = True
                true_positives.append({'ground_truth': gt, 'detection': det})
                break

        if not detected:
            false_negatives.append(gt)

    for det in all_detections:
        is_fp = True
        for gt in ground_truth:
            if (gt['term'] == det['term'] and
                gt['date'] == det['date'] and
                gt['type'] == det['shift_type']):
                is_fp = False
                break
        if is_fp:
            false_positives.append(det)

    # Calculate metrics
    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"\nPrecision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")

    # Check critical test
    transitory_dec_2021 = None
    for det in all_detections:
        if det['term'] == 'transitory' and det['date'] == '20211215':
            transitory_dec_2021 = det
            break

    print("\n" + "="*80)
    print("CRITICAL TEST: Transitory December 2021")
    print("="*80)
    if transitory_dec_2021:
        print("PASSED: Detected")
        print(f"  Shift type: {transitory_dec_2021['shift_type']}")
        print(f"  Confidence: {transitory_dec_2021['confidence']}")
    else:
        print("FAILED: Not detected")

    return {
        'method': 'improved_hybrid',
        'metrics': {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3)
        },
        'transitory_test': {
            'detected': transitory_dec_2021 is not None,
            'details': transitory_dec_2021
        },
        'sample_true_positives': true_positives[:5],
        'sample_false_positives': false_positives[:5],
        'sample_false_negatives': false_negatives[:5]
    }


if __name__ == "__main__":
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    GROUND_TRUTH = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"

    results = test_improved_detector(DATA_DIR, GROUND_TRUTH)

    with open(f"{OUTPUT_DIR}/improved_detector_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {OUTPUT_DIR}/improved_detector_results.json")
