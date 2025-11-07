"""
Jensen-Shannon Divergence for FedSpeak Shift Detection
========================================================

Implements Jensen-Shannon Divergence (JSD) to detect changes in word
frequency distributions between consecutive FOMC policy statements.

Theory:
- JSD measures similarity between two probability distributions
- Symmetric version of Kullback-Leibler divergence
- Bounded [0, 1], with 0 = identical distributions
- Higher JSD indicates greater distributional change

JSD(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
where M = 0.5 * (P + Q)
"""

import os
import re
import json
import math
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np
import csv


class JSDDetector:
    """
    Jensen-Shannon Divergence based shift detection.

    Detects distributional changes between consecutive documents and
    attributes them to specific terms.
    """

    def __init__(self, jsd_threshold: float = 0.01,
                 term_contribution_threshold: float = 0.001):
        """
        Initialize JSD detector.

        Args:
            jsd_threshold: Minimum JSD for significant change
            term_contribution_threshold: Minimum term contribution to JSD
        """
        self.jsd_threshold = jsd_threshold
        self.term_contribution_threshold = term_contribution_threshold

    def calculate_jsd(self, p: Dict[str, float], q: Dict[str, float]) -> float:
        """
        Calculate Jensen-Shannon Divergence between two distributions.

        Args:
            p, q: Probability distributions as {word: probability} dicts

        Returns:
            JSD value [0, 1]
        """
        # Get all words from both distributions
        all_words = set(p.keys()) | set(q.keys())

        # Calculate mixture distribution M = 0.5 * (P + Q)
        m = {}
        for word in all_words:
            m[word] = 0.5 * (p.get(word, 0) + q.get(word, 0))

        # Calculate KL divergences
        kl_pm = self._kl_divergence(p, m)
        kl_qm = self._kl_divergence(q, m)

        # JSD = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
        jsd = 0.5 * kl_pm + 0.5 * kl_qm

        return jsd

    def _kl_divergence(self, p: Dict[str, float],
                       q: Dict[str, float]) -> float:
        """
        Calculate Kullback-Leibler divergence KL(P||Q).

        KL(P||Q) = sum_i P(i) * log(P(i) / Q(i))
        """
        kl = 0.0
        for word, p_prob in p.items():
            if p_prob > 0:
                q_prob = q.get(word, 1e-10)  # Smoothing for zero probabilities
                kl += p_prob * math.log(p_prob / q_prob)
        return kl

    def calculate_term_contribution(self, term: str,
                                   p: Dict[str, float],
                                   q: Dict[str, float]) -> float:
        """
        Calculate a specific term's contribution to total JSD.

        This is an approximation: we measure how much the term's
        probability change contributes to the overall divergence.
        """
        # Create modified distributions without the term
        p_without = {k: v for k, v in p.items() if k != term}
        q_without = {k: v for k, v in q.items() if k != term}

        # Renormalize
        p_sum = sum(p_without.values())
        q_sum = sum(q_without.values())

        if p_sum > 0:
            p_without = {k: v/p_sum for k, v in p_without.items()}
        if q_sum > 0:
            q_without = {k: v/q_sum for k, v in q_without.items()}

        # JSD with and without the term
        jsd_full = self.calculate_jsd(p, q)
        jsd_without = self.calculate_jsd(p_without, q_without)

        # Contribution is the difference
        contribution = jsd_full - jsd_without

        return max(0, contribution)  # Can't be negative

    def detect_shifts(self, prev_text: str, curr_text: str,
                     prev_date: str, curr_date: str,
                     terms_to_track: List[str]) -> Dict:
        """
        Detect distributional shifts between two consecutive documents.

        Args:
            prev_text: Previous document text
            curr_text: Current document text
            prev_date: Previous document date
            curr_date: Current document date
            terms_to_track: Specific terms to analyze

        Returns:
            Detection results
        """
        # Build word frequency distributions
        prev_dist = self._build_distribution(prev_text)
        curr_dist = self._build_distribution(curr_text)

        # Calculate overall JSD
        overall_jsd = self.calculate_jsd(prev_dist, curr_dist)

        # Analyze each tracked term
        term_contributions = {}
        for term in terms_to_track:
            # Normalize term for lookup
            term_words = term.lower().split()

            # For multi-word terms, we approximate by looking at component words
            # (This is a simplification; ideal would be to treat phrase as single token)
            contribution = 0
            for word in term_words:
                if word in prev_dist or word in curr_dist:
                    word_contrib = self.calculate_term_contribution(
                        word, prev_dist, curr_dist
                    )
                    contribution = max(contribution, word_contrib)

            term_contributions[term] = contribution

        # Determine shift type for each term
        detections = []
        for term, contribution in term_contributions.items():
            if contribution >= self.term_contribution_threshold:
                # Count term in both documents
                prev_count = count_term_occurrences(prev_text, term)
                curr_count = count_term_occurrences(curr_text, term)

                # Determine shift type
                shift_type = None
                if curr_count > 0 and prev_count == 0:
                    shift_type = 'emergence'
                elif curr_count == 0 and prev_count > 0:
                    shift_type = 'removal'
                elif curr_count > prev_count * 1.5:
                    shift_type = 'increase'
                elif curr_count < prev_count * 0.5 and prev_count > 0:
                    shift_type = 'decrease'

                if shift_type:
                    detections.append({
                        'term': term,
                        'date': curr_date,
                        'shift_type': shift_type,
                        'jsd_contribution': round(contribution, 6),
                        'overall_jsd': round(overall_jsd, 6),
                        'prev_count': prev_count,
                        'curr_count': curr_count,
                        'is_significant': overall_jsd >= self.jsd_threshold
                    })

        return {
            'prev_date': prev_date,
            'curr_date': curr_date,
            'overall_jsd': round(overall_jsd, 6),
            'is_significant': overall_jsd >= self.jsd_threshold,
            'detections': detections
        }

    def _build_distribution(self, text: str) -> Dict[str, float]:
        """
        Build word frequency distribution from text.

        Returns normalized probabilities: {word: probability}
        """
        # Tokenize
        words = text.lower().split()

        # Count frequencies
        counts = Counter(words)

        # Normalize to probabilities
        total = sum(counts.values())
        if total == 0:
            return {}

        distribution = {word: count / total for word, count in counts.items()}

        return distribution


