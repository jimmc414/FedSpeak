# FedSpeak Statistical Detection Methods - Prototypes

This directory contains working implementations and empirical tests of statistical methods for detecting linguistic shifts in FOMC policy statements.

## Quick Start

### Run All Tests
```bash
python run_all_tests.py
```

### Run Individual Methods
```bash
# Recommended method (best performance)
python improved_detection.py

# Original methods (mostly failed)
python burst_detection_test.py
python g_test_detection.py
python jsd_detection.py

# Diagnostic analysis
python diagnostic_analysis.py

# Generate charts
python generate_comparison_charts.py
```

## Results Summary

### Critical Test: "Transitory" December 2021 Removal

| Method | Result | Performance |
|--------|--------|-------------|
| **Improved Hybrid** | **PASS** | 55.3% precision, 16.2% recall |
| Kleinberg Burst | PASS | Too conservative (6 total detections) |
| G-test | FAIL | 0% on all metrics |
| JSD | FAIL | 0% on all metrics |

**Winner**: Improved Hybrid Detector

### Full Backtest (130 Ground Truth Shifts)

```
Improved Hybrid:
  True Positives:  21
  False Positives: 17
  False Negatives: 109

  Precision: 55.3%
  Recall:    16.2%
  F1 Score:  25.0%
```

## Files

### Implementations

1. **`improved_detection.py`** ⭐ RECOMMENDED
   - Hybrid rule-based + statistical approach
   - Optimized for FedSpeak's sparse data
   - Best empirical performance

2. `burst_detection_test.py`
   - Kleinberg burst detection algorithm
   - Passes critical test but too conservative

3. `g_test_detection.py`
   - G-test / log-likelihood ratio
   - Failed on sparse data (0% F1)

4. `jsd_detection.py`
   - Jensen-Shannon Divergence
   - Failed to isolate term contributions (0% F1)

### Utilities

5. `run_all_tests.py`
   - Master test runner
   - Compares all methods

6. `diagnostic_analysis.py`
   - Explains why G-test and JSD failed
   - Shows actual data for December 2021 case

7. `generate_comparison_charts.py`
   - Creates performance visualizations
   - Text and graphical output

### Documentation

8. `RESULTS_SUMMARY.md`
   - Quick reference for results
   - Tables and key findings

## Key Findings

### What Worked

**Improved Hybrid Detector**:
- Combines presence/absence rules with statistical validation
- 55% precision means most detections are actionable
- Successfully detects high-confidence shifts
- Fast (<1 second execution)

### What Didn't Work

**G-test**: Data too sparse for significance thresholds
- Removing 1 word from 1 document: G-statistic = 1.22
- Required for p<0.001: 10.83
- Gap: 8.8x too small

**JSD**: Can't isolate single-term contributions
- Overall JSD captures total change
- Individual term contributions lost in noise
- Can't attribute shifts to specific terms

**Kleinberg**: Too conservative
- Only detected 6/130 shifts
- All were complete removals (dropping to 0)
- Missed emergences and subtle changes

### Why Standard Methods Failed

FedSpeak has fundamentally different characteristics than the data statistical methods assume:

| Assumption | Reality in FedSpeak |
|------------|---------------------|
| Dense frequencies (100s of occurrences) | Sparse (1-2 per document) |
| Statistical power from large N | Single-digit counts |
| Continuous distributions | Binary presence/absence |

## Recommendations

### For Production Use

1. **Use Improved Hybrid Detector** as primary method
2. **Add confidence tiers**:
   - High: Complete presence/absence changes → Auto-alert
   - Medium: 2x frequency changes with p<0.05 → Human review
   - Low: Subtle variations → Log only

3. **Combine with baseline system**:
   - Baseline finds candidate terms
   - Statistical validates significance
   - Hybrid approach maximizes coverage

### For Research

1. Test semantic similarity methods (BERT embeddings)
2. Build ensemble combining multiple signals
3. Add temporal modeling (HMMs, change-point detection)
4. Incorporate economic context (CPI, policy events)

## Output Files

Results are saved to `results/` directory:

- `comprehensive_comparison.json` - All method results
- `improved_detector_results.json` - Best method details
- `method_comparison_charts.png` - Performance visualizations
- `burst_*.json` - Kleinberg results by term

## Reproducibility

All tests use:
- **Data**: `/mnt/c/python/FedSpeak/data/processed/policy_statement_*.txt`
- **Ground Truth**: `/mnt/c/python/FedSpeak/GROUND_TRUTH_SHIFTS.csv`
- **Test Suite**: `/mnt/c/python/FedSpeak/TEST_SUITE.json`

No randomness or manual parameters - results are fully reproducible.

## Performance

All methods complete in <2 seconds:
- Kleinberg: 1.32s
- G-test: 0.82s
- JSD: 0.91s
- Improved: 0.95s

Fast enough for real-time detection on new statements.

## Next Steps

1. **Production Integration**: Add improved detector to main FedSpeak system
2. **Confidence Tiers**: Implement multi-level alerting
3. **Human Review**: Build workflow for medium-confidence cases
4. **Ensemble Methods**: Combine multiple detection signals
5. **Semantic Analysis**: Test BERT-based contextual shift detection

## Contact

For questions about implementation or results, see:
- Main documentation: `/mnt/c/python/FedSpeak/PHASE2_STATISTICAL_TESTS.md`
- Results summary: `/mnt/c/python/FedSpeak/prototypes/RESULTS_SUMMARY.md`

---

**Date**: November 6, 2025
**Status**: Phase 2 Complete - Ready for Production Integration
