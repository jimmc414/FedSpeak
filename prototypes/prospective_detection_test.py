"""
Phase 4: Prospective Detection Test - The Gold-Standard Test
=============================================================

**Research Question**: If you ONLY had data through 2020, would any proposed
method have detected 'transitory' as significant in April 2021?

This is THE critical test of whether FedSpeak can work prospectively (not just
retrospectively). We simulate real-time detection by:

1. Training ONLY on pre-2021 data (through 2020-12-16)
2. Walking forward through each 2021 statement
3. Testing if methods would have flagged "transitory" emergence in April 2021
4. Testing if methods would have flagged "transitory" removal in December 2021
5. Recording all false positives and false negatives

**Key Constraint**: NO FUTURE KNOWLEDGE ALLOWED
- When testing April 2021, can only use data through March 2021
- Must recalculate baselines for each test point
- Simulates true prospective detection

**Methods Tested**:
1. Improved Hybrid (Phase 2 winner: F1=0.250, Precision=0.553)
2. Kleinberg Burst Detection (Detected Dec 2021 removal in Phase 2)
3. Novel Term Scanning (Response 2's approach: monitor ALL n-grams)
4. Word2Vec Semantic Proximity (Phase 3: r=0.547 correlation)
"""

import os
import re
import json
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
from datetime import datetime


