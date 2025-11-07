"""
Kleinberg Burst Detection for FedSpeak Analysis
=================================================

Implements Kleinberg's burst detection algorithm to identify sudden increases
or decreases in term usage frequency across FOMC policy statements.

Theory:
- Models term appearance as a two-state automaton (low/high usage)
- Uses state transition costs to detect "bursts" of activity
- Assigns burst weights indicating strength of signal

Reference: Kleinberg, J. (2002). "Bursty and Hierarchical Structure in Streams"
"""

import os
import re
import json
import math
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np


class KleinbergBurstDetector:
    """
    Kleinberg burst detection implementation for term frequency analysis.

    Detects both emergences (bursts) and removals (anti-bursts) of terms.
    """

    def __init__(self, s: float = 2.0, gamma: float = 1.0):
        """
        Initialize burst detector.

        Args:
            s: State advancement cost (higher = fewer state changes)
            gamma: Transition cost scaling factor
        """
        self.s = s
        self.gamma = gamma

    def detect_bursts(self, dates: List[str], counts: List[int],
                     doc_lengths: List[int]) -> List[Dict]:
        """
        Detect bursts in term frequency sequence.

        Args:
            dates: Chronologically ordered document dates
            counts: Term count in each document
            doc_lengths: Total words in each document

        Returns:
            List of burst/anti-burst events with scores
        """
        if len(dates) != len(counts) or len(dates) != len(doc_lengths):
            raise ValueError("Input arrays must have same length")

        if len(dates) < 2:
            return []

        # Normalize counts by document length
        normalized_rates = []
        for i, count in enumerate(counts):
            if doc_lengths[i] > 0:
                normalized_rates.append(count / doc_lengths[i])
            else:
                normalized_rates.append(0)

        # Calculate baseline rate
        total_count = sum(counts)
        total_length = sum(doc_lengths)
        baseline_rate = total_count / total_length if total_length > 0 else 0

        if baseline_rate == 0:
            return []

        # Calculate burst states using Viterbi-like algorithm
        states = self._compute_burst_states(normalized_rates, baseline_rate)

        # Identify burst/anti-burst periods
        bursts = self._identify_burst_periods(dates, counts, normalized_rates,
                                              states, baseline_rate)

        return bursts

    def _compute_burst_states(self, rates: List[float],
                             baseline_rate: float) -> List[int]:
        """
        Compute optimal burst state sequence using dynamic programming.

        Uses a simplified version of Kleinberg's automaton model.
        """
        n = len(rates)
        max_state = 3  # 0=baseline, 1=elevated, 2=burst, 3=super-burst

        # State emission probabilities (simplified)
        state_rates = [baseline_rate * (self.s ** i) for i in range(max_state + 1)]

        # Dynamic programming: cost[t][state] = min cost to reach state at time t
        cost = [[float('inf')] * (max_state + 1) for _ in range(n)]
        backpointer = [[0] * (max_state + 1) for _ in range(n)]

        # Initialize first timestep
        for state in range(max_state + 1):
            cost[0][state] = self._emission_cost(rates[0], state_rates[state])

        # Forward pass
        for t in range(1, n):
            for curr_state in range(max_state + 1):
                emission = self._emission_cost(rates[t], state_rates[curr_state])

                for prev_state in range(max_state + 1):
                    transition = self._transition_cost(prev_state, curr_state)
                    total_cost = cost[t-1][prev_state] + transition + emission

                    if total_cost < cost[t][curr_state]:
                        cost[t][curr_state] = total_cost
                        backpointer[t][curr_state] = prev_state

        # Backward pass: find optimal path
        states = [0] * n
        states[n-1] = min(range(max_state + 1), key=lambda s: cost[n-1][s])

        for t in range(n-2, -1, -1):
            states[t] = backpointer[t+1][states[t+1]]

        return states

    def _emission_cost(self, observed_rate: float,
                       expected_rate: float) -> float:
        """
        Cost of emitting observed rate from a state with expected rate.
        Uses negative log-likelihood.
        """
        if expected_rate <= 0:
            return 0 if observed_rate == 0 else float('inf')

        # Simplified: assume Poisson-like behavior
        if observed_rate == 0:
            return expected_rate

        return -math.log(expected_rate) + expected_rate - observed_rate * math.log(observed_rate)

    def _transition_cost(self, from_state: int, to_state: int) -> float:
        """Cost of transitioning between states."""
        if from_state == to_state:
            return 0
        return self.gamma * abs(to_state - from_state)

    def _identify_burst_periods(self, dates: List[str], counts: List[int],
                                rates: List[float], states: List[int],
                                baseline_rate: float) -> List[Dict]:
        """Identify and score burst periods from state sequence."""
        bursts = []
        n = len(dates)

        # Find state transitions
        for i in range(1, n):
            prev_state = states[i-1]
            curr_state = states[i]

            # Detect emergence (state increase)
            if curr_state > prev_state and curr_state > 0:
                burst_weight = self._calculate_burst_weight(
                    rates[i], baseline_rate, counts[i]
                )

                if burst_weight > 1.0:  # Threshold for significance
                    bursts.append({
                        'date': dates[i],
                        'type': 'emergence',
                        'state_change': f"{prev_state} -> {curr_state}",
                        'burst_weight': round(burst_weight, 2),
                        'count': counts[i],
                        'normalized_rate': round(rates[i], 6),
                        'baseline_rate': round(baseline_rate, 6)
                    })

            # Detect removal (state decrease or drop to zero)
            elif curr_state < prev_state or (counts[i] == 0 and counts[i-1] > 0):
                burst_weight = self._calculate_burst_weight(
                    rates[i-1], baseline_rate, counts[i-1]
                )

                # For removals, weight based on previous usage
                if counts[i] == 0 and counts[i-1] > 0:
                    burst_weight = max(burst_weight, 3.0)  # Minimum weight for complete removal

                if burst_weight > 1.0:
                    bursts.append({
                        'date': dates[i],
                        'type': 'removal',
                        'state_change': f"{prev_state} -> {curr_state}",
                        'burst_weight': round(burst_weight, 2),
                        'count': counts[i],
                        'prev_count': counts[i-1],
                        'normalized_rate': round(rates[i], 6),
                        'baseline_rate': round(baseline_rate, 6)
                    })

        return bursts

    def _calculate_burst_weight(self, rate: float, baseline: float,
                                count: int) -> float:
        """
        Calculate burst weight (strength of signal).
        Higher values indicate stronger bursts.
        """
        if baseline <= 0:
            return 0.0

        ratio = rate / baseline if baseline > 0 else 0

        # Weight combines relative increase and absolute count
        weight = math.log(max(ratio, 1.0)) * math.log(count + 1)

        return weight


