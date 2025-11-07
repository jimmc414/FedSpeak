#!/usr/bin/env python3
"""
Semantic Proximity to Policy Terms
===================================

Tests Response 2 & 3 claim: Calculate cosine similarity to policy seed set
to identify policy-relevant terms.

Claim: "Transitory" would score high due to proximity to "inflation"
Tests: Does semantic proximity correlate with shift significance?

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import json
import csv
from datetime import datetime
from gensim.models import Word2Vec
import numpy as np
from collections import defaultdict


class SemanticProximityTester:
    """Test semantic proximity scoring for policy relevance"""

    def __init__(self, model_path, ground_truth_path):
        self.model = Word2Vec.load(model_path)
        self.wv = self.model.wv

        # Load ground truth shifts
        self.ground_truth = self.load_ground_truth(ground_truth_path)

        # Policy seed set from Response 2
        self.policy_seeds = [
            'inflation',
            'employment',
            'growth',
            'policy',
            'rate',
            'risk',
            'economy',
            'labor',
            'prices'
        ]

    def load_ground_truth(self, path):
        """Load ground truth shifts from CSV"""
        shifts = []
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                shifts.append({
                    'date': row['Date'],
                    'type': row['Type'],
                    'term': row['Term'],
                    'alert_file': row['Alert_File']
                })
        return shifts

    def check_word_exists(self, word):
        """Check if word exists in vocabulary"""
        return word.lower() in self.wv

    def calculate_proximity_score(self, word):
        """
        Calculate semantic proximity to policy seed set

        Returns average cosine similarity to all policy seed words
        """
        word = word.lower()

        if not self.check_word_exists(word):
            return None, f"'{word}' not in vocabulary"

        similarities = []
        for seed in self.policy_seeds:
            if self.check_word_exists(seed):
                sim = self.wv.similarity(word, seed)
                similarities.append(sim)

        if not similarities:
            return None, "No policy seeds found in vocabulary"

        # Average similarity to policy terms
        avg_similarity = np.mean(similarities)

        # Max similarity (closest policy term)
        max_similarity = np.max(similarities)
        max_seed = self.policy_seeds[np.argmax(similarities)]

        return {
            'avg_similarity': float(avg_similarity),
            'max_similarity': float(max_similarity),
            'closest_policy_term': max_seed,
            'individual_similarities': {seed: float(sim) for seed, sim in zip(self.policy_seeds, similarities)}
        }, None

    def test_tracked_keywords(self):
        """Test semantic proximity for all tracked keywords"""
        print("\n" + "="*80)
        print("SEMANTIC PROXIMITY FOR TRACKED KEYWORDS")
        print("="*80)

        tracked_terms = [
            'transitory',
            'accommodative',
            'patient',
            'considerable_time',
            'full_range_of_tools'
        ]

        results = []

        for term in tracked_terms:
            print(f"\n{term.upper()}")
            print("-" * 60)

            score, error = self.calculate_proximity_score(term)

            if error:
                print(f"ERROR: {error}")
                results.append({
                    'term': term,
                    'error': error
                })
                continue

            print(f"Average similarity to policy terms: {score['avg_similarity']:.4f}")
            print(f"Closest policy term: '{score['closest_policy_term']}' (sim={score['max_similarity']:.4f})")
            print(f"\nIndividual similarities:")
            for seed, sim in sorted(score['individual_similarities'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {seed:15s} {sim:.4f}")

            results.append({
                'term': term,
                'proximity_score': score
            })

        return results

    def test_response_claim_transitory(self):
        """Test specific claim: 'transitory' scores high due to proximity to 'inflation'"""
        print("\n" + "="*80)
        print("TESTING RESPONSE CLAIM: TRANSITORY-INFLATION PROXIMITY")
        print("="*80)

        term = 'transitory'
        seed = 'inflation'

        if not self.check_word_exists(term):
            print(f"ERROR: '{term}' not in vocabulary")
            return None

        if not self.check_word_exists(seed):
            print(f"ERROR: '{seed}' not in vocabulary")
            return None

        similarity = self.wv.similarity(term, seed)

        print(f"\n'{term}' <-> '{seed}' similarity: {similarity:.4f}")

        # Get overall proximity score
        score, error = self.calculate_proximity_score(term)
        if not error:
            print(f"'{term}' average proximity to policy terms: {score['avg_similarity']:.4f}")
            print(f"'{term}' closest policy term: '{score['closest_policy_term']}' (sim={score['max_similarity']:.4f})")

            # Validate claim
            is_high = score['avg_similarity'] > 0.3  # Threshold for "high" proximity
            print(f"\nClaim: 'transitory' scores high proximity to policy terms")
            print(f"Result: {'✓ PASS' if is_high else '✗ FAIL'} (avg_similarity = {score['avg_similarity']:.4f})")

        return {
            'term': term,
            'seed': seed,
            'direct_similarity': float(similarity),
            'overall_proximity': score if not error else None,
            'claim_validated': is_high if not error else None
        }

    def analyze_ground_truth_correlation(self):
        """
        Analyze correlation between semantic proximity and shift significance

        Do shifts with high proximity to policy terms occur more frequently?
        """
        print("\n" + "="*80)
        print("CORRELATION: SEMANTIC PROXIMITY vs SHIFT SIGNIFICANCE")
        print("="*80)

        # Count shifts by term
        shift_counts = defaultdict(int)
        shift_types = defaultdict(lambda: defaultdict(int))

        for shift in self.ground_truth:
            term = shift['term']
            shift_type = shift['type']
            shift_counts[term] += 1
            shift_types[term][shift_type] += 1

        print(f"\nGround truth: {len(self.ground_truth)} total shifts")
        print(f"Unique terms: {len(shift_counts)}")

        # Calculate proximity for each term
        term_proximity = {}
        for term in shift_counts.keys():
            score, error = self.calculate_proximity_score(term)
            if not error:
                term_proximity[term] = score['avg_similarity']

        print(f"Terms with calculable proximity: {len(term_proximity)}")

        # Analyze correlation
        if term_proximity:
            # Sort terms by proximity
            sorted_terms = sorted(term_proximity.items(), key=lambda x: x[1], reverse=True)

            print("\n" + "-"*80)
            print("TERMS RANKED BY SEMANTIC PROXIMITY TO POLICY CONCEPTS")
            print("-"*80)
            print(f"{'Term':<25s} {'Proximity':<12s} {'# Shifts':<12s} {'Types'}")
            print("-"*80)

            results = []
            for term, proximity in sorted_terms:
                num_shifts = shift_counts[term]
                types = shift_types[term]
                type_str = ", ".join(f"{k}:{v}" for k, v in types.items())

                print(f"{term:<25s} {proximity:>6.4f}       {num_shifts:>6d}       {type_str}")

                results.append({
                    'term': term,
                    'proximity_score': proximity,
                    'num_shifts': num_shifts,
                    'shift_types': dict(types)
                })

            # Calculate correlation coefficient
            proximities = [term_proximity[term] for term in shift_counts.keys() if term in term_proximity]
            shift_freqs = [shift_counts[term] for term in shift_counts.keys() if term in term_proximity]

            if len(proximities) > 1:
                correlation = np.corrcoef(proximities, shift_freqs)[0, 1]
                print(f"\nCorrelation coefficient: {correlation:.4f}")

                if abs(correlation) > 0.5:
                    print(f"Result: ✓ Strong correlation (|r| > 0.5)")
                elif abs(correlation) > 0.3:
                    print(f"Result: ~ Moderate correlation (|r| > 0.3)")
                else:
                    print(f"Result: ✗ Weak correlation (|r| < 0.3)")
            else:
                correlation = None
                print("\nInsufficient data for correlation analysis")

            return {
                'terms_analyzed': results,
                'correlation_coefficient': float(correlation) if correlation is not None else None,
                'interpretation': 'strong' if correlation and abs(correlation) > 0.5 else
                                'moderate' if correlation and abs(correlation) > 0.3 else
                                'weak'
            }

        return None

    def compare_high_vs_low_proximity(self):
        """Compare shifts between high and low proximity terms"""
        print("\n" + "="*80)
        print("COMPARISON: HIGH vs LOW PROXIMITY TERMS")
        print("="*80)

        # Calculate proximity for all unique terms
        unique_terms = set(shift['term'] for shift in self.ground_truth)

        term_proximity = {}
        for term in unique_terms:
            score, error = self.calculate_proximity_score(term)
            if not error:
                term_proximity[term] = score['avg_similarity']

        if not term_proximity:
            print("No terms with calculable proximity")
            return None

        # Define threshold (median proximity)
        median_proximity = np.median(list(term_proximity.values()))
        print(f"Median proximity: {median_proximity:.4f}")

        # Classify terms
        high_proximity_terms = [t for t, p in term_proximity.items() if p >= median_proximity]
        low_proximity_terms = [t for t, p in term_proximity.items() if p < median_proximity]

        print(f"\nHigh proximity terms (>= {median_proximity:.4f}): {len(high_proximity_terms)}")
        print(f"Low proximity terms (< {median_proximity:.4f}): {len(low_proximity_terms)}")

        # Count shifts in each category
        high_proximity_shifts = [s for s in self.ground_truth if s['term'] in high_proximity_terms]
        low_proximity_shifts = [s for s in self.ground_truth if s['term'] in low_proximity_terms]

        print(f"\nShifts from high proximity terms: {len(high_proximity_shifts)}")
        print(f"Shifts from low proximity terms: {len(low_proximity_shifts)}")

        # Average shifts per term
        avg_shifts_high = len(high_proximity_shifts) / len(high_proximity_terms) if high_proximity_terms else 0
        avg_shifts_low = len(low_proximity_shifts) / len(low_proximity_terms) if low_proximity_terms else 0

        print(f"\nAverage shifts per term:")
        print(f"  High proximity: {avg_shifts_high:.2f}")
        print(f"  Low proximity: {avg_shifts_low:.2f}")

        if avg_shifts_high > avg_shifts_low * 1.5:
            print(f"Result: ✓ High proximity terms show more shifts")
        elif avg_shifts_low > avg_shifts_high * 1.5:
            print(f"Result: ✗ Low proximity terms show more shifts")
        else:
            print(f"Result: ~ No clear difference")

        return {
            'median_proximity': float(median_proximity),
            'high_proximity_terms': high_proximity_terms,
            'low_proximity_terms': low_proximity_terms,
            'high_proximity_shifts': len(high_proximity_shifts),
            'low_proximity_shifts': len(low_proximity_shifts),
            'avg_shifts_per_term_high': avg_shifts_high,
            'avg_shifts_per_term_low': avg_shifts_low
        }


def main():
    """Main execution"""
    print("Semantic Proximity Testing")
    print("=" * 80)

    # Configuration
    model_path = "/mnt/c/python/FedSpeak/prototypes/results/fed_word2vec.model"
    ground_truth_path = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"
    output_dir = "/mnt/c/python/FedSpeak/prototypes/results"

    # Check if model exists
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        print("Please run word2vec_training.py first")
        return

    # Initialize tester
    print("\nLoading Word2Vec model and ground truth...")
    tester = SemanticProximityTester(model_path, ground_truth_path)
    print(f"Vocabulary size: {len(tester.wv):,} words")
    print(f"Ground truth shifts: {len(tester.ground_truth)}")
    print(f"Policy seed terms: {', '.join(tester.policy_seeds)}")

    # Test 1: Tracked keywords proximity
    tracked_results = tester.test_tracked_keywords()

    # Test 2: Response claim validation
    transitory_claim = tester.test_response_claim_transitory()

    # Test 3: Correlation analysis
    correlation_results = tester.analyze_ground_truth_correlation()

    # Test 4: High vs low proximity comparison
    comparison_results = tester.compare_high_vs_low_proximity()

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'model_path': model_path,
        'policy_seeds': tester.policy_seeds,
        'tracked_keywords': tracked_results,
        'transitory_claim_test': transitory_claim,
        'correlation_analysis': correlation_results,
        'high_vs_low_comparison': comparison_results
    }

    results_path = os.path.join(output_dir, 'semantic_proximity_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {results_path}")

    # Summary
    print("\n" + "="*80)
    print("SEMANTIC PROXIMITY SUMMARY")
    print("="*80)
    if correlation_results and correlation_results['correlation_coefficient'] is not None:
        print(f"Correlation (proximity vs shift frequency): {correlation_results['correlation_coefficient']:.4f}")
        print(f"Interpretation: {correlation_results['interpretation']}")
    if comparison_results:
        print(f"\nHigh proximity terms: {comparison_results['avg_shifts_per_term_high']:.2f} shifts/term")
        print(f"Low proximity terms: {comparison_results['avg_shifts_per_term_low']:.2f} shifts/term")

    return results


if __name__ == "__main__":
    main()