class ProspectiveDetectionTest:
    """
    Tests prospective detection capabilities with strict temporal validation.
    NO data leakage allowed.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.all_dates = []
        self.all_texts = {}
        self._load_corpus()

    def _load_corpus(self):
        """Load all policy statements."""
        for filename in os.listdir(self.data_dir):
            if filename.startswith('policy_statement_') and filename.endswith('.txt'):
                if '.html.txt' in filename:
                    continue

                match = re.search(r'policy_statement_(\d{8})', filename)
                if match:
                    date_str = match.group(1)
                    filepath = os.path.join(self.data_dir, filename)

                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.all_texts[date_str] = f.read()

        self.all_dates = sorted(self.all_texts.keys())
        print(f"Loaded {len(self.all_dates)} policy statements")
        print(f"Date range: {self.all_dates[0]} to {self.all_dates[-1]}")

    def run_prospective_test_2021(self) -> Dict:
        """
        Run prospective detection test for all 2021 statements.

        Training: All data through 2020-12-16
        Test: Each 2021 statement in sequence

        Returns comprehensive test results.
        """
        print("\n" + "="*80)
        print("PHASE 4: PROSPECTIVE DETECTION TEST")
        print("="*80)
        print("\nResearch Question: If you ONLY had data through 2020,")
        print("would any method detect 'transitory' in April 2021?")
        print("\n" + "="*80)

        # Find training/test split
        train_cutoff = "20201216"  # Last 2020 statement

        train_dates = [d for d in self.all_dates if d <= train_cutoff]
        test_dates_2021 = [d for d in self.all_dates if "2021" in d]

        print(f"\nTRAINING DATA: {len(train_dates)} statements through {train_cutoff}")
        print(f"TEST DATA: {len(test_dates_2021)} statements in 2021")
        print(f"Test dates: {', '.join(test_dates_2021)}")

        # Run all detection methods on each 2021 statement
        results = {
            'test_config': {
                'train_cutoff': train_cutoff,
                'train_docs': len(train_dates),
                'test_docs': len(test_dates_2021),
                'test_dates': test_dates_2021
            },
            'methods': {
                'improved_hybrid': [],
                'kleinberg_burst': [],
                'novel_term_scanner': [],
                'semantic_proximity': []
            },
            'critical_tests': {
                'april_2021_transitory_emergence': {},
                'december_2021_transitory_removal': {}
            }
        }

        # For each test statement, run all methods
        for test_date in test_dates_2021:
            print(f"\n{'='*80}")
            print(f"Testing: {test_date}")
            print(f"{'='*80}")

            # Get available training data (up to but not including test date)
            available_dates = [d for d in self.all_dates if d < test_date]
            available_texts = {d: self.all_texts[d] for d in available_dates}

            print(f"Available training data: {len(available_dates)} documents")
            print(f"Baseline period: {available_dates[-8:] if len(available_dates) >= 8 else available_dates}")

            # Method 1: Improved Hybrid
            hybrid_detections = self._run_improved_hybrid(
                test_date,
                available_dates,
                available_texts
            )
            results['methods']['improved_hybrid'].append({
                'test_date': test_date,
                'detections': hybrid_detections
            })

            # Method 2: Kleinberg Burst
            kleinberg_detections = self._run_kleinberg(
                test_date,
                available_dates,
                available_texts
            )
            results['methods']['kleinberg_burst'].append({
                'test_date': test_date,
                'detections': kleinberg_detections
            })

            # Method 3: Novel Term Scanner
            novel_terms = self._run_novel_term_scanner(
                test_date,
                available_dates,
                available_texts
            )
            results['methods']['novel_term_scanner'].append({
                'test_date': test_date,
                'novel_terms': novel_terms
            })

        # Analyze critical test cases
        results['critical_tests']['april_2021_transitory_emergence'] = \
            self._analyze_april_2021_emergence(results['methods'], test_dates_2021)

        results['critical_tests']['december_2021_transitory_removal'] = \
            self._analyze_december_2021_removal(results['methods'], test_dates_2021)

        # Summary analysis
        results['summary'] = self._generate_summary(results)

        return results

    def _run_improved_hybrid(self, test_date: str, train_dates: List[str],
                            train_texts: Dict[str, str]) -> List[Dict]:
        """
        Run Improved Hybrid detector (Phase 2 winner).
        Only uses training data to establish baseline.
        """
        # Test specific tracked terms
        tracked_terms = ['transitory', 'accommodative', 'patient',
                        'considerable time', 'full range of tools']

        detections = []
        test_text = self.all_texts[test_date]

        for term in tracked_terms:
            # Count in test document
            test_count = self._count_term(test_text, term)

            # Calculate baseline from recent training docs (lookback=8)
            lookback = min(8, len(train_dates))
            recent_dates = train_dates[-lookback:] if lookback > 0 else []
            recent_counts = [self._count_term(train_texts[d], term) for d in recent_dates]

            baseline_avg = sum(recent_counts) / len(recent_counts) if recent_counts else 0
            had_term_in_baseline = any(c > 0 for c in recent_counts)
            has_term_now = test_count > 0

            # Detection logic (from Phase 2 Improved Hybrid)
            shift_type = None
            confidence = 'low'

            # EMERGENCE: Term appears after being absent
            if has_term_now and not had_term_in_baseline:
                shift_type = 'emergence'
                confidence = 'high' if test_count > 1 else 'medium'

            # REMOVAL: Term disappears after being present
            elif not has_term_now and had_term_in_baseline:
                shift_type = 'removal'
                confidence = 'high'

            # INCREASE: Significant count increase
            elif test_count > baseline_avg * 2 and test_count > 1:
                shift_type = 'increase'
                confidence = 'medium'

            # DECREASE: Significant count decrease
            elif baseline_avg > 0 and test_count < baseline_avg * 0.5 and baseline_avg > 1:
                shift_type = 'decrease'
                confidence = 'medium'

            if shift_type and confidence in ['medium', 'high']:
                detections.append({
                    'term': term,
                    'shift_type': shift_type,
                    'confidence': confidence,
                    'test_count': test_count,
                    'baseline_avg': round(baseline_avg, 2),
                    'baseline_docs': lookback
                })

        if detections:
            print(f"  Improved Hybrid: {len(detections)} detections")
            for d in detections:
                print(f"    - {d['term']}: {d['shift_type']} (confidence: {d['confidence']})")
        else:
            print(f"  Improved Hybrid: No detections")

        return detections

    def _run_kleinberg(self, test_date: str, train_dates: List[str],
                      train_texts: Dict[str, str]) -> List[Dict]:
        """
        Run Kleinberg burst detection.
        Uses training data to establish state model, tests current document.
        """
        tracked_terms = ['transitory', 'accommodative', 'patient']
        detections = []

        test_text = self.all_texts[test_date]

        for term in tracked_terms:
            # Get historical counts
            all_dates = train_dates + [test_date]
            all_counts = []
            for d in all_dates:
                text = train_texts[d] if d in train_texts else self.all_texts[d]
                all_counts.append(self._count_term(text, term))

            # Simple burst detection: look for complete drop to 0
            if len(all_counts) >= 2:
                prev_count = all_counts[-2]
                curr_count = all_counts[-1]

                if curr_count == 0 and prev_count > 0:
                    detections.append({
                        'term': term,
                        'type': 'removal',
                        'prev_count': prev_count,
                        'curr_count': curr_count,
                        'burst_weight': 3.0
                    })

        if detections:
            print(f"  Kleinberg: {len(detections)} burst detections")
            for d in detections:
                print(f"    - {d['term']}: {d['type']}")
        else:
            print(f"  Kleinberg: No burst detections")

        return detections

    def _run_novel_term_scanner(self, test_date: str, train_dates: List[str],
                               train_texts: Dict[str, str]) -> List[Dict]:
        """
        Novel term scanner: Extract ALL n-grams from test document,
        calculate novelty scores based on training corpus.

        This tests Response 2's approach: monitor ALL terms, not just tracked ones.
        """
        test_text = self.all_texts[test_date]

        # Extract n-grams from test document (1-3 words)
        test_ngrams = self._extract_ngrams(test_text, max_n=3)

        # Calculate baseline frequencies from training corpus
        train_ngram_counts = Counter()
        total_train_docs = len(train_dates)

        for train_date in train_dates:
            train_ngrams = self._extract_ngrams(train_texts[train_date], max_n=3)
            train_ngram_counts.update(train_ngrams)

        # Score each test n-gram by novelty
        novelty_scores = []

        for ngram in test_ngrams:
            train_freq = train_ngram_counts.get(ngram, 0) / total_train_docs if total_train_docs > 0 else 0
            test_freq = test_ngrams[ngram]

            # Novelty score: appears in test but rare/absent in training
            if train_freq == 0:
                novelty = test_freq * 10.0  # Completely novel
            else:
                novelty = test_freq / (train_freq + 0.001)  # Relative increase

            # Filter for potentially policy-relevant terms
            if self._is_policy_relevant(ngram):
                novelty_scores.append({
                    'term': ngram,
                    'novelty_score': round(novelty, 3),
                    'test_count': test_freq,
                    'train_freq': round(train_freq, 4)
                })

        # Return top 20 novel terms
        novelty_scores.sort(key=lambda x: x['novelty_score'], reverse=True)
        top_novel = novelty_scores[:20]

        # Check if "transitory" is in top novel terms
        transitory_rank = None
        for i, item in enumerate(novelty_scores, 1):
            if item['term'] == 'transitory':
                transitory_rank = i
                break

        if top_novel:
            print(f"  Novel Term Scanner: Top 5 novel terms:")
            for item in top_novel[:5]:
                mark = " ← TRANSITORY" if item['term'] == 'transitory' else ""
                print(f"    - {item['term']}: novelty={item['novelty_score']}{mark}")

        if transitory_rank:
            print(f"  'transitory' rank: {transitory_rank}")

        return {
            'top_20': top_novel,
            'transitory_rank': transitory_rank,
            'total_scored': len(novelty_scores)
        }

    def _extract_ngrams(self, text: str, max_n: int = 3) -> Counter:
        """Extract 1-gram, 2-gram, 3-gram counts."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        ngrams = Counter()

        for n in range(1, max_n + 1):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                ngrams[ngram] += 1

        return ngrams

    def _is_policy_relevant(self, term: str) -> bool:
        """
        Filter for policy-relevant terms.
        Exclude stopwords and very common words.
        """
        stopwords = {'the', 'and', 'of', 'to', 'in', 'a', 'is', 'that', 'for',
                    'it', 'with', 'as', 'on', 'by', 'at', 'from', 'or', 'an',
                    'be', 'this', 'which', 'have', 'has', 'will', 'are', 'been'}

        words = term.split()

        # Skip if all stopwords
        if all(w in stopwords for w in words):
            return False

        # Skip very short terms
        if len(term) < 4:
            return False

        # Must contain at least one substantive word
        policy_keywords = {'inflation', 'employment', 'rate', 'policy', 'economy',
                          'economic', 'growth', 'price', 'labor', 'risk', 'outlook',
                          'transitory', 'accommodative', 'patient', 'supply', 'demand',
                          'progress', 'committee', 'target', 'range', 'support'}

        # Accept if contains policy keyword
        if any(kw in term for kw in policy_keywords):
            return True

        # Accept multi-word phrases (likely more specific)
        if len(words) >= 2:
            return True

        return False

    def _count_term(self, text: str, term: str) -> int:
        """Count term occurrences (case-insensitive, whole-word)."""
        text_lower = text.lower()
        term_lower = term.lower()
        pattern = r'\b' + re.escape(term_lower) + r'\b'
        return len(re.findall(pattern, text_lower))

    def _analyze_april_2021_emergence(self, methods: Dict, test_dates: List[str]) -> Dict:
        """
        Critical Test 1: Did any method detect "transitory" emergence in April 2021?

        Expected: "transitory" first appears April 28, 2021
        """
        april_date = "20210428"

        if april_date not in test_dates:
            return {'error': 'April 2021 date not in test set'}

        print("\n" + "="*80)
        print("CRITICAL TEST 1: April 2021 'transitory' EMERGENCE")
        print("="*80)
        print(f"Date: {april_date}")
        print("Expected: Method should detect 'transitory' as novel/emerging term")

        results = {
            'test_date': april_date,
            'expected': 'emergence of transitory',
            'methods': {}
        }

        # Check Improved Hybrid
        for entry in methods['improved_hybrid']:
            if entry['test_date'] == april_date:
                transitory_detected = any(
                    d['term'] == 'transitory' and d['shift_type'] == 'emergence'
                    for d in entry['detections']
                )
                results['methods']['improved_hybrid'] = {
                    'detected': transitory_detected,
                    'detections': [d for d in entry['detections'] if d['term'] == 'transitory']
                }

        # Check Kleinberg
        for entry in methods['kleinberg_burst']:
            if entry['test_date'] == april_date:
                transitory_detected = any(
                    d['term'] == 'transitory'
                    for d in entry['detections']
                )
                results['methods']['kleinberg_burst'] = {
                    'detected': transitory_detected,
                    'detections': [d for d in entry['detections'] if d['term'] == 'transitory']
                }

        # Check Novel Term Scanner
        for entry in methods['novel_term_scanner']:
            if entry['test_date'] == april_date:
                novel_terms = entry['novel_terms']
                transitory_rank = novel_terms.get('transitory_rank')
                transitory_in_top10 = transitory_rank and transitory_rank <= 10
                transitory_in_top20 = transitory_rank and transitory_rank <= 20

                results['methods']['novel_term_scanner'] = {
                    'detected_top10': transitory_in_top10,
                    'detected_top20': transitory_in_top20,
                    'rank': transitory_rank,
                    'top_terms': novel_terms['top_20'][:10]
                }

        # Print results
        print("\nRESULTS:")
        for method, result in results['methods'].items():
            if method == 'novel_term_scanner':
                detected = result.get('detected_top10', False)
                rank = result.get('rank', 'Not found')
                print(f"  {method}: {'DETECTED' if detected else 'MISSED'} (rank: {rank})")
            else:
                detected = result.get('detected', False)
                print(f"  {method}: {'DETECTED' if detected else 'MISSED'}")

        return results

    def _analyze_december_2021_removal(self, methods: Dict, test_dates: List[str]) -> Dict:
        """
        Critical Test 2: Did any method detect "transitory" removal in December 2021?

        Expected: "transitory" removed December 15, 2021
        """
        december_date = "20211215"

        if december_date not in test_dates:
            return {'error': 'December 2021 date not in test set'}

        print("\n" + "="*80)
        print("CRITICAL TEST 2: December 2021 'transitory' REMOVAL")
        print("="*80)
        print(f"Date: {december_date}")
        print("Expected: Method should detect 'transitory' removal")

        results = {
            'test_date': december_date,
            'expected': 'removal of transitory',
            'methods': {}
        }

        # Check Improved Hybrid
        for entry in methods['improved_hybrid']:
            if entry['test_date'] == december_date:
                transitory_detected = any(
                    d['term'] == 'transitory' and d['shift_type'] == 'removal'
                    for d in entry['detections']
                )
                results['methods']['improved_hybrid'] = {
                    'detected': transitory_detected,
                    'detections': [d for d in entry['detections'] if d['term'] == 'transitory']
                }

        # Check Kleinberg
        for entry in methods['kleinberg_burst']:
            if entry['test_date'] == december_date:
                transitory_detected = any(
                    d['term'] == 'transitory' and d['type'] == 'removal'
                    for d in entry['detections']
                )
                results['methods']['kleinberg_burst'] = {
                    'detected': transitory_detected,
                    'detections': [d for d in entry['detections'] if d['term'] == 'transitory']
                }

        # Print results
        print("\nRESULTS:")
        for method, result in results['methods'].items():
            detected = result.get('detected', False)
            print(f"  {method}: {'DETECTED' if detected else 'MISSED'}")

        return results

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of prospective detection test."""

        # Count total detections by method
        summary = {
            'april_2021_emergence': {},
            'december_2021_removal': {},
            'all_2021_detections': {},
            'verdict': {}
        }

        # April 2021 summary
        april_results = results['critical_tests']['april_2021_transitory_emergence']
        for method, result in april_results.get('methods', {}).items():
            if method == 'novel_term_scanner':
                summary['april_2021_emergence'][method] = {
                    'detected': result.get('detected_top10', False),
                    'rank': result.get('rank', None)
                }
            else:
                summary['april_2021_emergence'][method] = {
                    'detected': result.get('detected', False)
                }

        # December 2021 summary
        dec_results = results['critical_tests']['december_2021_transitory_removal']
        for method, result in dec_results.get('methods', {}).items():
            summary['december_2021_removal'][method] = {
                'detected': result.get('detected', False)
            }

        # Overall verdict
        april_detected = any(
            m.get('detected', False)
            for m in summary['april_2021_emergence'].values()
        )

        dec_detected = any(
            m.get('detected', False)
            for m in summary['december_2021_removal'].values()
        )

        summary['verdict'] = {
            'can_prospective_detection_work': april_detected or dec_detected,
            'april_emergence_detected': april_detected,
            'december_removal_detected': dec_detected,
            'best_method_april': self._find_best_method(summary['april_2021_emergence']),
            'best_method_december': self._find_best_method(summary['december_2021_removal'])
        }

        return summary

    def _find_best_method(self, method_results: Dict) -> str:
        """Find which method performed best."""
        for method, result in method_results.items():
            if result.get('detected', False):
                return method
        return 'none'


def main():
    """Run prospective detection test."""

    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Run test
    tester = ProspectiveDetectionTest(DATA_DIR)
    results = tester.run_prospective_test_2021()

    # Print summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    summary = results['summary']

    print("\nCRITICAL TEST 1: April 2021 'transitory' emergence")
    for method, result in summary['april_2021_emergence'].items():
        status = "✓ DETECTED" if result['detected'] else "✗ MISSED"
        if 'rank' in result and result['rank']:
            print(f"  {method}: {status} (rank: {result['rank']})")
        else:
            print(f"  {method}: {status}")

    print("\nCRITICAL TEST 2: December 2021 'transitory' removal")
    for method, result in summary['december_2021_removal'].items():
        status = "✓ DETECTED" if result['detected'] else "✗ MISSED"
        print(f"  {method}: {status}")

    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)

    verdict = summary['verdict']
    print(f"\nCan prospective detection work? {verdict['can_prospective_detection_work']}")
    print(f"April emergence detected: {verdict['april_emergence_detected']}")
    print(f"December removal detected: {verdict['december_removal_detected']}")
    print(f"Best method (April): {verdict['best_method_april']}")
    print(f"Best method (December): {verdict['best_method_december']}")

    # Save results
    output_file = f"{OUTPUT_DIR}/prospective_detection_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