def load_corpus_data(data_dir: str) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
    """
    Load all policy statements from corpus.

    Returns:
        dates: Sorted list of dates
        texts: Dict mapping date to document text
        doc_lengths: Dict mapping date to word count
    """
    texts = {}
    doc_lengths = {}

    # Find all policy statement files
    for filename in os.listdir(data_dir):
        if filename.startswith('policy_statement_') and filename.endswith('.txt'):
            # Extract date from filename
            match = re.search(r'policy_statement_(\d{8})', filename)
            if match:
                date_str = match.group(1)
                filepath = os.path.join(data_dir, filename)

                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    texts[date_str] = text
                    # Simple word count
                    words = text.lower().split()
                    doc_lengths[date_str] = len(words)

    # Sort dates chronologically
    dates = sorted(texts.keys())

    return dates, texts, doc_lengths


def count_term_occurrences(text: str, term: str) -> int:
    """
    Count occurrences of a term (supports multi-word phrases).
    Case-insensitive, whole-word matching.
    """
    text_lower = text.lower()
    term_lower = term.lower()

    # Use word boundaries for accurate matching
    pattern = r'\b' + re.escape(term_lower) + r'\b'
    matches = re.findall(pattern, text_lower)

    return len(matches)


def analyze_term_bursts(term: str, data_dir: str,
                       output_file: Optional[str] = None) -> Dict:
    """
    Analyze burst patterns for a specific term across the corpus.

    Args:
        term: Term or phrase to analyze
        data_dir: Directory containing policy statements
        output_file: Optional file to save results

    Returns:
        Analysis results dictionary
    """
    print(f"\n{'='*70}")
    print(f"Kleinberg Burst Detection Analysis: '{term}'")
    print(f"{'='*70}\n")

    # Load corpus
    dates, texts, doc_lengths = load_corpus_data(data_dir)
    print(f"Loaded {len(dates)} policy statements")
    print(f"Date range: {dates[0]} to {dates[-1]}\n")

    # Count term occurrences in each document
    counts = [count_term_occurrences(texts[date], term) for date in dates]
    lengths = [doc_lengths[date] for date in dates]

    total_occurrences = sum(counts)
    docs_with_term = sum(1 for c in counts if c > 0)

    print(f"Term Statistics:")
    print(f"  Total occurrences: {total_occurrences}")
    print(f"  Documents containing term: {docs_with_term}/{len(dates)}")
    print(f"  Average count per document: {total_occurrences/len(dates):.2f}")

    if total_occurrences == 0:
        print(f"\nNo occurrences of '{term}' found in corpus.")
        return {'term': term, 'bursts': [], 'total_occurrences': 0}

    # Run burst detection
    detector = KleinbergBurstDetector(s=2.0, gamma=1.0)
    bursts = detector.detect_bursts(dates, counts, lengths)

    print(f"\nDetected {len(bursts)} burst events:\n")

    for i, burst in enumerate(bursts, 1):
        print(f"{i}. Date: {burst['date']}")
        print(f"   Type: {burst['type'].upper()}")
        print(f"   Burst Weight: {burst['burst_weight']}")
        print(f"   State Change: {burst['state_change']}")
        print(f"   Count: {burst['count']}")
        if 'prev_count' in burst:
            print(f"   Previous Count: {burst['prev_count']}")
        print()

    # Prepare results
    results = {
        'term': term,
        'analysis_date': datetime.now().isoformat(),
        'corpus_stats': {
            'total_documents': len(dates),
            'date_range': [dates[0], dates[-1]],
            'total_occurrences': total_occurrences,
            'documents_with_term': docs_with_term
        },
        'bursts': bursts,
        'detection_params': {
            's': detector.s,
            'gamma': detector.gamma
        }
    }

    # Save results if output file specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")

    return results