def count_term_occurrences(text: str, term: str) -> int:
    """Count occurrences of a term (case-insensitive, whole-word)."""
    text_lower = text.lower()
    term_lower = term.lower()
    pattern = r'\b' + re.escape(term_lower) + r'\b'
    matches = re.findall(pattern, text_lower)
    return len(matches)


def load_corpus_data(data_dir: str) -> Tuple[List[str], Dict[str, str]]:
    """Load all policy statements from corpus."""
    texts = {}

    for filename in os.listdir(data_dir):
        if filename.startswith('policy_statement_') and filename.endswith('.txt'):
            match = re.search(r'policy_statement_(\d{8})', filename)
            if match:
                date_str = match.group(1)
                filepath = os.path.join(data_dir, filename)

                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    texts[date_str] = text

    dates = sorted(texts.keys())
    return dates, texts


def analyze_corpus_with_jsd(data_dir: str, terms_to_track: List[str]) -> Dict:
    """
    Analyze entire corpus using JSD to detect shifts.

    Args:
        data_dir: Directory with policy statements
        terms_to_track: List of terms to monitor

    Returns:
        Analysis results
    """
    print(f"\n{'='*70}")
    print(f"Jensen-Shannon Divergence Analysis")
    print(f"{'='*70}\n")

    # Load corpus
    dates, texts = load_corpus_data(data_dir)
    print(f"Loaded {len(dates)} documents")
    print(f"Tracking {len(terms_to_track)} terms\n")

    detector = JSDDetector(jsd_threshold=0.01,
                          term_contribution_threshold=0.001)

    all_results = []
    all_detections = []

    # Analyze consecutive document pairs
    for i in range(1, len(dates)):
        prev_date = dates[i-1]
        curr_date = dates[i]

        result = detector.detect_shifts(
            texts[prev_date], texts[curr_date],
            prev_date, curr_date,
            terms_to_track
        )

        all_results.append(result)

        # Collect significant detections
        if result['is_significant'] and result['detections']:
            for detection in result['detections']:
                all_detections.append(detection)
                print(f"DETECTION at {detection['date']}:")
                print(f"  Term: {detection['term']}")
                print(f"  Type: {detection['shift_type'].upper()}")
                print(f"  JSD contribution: {detection['jsd_contribution']:.6f}")
                print(f"  Overall JSD: {detection['overall_jsd']:.6f}")
                print(f"  Count change: {detection['prev_count']} -> {detection['curr_count']}")
                print()

    # Summary statistics
    emergences = [d for d in all_detections if d['shift_type'] == 'emergence']
    removals = [d for d in all_detections if d['shift_type'] == 'removal']

    print(f"\nSummary:")
    print(f"  Document pairs analyzed: {len(all_results)}")
    print(f"  Significant changes detected: {sum(1 for r in all_results if r['is_significant'])}")
    print(f"  Term-level detections: {len(all_detections)}")
    print(f"    Emergences: {len(emergences)}")
    print(f"    Removals: {len(removals)}")

    return {
        'analysis_date': datetime.now().isoformat(),
        'parameters': {
            'jsd_threshold': detector.jsd_threshold,
            'term_contribution_threshold': detector.term_contribution_threshold
        },
        'terms_tracked': terms_to_track,
        'results': all_results,
        'summary': {
            'pairs_analyzed': len(all_results),
            'significant_changes': sum(1 for r in all_results if r['is_significant']),
            'total_detections': len(all_detections),
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

    results = analyze_corpus_with_jsd(data_dir, ['transitory'])

    # Find December 2021 detection
    dec_2021_detection = None
    for result in results['results']:
        if result['curr_date'] == '20211215':
            for detection in result['detections']:
                if detection['term'] == 'transitory':
                    dec_2021_detection = detection
                    break

    detected = (dec_2021_detection is not None and
                dec_2021_detection['shift_type'] == 'removal' and
                dec_2021_detection['is_significant'])

    print("\n" + "-"*70)
    print("TEST RESULT:")
    if detected:
        print(f"  SUCCESS: December 2021 removal DETECTED")
        print(f"  JSD contribution: {dec_2021_detection['jsd_contribution']}")
        print(f"  Overall JSD: {dec_2021_detection['overall_jsd']}")
    else:
        print(f"  FAILURE: December 2021 removal NOT DETECTED")
        if dec_2021_detection:
            print(f"  (Found detection but not classified as significant removal)")
    print("-"*70)

    return {
        'test_name': 'transitory_december_2021_removal',
        'detected': detected,
        'detection_details': dec_2021_detection,
        'all_results': results['results']
    }


def backtest_ground_truth(data_dir: str, ground_truth_file: str) -> Dict:
    """
    Backtest JSD detector on all 130 ground truth shifts.
    """
    print("\n" + "="*70)
    print("BACKTESTING JSD ON 130 GROUND TRUTH SHIFTS")
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
    terms = list(set(shift['term'] for shift in ground_truth))
    print(f"Analyzing {len(terms)} unique terms\n")

    # Run JSD analysis
    results = analyze_corpus_with_jsd(data_dir, terms)

    # Collect all detections
    all_detections = []
    for result in results['results']:
        for detection in result['detections']:
            if detection['is_significant']:
                all_detections.append(detection)

    # Compare against ground truth
    true_positives = []
    false_positives = []
    false_negatives = []

    # Check each ground truth shift
    for gt_shift in ground_truth:
        detected = False

        for detection in all_detections:
            if (detection['term'] == gt_shift['term'] and
                detection['date'] == gt_shift['date'] and
                detection['shift_type'] == gt_shift['type']):
                detected = True
                true_positives.append({
                    'ground_truth': gt_shift,
                    'detection': detection
                })
                break

        if not detected:
            false_negatives.append(gt_shift)

    # Find false positives
    for detection in all_detections:
        is_false_positive = True
        for gt_shift in ground_truth:
            if (gt_shift['term'] == detection['term'] and
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
        'method': 'jsd',
        'parameters': {
            'jsd_threshold': 0.01,
            'term_contribution_threshold': 0.001
        },
        'metrics': {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3)
        },
        'true_positives': true_positives[:10],
        'false_positives': false_positives[:10],
        'false_negatives': false_negatives[:10]
    }


if __name__ == "__main__":
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"
    GROUND_TRUTH = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Test 1: Critical transitory test
    transitory_results = test_transitory_december_2021(DATA_DIR)
    with open(f"{OUTPUT_DIR}/jsd_transitory_test.json", 'w') as f:
        json.dump(transitory_results, f, indent=2)

    # Test 2: Full backtest on 130 ground truth shifts
    print("\n\n")
    backtest_results = backtest_ground_truth(DATA_DIR, GROUND_TRUTH)
    with open(f"{OUTPUT_DIR}/jsd_backtest_results.json", 'w') as f:
        json.dump(backtest_results, f, indent=2)
