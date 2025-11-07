"""
Master Test Runner for Statistical Detection Methods
======================================================

Runs all three statistical methods and produces comprehensive comparison:
1. Kleinberg Burst Detection
2. G-test / Log-Likelihood Ratio
3. Jensen-Shannon Divergence

Outputs unified comparison and recommendations.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add prototypes directory to path
sys.path.insert(0, '/mnt/c/python/FedSpeak/prototypes')

import burst_detection_test
import g_test_detection
import jsd_detection


def run_all_tests():
    """Run all three detection methods and compare results."""

    print("="*80)
    print("FEDSPEAK STATISTICAL DETECTION METHODS - COMPREHENSIVE TEST")
    print("="*80)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Configuration
    DATA_DIR = "/mnt/c/python/FedSpeak/data/processed"
    OUTPUT_DIR = "/mnt/c/python/FedSpeak/prototypes/results"
    GROUND_TRUTH = "/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = {
        'test_date': datetime.now().isoformat(),
        'methods': {}
    }

    # ========================================================================
    # TEST 1: KLEINBERG BURST DETECTION
    # ========================================================================
    print("\n\n")
    print("#" * 80)
    print("# METHOD 1: KLEINBERG BURST DETECTION")
    print("#" * 80)

    start_time = time.time()

    try:
        # Critical test: transitory Dec 2021
        burst_transitory = burst_detection_test.test_transitory_december_2021(DATA_DIR)

        # Additional terms for comparison
        burst_patient = burst_detection_test.analyze_term_bursts(
            'patient', DATA_DIR,
            f"{OUTPUT_DIR}/burst_patient.json"
        )

        burst_accommodative = burst_detection_test.analyze_term_bursts(
            'accommodative', DATA_DIR,
            f"{OUTPUT_DIR}/burst_accommodative.json"
        )

        burst_time = time.time() - start_time

        results['methods']['kleinberg_burst'] = {
            'status': 'completed',
            'execution_time_seconds': round(burst_time, 2),
            'transitory_test': burst_transitory,
            'additional_terms_analyzed': ['patient', 'accommodative']
        }

        print(f"\nKleinberg Burst Detection completed in {burst_time:.2f} seconds")

    except Exception as e:
        print(f"\nERROR in Kleinberg Burst Detection: {e}")
        results['methods']['kleinberg_burst'] = {
            'status': 'failed',
            'error': str(e)
        }

    # ========================================================================
    # TEST 2: G-TEST / LOG-LIKELIHOOD RATIO
    # ========================================================================
    print("\n\n")
    print("#" * 80)
    print("# METHOD 2: G-TEST / LOG-LIKELIHOOD RATIO")
    print("#" * 80)

    start_time = time.time()

    try:
        # Critical test: transitory Dec 2021
        gtest_transitory = g_test_detection.test_transitory_december_2021(DATA_DIR)

        # Full backtest on 130 ground truth shifts
        gtest_backtest = g_test_detection.backtest_ground_truth(DATA_DIR, GROUND_TRUTH)

        gtest_time = time.time() - start_time

        results['methods']['g_test'] = {
            'status': 'completed',
            'execution_time_seconds': round(gtest_time, 2),
            'transitory_test': gtest_transitory,
            'backtest_metrics': gtest_backtest['metrics']
        }

        print(f"\nG-test completed in {gtest_time:.2f} seconds")

    except Exception as e:
        print(f"\nERROR in G-test: {e}")
        results['methods']['g_test'] = {
            'status': 'failed',
            'error': str(e)
        }

    # ========================================================================
    # TEST 3: JENSEN-SHANNON DIVERGENCE
    # ========================================================================
    print("\n\n")
    print("#" * 80)
    print("# METHOD 3: JENSEN-SHANNON DIVERGENCE")
    print("#" * 80)

    start_time = time.time()

    try:
        # Critical test: transitory Dec 2021
        jsd_transitory = jsd_detection.test_transitory_december_2021(DATA_DIR)

        # Full backtest on 130 ground truth shifts
        jsd_backtest = jsd_detection.backtest_ground_truth(DATA_DIR, GROUND_TRUTH)

        jsd_time = time.time() - start_time

        results['methods']['jsd'] = {
            'status': 'completed',
            'execution_time_seconds': round(jsd_time, 2),
            'transitory_test': jsd_transitory,
            'backtest_metrics': jsd_backtest['metrics']
        }

        print(f"\nJensen-Shannon Divergence completed in {jsd_time:.2f} seconds")

    except Exception as e:
        print(f"\nERROR in JSD: {e}")
        results['methods']['jsd'] = {
            'status': 'failed',
            'error': str(e)
        }

    # ========================================================================
    # COMPARATIVE ANALYSIS
    # ========================================================================
    print("\n\n")
    print("="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)

    # Transitory Test Comparison
    print("\nCRITICAL TEST: 'transitory' Removal December 2021")
    print("-" * 80)

    comparison_table = []
    for method_name, method_data in results['methods'].items():
        if method_data['status'] == 'completed':
            transitory_test = method_data.get('transitory_test', {})
            detected = transitory_test.get('detected', False)

            row = {
                'method': method_name,
                'detected': detected,
                'status': 'PASS' if detected else 'FAIL'
            }

            comparison_table.append(row)

            print(f"{method_name:25s}: {row['status']:5s}")

    # Performance Metrics Comparison (for methods with backtest)
    print("\n\nBACKTEST PERFORMANCE (130 Ground Truth Shifts)")
    print("-" * 80)
    print(f"{'Method':<25s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s} {'Time(s)':>10s}")
    print("-" * 80)

    for method_name, method_data in results['methods'].items():
        if method_data['status'] == 'completed' and 'backtest_metrics' in method_data:
            metrics = method_data['backtest_metrics']
            exec_time = method_data['execution_time_seconds']

            print(f"{method_name:<25s} "
                  f"{metrics['precision']:>10.3f} "
                  f"{metrics['recall']:>10.3f} "
                  f"{metrics['f1_score']:>10.3f} "
                  f"{exec_time:>10.2f}")

    # Summary recommendations
    print("\n\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    # Find best F1 score
    best_method = None
    best_f1 = 0

    for method_name, method_data in results['methods'].items():
        if method_data['status'] == 'completed' and 'backtest_metrics' in method_data:
            f1 = method_data['backtest_metrics']['f1_score']
            if f1 > best_f1:
                best_f1 = f1
                best_method = method_name

    if best_method:
        print(f"\nBest Overall Performance: {best_method.upper()}")
        print(f"  F1 Score: {best_f1:.3f}")

        best_data = results['methods'][best_method]
        metrics = best_data['backtest_metrics']

        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Recall: {metrics['recall']:.3f}")
        print(f"  Execution Time: {best_data['execution_time_seconds']:.2f}s")

    # Check transitory test results
    transitory_passes = sum(1 for m in results['methods'].values()
                           if m['status'] == 'completed' and
                           m.get('transitory_test', {}).get('detected', False))

    print(f"\nCritical Test (Transitory Dec 2021): {transitory_passes}/3 methods passed")

    # Save comprehensive results
    output_file = f"{OUTPUT_DIR}/comprehensive_comparison.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nFull results saved to: {output_file}")

    print("\n" + "="*80)
    print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return results


if __name__ == "__main__":
    results = run_all_tests()
