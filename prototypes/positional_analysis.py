#!/usr/bin/env python3
"""
Positional Weighting Analysis
==============================

Tests Response 1 & 2 claims about positional importance:
- Response 2: "Assign higher score if term appears in first 25% of statement"
- Response 1: "First paragraph terms weighted 2x"

Tests:
1. Do significant terms actually appear earlier in statements?
2. Calculate correlation between position and significance
3. Validate 2x weighting claim

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import csv
import json
import glob
from datetime import datetime
import numpy as np
from collections import defaultdict


class PositionalAnalyzer:
    """Analyze positional patterns of keyword shifts"""

    def __init__(self, corpus_dir, ground_truth_path):
        self.corpus_dir = corpus_dir
        self.ground_truth = self.load_ground_truth(ground_truth_path)
        self.statements = self.load_statements()

    def load_ground_truth(self, path):
        """Load ground truth shifts"""
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

    def load_statements(self):
        """Load all policy statements"""
        pattern = os.path.join(self.corpus_dir, "policy_statement_*.txt")
        files = sorted(glob.glob(pattern))

        statements = {}
        for filepath in files:
            filename = os.path.basename(filepath)
            date_str = filename.replace("policy_statement_", "").replace(".txt", "")

            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            statements[date_str] = {
                'text': text,
                'filepath': filepath
            }

        return statements

    def find_first_occurrence_position(self, text, term):
        """
        Find first occurrence position of term in text

        Returns:
        - char_position: Character position of first occurrence
        - paragraph_num: Paragraph number (1-indexed)
        - relative_position: Position as fraction of document (0.0 to 1.0)
        - word_position: Word position (0-indexed)
        """
        text_lower = text.lower()
        term_lower = term.replace('_', ' ').lower()

        # Find character position
        char_pos = text_lower.find(term_lower)
        if char_pos == -1:
            return None  # Term not found

        # Calculate relative position
        total_chars = len(text)
        relative_pos = char_pos / total_chars if total_chars > 0 else 0

        # Find paragraph number (split by double newlines)
        paragraphs = text[:char_pos].split('\n\n')
        paragraph_num = len(paragraphs)

        # Find word position
        words_before = text[:char_pos].split()
        word_pos = len(words_before)

        total_words = len(text.split())

        return {
            'char_position': char_pos,
            'total_chars': total_chars,
            'relative_position': relative_pos,
            'paragraph_number': paragraph_num,
            'word_position': word_pos,
            'total_words': total_words,
            'relative_word_position': word_pos / total_words if total_words > 0 else 0
        }

    def analyze_shift_positions(self):
        """Analyze positions of all ground truth shifts"""
        print("\n" + "="*80)
        print("POSITIONAL ANALYSIS OF GROUND TRUTH SHIFTS")
        print("="*80)

        results = []
        positions_found = []
        positions_not_found = []

        for shift in self.ground_truth:
            date = shift['date']
            term = shift['term']
            shift_type = shift['type']

            # Find corresponding statement
            if date not in self.statements:
                print(f"WARNING: No statement found for {date}")
                continue

            statement = self.statements[date]
            text = statement['text']

            # Find position
            position = self.find_first_occurrence_position(text, term)

            result = {
                'date': date,
                'term': term,
                'type': shift_type,
                'position': position
            }

            results.append(result)

            if position:
                positions_found.append(position['relative_position'])
            else:
                positions_not_found.append(term)

        print(f"\nTotal shifts analyzed: {len(results)}")
        print(f"Positions found: {len(positions_found)}")
        print(f"Not found (likely removals): {len(positions_not_found)}")

        return results, positions_found, positions_not_found

    def test_first_quarter_claim(self, positions):
        """Test Response 2 claim: Terms appear in first 25% of statement"""
        print("\n" + "="*80)
        print("TESTING CLAIM: TERMS APPEAR IN FIRST 25%")
        print("="*80)

        if not positions:
            print("No position data available")
            return None

        # Count positions in each quartile
        quartiles = {
            'first_quarter': sum(1 for p in positions if p <= 0.25),
            'second_quarter': sum(1 for p in positions if 0.25 < p <= 0.50),
            'third_quarter': sum(1 for p in positions if 0.50 < p <= 0.75),
            'fourth_quarter': sum(1 for p in positions if p > 0.75)
        }

        total = len(positions)

        print(f"\nDistribution across document:")
        print(f"  First quarter  (0-25%):  {quartiles['first_quarter']:4d} ({quartiles['first_quarter']/total*100:5.1f}%)")
        print(f"  Second quarter (25-50%): {quartiles['second_quarter']:4d} ({quartiles['second_quarter']/total*100:5.1f}%)")
        print(f"  Third quarter  (50-75%): {quartiles['third_quarter']:4d} ({quartiles['third_quarter']/total*100:5.1f}%)")
        print(f"  Fourth quarter (75-100%):{quartiles['fourth_quarter']:4d} ({quartiles['fourth_quarter']/total*100:5.1f}%)")

        # Test claim: More than 50% in first quarter?
        first_quarter_pct = quartiles['first_quarter'] / total
        claim_threshold = 0.50  # More than 50% in first quarter

        print(f"\nClaim: Significant terms appear in first 25% of document")
        print(f"Result: {first_quarter_pct*100:.1f}% of terms in first quarter")

        if first_quarter_pct >= claim_threshold:
            print(f"Validation: ✓ PASS (>= {claim_threshold*100:.0f}% in first quarter)")
        else:
            print(f"Validation: ✗ FAIL (< {claim_threshold*100:.0f}% in first quarter)")

        # Calculate mean and median position
        mean_pos = np.mean(positions)
        median_pos = np.median(positions)

        print(f"\nPosition statistics:")
        print(f"  Mean position: {mean_pos:.3f} ({mean_pos*100:.1f}% through document)")
        print(f"  Median position: {median_pos:.3f} ({median_pos*100:.1f}% through document)")

        return {
            'quartile_distribution': quartiles,
            'first_quarter_percentage': first_quarter_pct,
            'claim_validated': first_quarter_pct >= claim_threshold,
            'mean_position': float(mean_pos),
            'median_position': float(median_pos),
            'total_positions': total
        }

    def test_2x_weighting_claim(self, results):
        """
        Test Response 1 claim: First paragraph terms should be weighted 2x

        Approach: Compare shift frequency between first paragraph vs rest
        If first paragraph terms are 2x more important, they should show
        more shifts per occurrence.
        """
        print("\n" + "="*80)
        print("TESTING CLAIM: FIRST PARAGRAPH 2X WEIGHTING")
        print("="*80)

        # Separate results by paragraph
        first_paragraph = [r for r in results if r['position'] and r['position']['paragraph_number'] == 1]
        later_paragraphs = [r for r in results if r['position'] and r['position']['paragraph_number'] > 1]

        print(f"\nShifts by paragraph:")
        print(f"  First paragraph: {len(first_paragraph)}")
        print(f"  Later paragraphs: {len(later_paragraphs)}")

        if not first_paragraph or not later_paragraphs:
            print("Insufficient data for comparison")
            return None

        # Calculate ratio
        total = len(first_paragraph) + len(later_paragraphs)
        first_pct = len(first_paragraph) / total
        later_pct = len(later_paragraphs) / total

        print(f"\nPercentage distribution:")
        print(f"  First paragraph: {first_pct*100:.1f}%")
        print(f"  Later paragraphs: {later_pct*100:.1f}%")

        # Test 2x claim
        ratio = first_pct / later_pct if later_pct > 0 else float('inf')

        print(f"\nRatio (first / later): {ratio:.2f}x")

        if ratio >= 2.0:
            print(f"Validation: ✓ PASS (ratio >= 2.0x)")
        elif ratio >= 1.5:
            print(f"Validation: ~ PARTIAL (ratio >= 1.5x)")
        else:
            print(f"Validation: ✗ FAIL (ratio < 1.5x)")

        return {
            'first_paragraph_shifts': len(first_paragraph),
            'later_paragraph_shifts': len(later_paragraphs),
            'first_paragraph_percentage': first_pct,
            'ratio': float(ratio),
            'claim_validated': ratio >= 2.0
        }

    def analyze_by_shift_type(self, results):
        """Analyze positional patterns by shift type (emergence vs removal)"""
        print("\n" + "="*80)
        print("POSITIONAL ANALYSIS BY SHIFT TYPE")
        print("="*80)

        # Group by type
        by_type = defaultdict(list)
        for result in results:
            if result['position']:
                by_type[result['type']].append(result['position']['relative_position'])

        print(f"\nShift types analyzed: {len(by_type)}")

        type_stats = {}
        for shift_type, positions in by_type.items():
            if positions:
                mean_pos = np.mean(positions)
                median_pos = np.median(positions)
                first_quarter = sum(1 for p in positions if p <= 0.25) / len(positions)

                print(f"\n{shift_type.upper()}:")
                print(f"  Count: {len(positions)}")
                print(f"  Mean position: {mean_pos:.3f} ({mean_pos*100:.1f}%)")
                print(f"  Median position: {median_pos:.3f} ({median_pos*100:.1f}%)")
                print(f"  In first quarter: {first_quarter*100:.1f}%")

                type_stats[shift_type] = {
                    'count': len(positions),
                    'mean_position': float(mean_pos),
                    'median_position': float(median_pos),
                    'first_quarter_percentage': float(first_quarter)
                }

        return type_stats

    def analyze_by_term(self, results):
        """Analyze positional patterns by term"""
        print("\n" + "="*80)
        print("POSITIONAL ANALYSIS BY TERM")
        print("="*80)

        # Group by term
        by_term = defaultdict(list)
        for result in results:
            if result['position']:
                by_term[result['term']].append(result['position']['relative_position'])

        # Sort by number of occurrences
        sorted_terms = sorted(by_term.items(), key=lambda x: len(x[1]), reverse=True)

        print(f"\nTerms analyzed: {len(sorted_terms)}")
        print(f"\n{'Term':<25s} {'Count':>6s} {'Mean':>8s} {'Median':>8s} {'1st Q':>6s}")
        print("-" * 80)

        term_stats = {}
        for term, positions in sorted_terms[:15]:  # Top 15
            mean_pos = np.mean(positions)
            median_pos = np.median(positions)
            first_q = sum(1 for p in positions if p <= 0.25) / len(positions)

            print(f"{term:<25s} {len(positions):>6d} {mean_pos:>7.3f} {median_pos:>7.3f} {first_q*100:>5.1f}%")

            term_stats[term] = {
                'count': len(positions),
                'mean_position': float(mean_pos),
                'median_position': float(median_pos),
                'first_quarter_percentage': float(first_q)
            }

        return term_stats


def main():
    """Main execution"""
    print("Positional Analysis of Keyword Shifts")
    print("=" * 80)

    # Configuration
    corpus_dir = "/mnt/c/python/FedSpeak/data/processed"
    ground_truth_path = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"
    output_dir = "/mnt/c/python/FedSpeak/prototypes/results"

    # Initialize analyzer
    print("\nLoading corpus and ground truth...")
    analyzer = PositionalAnalyzer(corpus_dir, ground_truth_path)
    print(f"Statements loaded: {len(analyzer.statements)}")
    print(f"Ground truth shifts: {len(analyzer.ground_truth)}")

    # Analyze positions
    results, positions_found, positions_not_found = analyzer.analyze_shift_positions()

    # Test first quarter claim
    first_quarter_results = analyzer.test_first_quarter_claim(positions_found)

    # Test 2x weighting claim
    weighting_results = analyzer.test_2x_weighting_claim(results)

    # Analyze by shift type
    type_stats = analyzer.analyze_by_shift_type(results)

    # Analyze by term
    term_stats = analyzer.analyze_by_term(results)

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_shifts_analyzed': len(results),
        'positions_found': len(positions_found),
        'positions_not_found': len(positions_not_found),
        'all_shift_positions': results,
        'first_quarter_analysis': first_quarter_results,
        'weighting_analysis': weighting_results,
        'by_shift_type': type_stats,
        'by_term': term_stats
    }

    results_path = os.path.join(output_dir, 'positional_analysis_results.json')
    with open(results_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {results_path}")

    # Summary
    print("\n" + "="*80)
    print("POSITIONAL ANALYSIS SUMMARY")
    print("="*80)
    if first_quarter_results:
        print(f"Terms in first 25%: {first_quarter_results['first_quarter_percentage']*100:.1f}%")
        print(f"Mean position: {first_quarter_results['mean_position']*100:.1f}% through document")
        print(f"First quarter claim: {'✓ VALIDATED' if first_quarter_results['claim_validated'] else '✗ NOT VALIDATED'}")
    if weighting_results:
        print(f"\nFirst paragraph ratio: {weighting_results['ratio']:.2f}x")
        print(f"2x weighting claim: {'✓ VALIDATED' if weighting_results['claim_validated'] else '✗ NOT VALIDATED'}")

    return output


if __name__ == "__main__":
    main()