def test_transitory_december_2021(data_dir: str) -> Dict:
    """
    Critical test: Detect "transitory" removal in December 2021.

    This is the gold-standard test case for the FedSpeak corpus.
    """
    print("\n" + "="*70)
    print("CRITICAL TEST: 'transitory' Removal - December 2021")
    print("="*70)

    results = analyze_term_bursts('transitory', data_dir)

    # Check if December 2021 removal was detected
    dec_2021_detected = False
    detection_details = None

    for burst in results['bursts']:
        if burst['date'] == '20211215' and burst['type'] == 'removal':
            dec_2021_detected = True
            detection_details = burst
            break

    print("\n" + "-"*70)
    print("TEST RESULT:")
    if dec_2021_detected:
        print(f"  SUCCESS: December 2021 removal DETECTED")
        print(f"  Burst Weight: {detection_details['burst_weight']}")
        print(f"  State Change: {detection_details['state_change']}")
    else:
        print(f"  FAILURE: December 2021 removal NOT DETECTED")
    print("-"*70)

    return {
        'test_name': 'transitory_december_2021_removal',
        'detected': dec_2021_detected,
        'details': detection_details,
        'all_bursts': results['bursts']
    }


if __name__ == "__main__":
    # Configuration
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"

    # Test 1: Critical "transitory" test
    transitory_results = test_transitory_december_2021(DATA_DIR)

    with open(f"{OUTPUT_DIR}/burst_transitory_test.json", 'w') as f:
        json.dump(transitory_results, f, indent=2)

    # Test 2: Analyze other key terms
    print("\n\n")
    key_terms = ['patient', 'accommodative', 'considerable time']

    for term in key_terms:
        results = analyze_term_bursts(
            term,
            DATA_DIR,
            f"{OUTPUT_DIR}/burst_{term.replace(' ', '_')}.json"
        )
        print("\n" + "="*70 + "\n")
