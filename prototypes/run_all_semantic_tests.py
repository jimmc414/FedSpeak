#!/usr/bin/env python3
"""
Master Test Runner for Phase 3 Semantic Methods
================================================

Runs all semantic/NLP method tests in sequence:
1. Word2Vec Training
2. Synonym Discovery
3. Semantic Proximity
4. Positional Analysis
5. BERT Feasibility

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import sys
import json
from datetime import datetime
import importlib.util


def run_module(module_path, module_name):
    """
    Import and run a module

    Returns: True if successful, False otherwise
    """
    print("\n" + "="*80)
    print(f"RUNNING: {module_name}")
    print("="*80)

    try:
        # Import module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Run main
        if hasattr(module, 'main'):
            result = module.main()
            print(f"\n✓ {module_name} completed successfully")
            return True, result
        else:
            print(f"\n✗ {module_name} has no main() function")
            return False, None

    except Exception as e:
        print(f"\n✗ {module_name} failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """Run all semantic tests"""
    print("="*80)
    print("PHASE 3: SEMANTIC/NLP METHODS - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Start time: {datetime.now().isoformat()}")

    prototypes_dir = "/mnt/c/python/FedSpeak/prototypes"
    results_dir = os.path.join(prototypes_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Test sequence
    tests = [
        {
            'name': 'Word2Vec Training',
            'file': 'word2vec_training.py',
            'description': 'Train Word2Vec on Fed corpus, validate similarity claims'
        },
        {
            'name': 'Synonym Discovery',
            'file': 'synonym_discovery.py',
            'description': 'Test automatic synonym discovery for tracked keywords'
        },
        {
            'name': 'Semantic Proximity',
            'file': 'semantic_proximity_test.py',
            'description': 'Test correlation between policy proximity and shift significance'
        },
        {
            'name': 'Positional Analysis',
            'file': 'positional_analysis.py',
            'description': 'Test if significant terms appear earlier in statements'
        },
        {
            'name': 'BERT Feasibility',
            'file': 'bert_feasibility.py',
            'description': 'Assess computational requirements for BERT fine-tuning'
        }
    ]

    # Run all tests
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': [],
        'summary': {}
    }

    for i, test in enumerate(tests, 1):
        print(f"\n\n{'#'*80}")
        print(f"# TEST {i}/{len(tests)}: {test['name']}")
        print(f"# {test['description']}")
        print(f"{'#'*80}")

        module_path = os.path.join(prototypes_dir, test['file'])
        success, test_result = run_module(module_path, test['name'].replace(' ', '_'))

        results['tests_run'].append({
            'test_name': test['name'],
            'file': test['file'],
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

        if not success:
            print(f"\n⚠ WARNING: {test['name']} failed. Continuing with remaining tests...")

    # Summary
    print("\n\n" + "="*80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*80)

    successful = sum(1 for t in results['tests_run'] if t['success'])
    total = len(results['tests_run'])

    print(f"\nTests completed: {successful}/{total}")
    print("\nTest Results:")
    for test in results['tests_run']:
        status = "✓ PASS" if test['success'] else "✗ FAIL"
        print(f"  {status}  {test['test_name']}")

    results['summary'] = {
        'total_tests': total,
        'successful': successful,
        'failed': total - successful,
        'success_rate': successful / total if total > 0 else 0
    }

    # Save comprehensive results
    summary_path = os.path.join(results_dir, 'comprehensive_test_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nComprehensive summary saved to: {summary_path}")
    print(f"\nEnd time: {datetime.now().isoformat()}")

    # Overall verdict
    print("\n" + "="*80)
    if successful == total:
        print("✓ ALL TESTS PASSED")
    elif successful > 0:
        print(f"⚠ PARTIAL SUCCESS ({successful}/{total} tests passed)")
    else:
        print("✗ ALL TESTS FAILED")
    print("="*80)

    return results


if __name__ == "__main__":
    main()
