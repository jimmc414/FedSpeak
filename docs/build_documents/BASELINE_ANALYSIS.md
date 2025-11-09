# FedSpeak Corpus Baseline Analysis
## Ground Truth Statistics for Algorithm Testing

**Analysis Date:** 2025-11-06  
**Corpus Version:** 145 policy statements (2008-01-30 to 2025-09-17)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Documents | 145 statements |
| Date Range | 2008-01-30 to 2025-09-17 (17.6 years) |
| Total Words | 67,671 |
| Unique Vocabulary | 1,572 words |
| Avg Document Length | 466.7 words (median: 448) |
| Known Shifts Detected | 130 shifts across 5 terms |
| Statements per Year | ~8 (except 2020: 11) |

---

## 1. Corpus Statistics

### 1.1 Temporal Distribution

**Statements by Year:**
```
2008: 8   2009: 8   2010: 8   2011: 8   2012: 8   2013: 8
2014: 8   2015: 8   2016: 8   2017: 8   2018: 8   2019: 8
2020: 11  2021: 8   2022: 8   2023: 8   2024: 8   2025: 6
```

**Key Observations:**
- Consistent 8 statements/year (FOMC meets 8 times annually)
- 2020 anomaly: 11 statements (emergency COVID meetings)
- No significant gaps (>90 days) between statements
- Data quality: All 145 statements successfully parsed

### 1.2 Vocabulary Distribution

**Document Length Statistics:**
- Mean: 466.7 words
- Median: 448 words
- Range: 136 - 888 words
- Std Dev: 146.7 words

**Top 20 Non-Stopword Terms:**

| Rank | Term | Frequency | % of Corpus |
|------|------|-----------|-------------|
| 1 | committee | 1,309 | 1.93% |
| 2 | inflation | 1,222 | 1.81% |
| 3 | its | 842 | 1.24% |
| 4 | economic | 767 | 1.13% |
| 5 | federal | 723 | 1.07% |
| 6 | rate | 636 | 0.94% |
| 7 | policy | 591 | 0.87% |
| 8 | market | 570 | 0.84% |
| 9 | percent | 569 | 0.84% |
| 10 | conditions | 473 | 0.70% |
| 11 | securities | 469 | 0.69% |
| 12 | range | 430 | 0.64% |
| 13 | labor | 428 | 0.63% |
| 14 | funds | 397 | 0.59% |
| 15 | monetary | 378 | 0.56% |
| 16 | employment | 351 | 0.52% |
| 17 | target | 319 | 0.47% |
| 18 | financial | 318 | 0.47% |
| 19 | agency | 314 | 0.46% |
| 20 | information | 306 | 0.45% |

**Vocabulary Growth:**
- Peak vocabulary: 2020 (614 unique words) - COVID-related terminology
- Typical range: 250-500 unique words per year
- Total corpus: 1,572 unique words

---

## 2. Known Shifts (Ground Truth)

### 2.1 Summary Statistics

**Total Shifts Detected:** 130 across 5 terms

| Term | Emergences | Removals | Total |
|------|------------|----------|-------|
| transitory | 5 | 39 | 44 |
| patient | 4 | 29 | 33 |
| accommodative | 9 | 22 | 31 |
| considerable_time | 3 | 10 | 13 |
| full_range_of_tools | 1 | 8 | 9 |

### 2.2 Detailed Shift Timelines

#### TRANSITORY (44 shifts)
**Pattern:** Intermittent use with major removal event in Dec 2021

**Emergences:**
- 2009-12-16 (First introduction)
- 2012-12-12 (Re-introduction)
- 2013-06-19 (Re-introduction)
- 2014-12-17 (Re-introduction)
- 2016-12-14 (Re-introduction)

**Notable Removals:**
- Multiple intermittent removals 2011-2013
- Sustained removals 2017-2019
- **CRITICAL: 2021-12-15** (After sustained COVID-era use)

**COVID Era Usage (2021):**
- 2021-04-28: "Inflation has risen, largely reflecting transitory factors"
- 2021-06-16: Same phrasing
- 2021-07-28: Same phrasing
- 2021-09-22: "Inflation is elevated, largely reflecting transitory factors"
- 2021-11-03: "factors that are expected to be transitory" (LAST USE)
- 2021-12-15: **ABSENT** (major policy shift)

#### SUBSTANTIAL FURTHER PROGRESS (8 occurrences)
**Pattern:** Clear emergence + removal lifecycle

- **First:** 2020-12-16 (Introduced as QE taper condition)
- **Usage:** Appeared in all 7 statements from Dec 2020 - Nov 2021
- **Last:** 2021-11-03 ("In light of the substantial further progress...")
- **Removed:** 2021-12-15 (When taper began)

**Context:** This phrase signaled the Fed's condition for beginning QE taper. Its removal coincided with actual taper implementation.

#### ACCOMMODATIVE (31 shifts)
**Pattern:** Complex on/off pattern reflecting policy stance

**Major Emergence Periods:**
- 2013-2014 (Tapering discussions)
- 2016-2017 (Rate normalization)

**Major Removal Period:**
- 2018-2020 (Post-tightening to COVID)
- 2022 (Begin current tightening cycle)

#### PATIENT (33 shifts)
**Pattern:** Multiple cycles of emergence and removal

**Notable Cycles:**
- 2013-2015 (Forward guidance language)
- Late 2015 (Pre-liftoff period)
- 2020 (COVID policy)

#### SYMMETRIC (Validation case)
**Pattern:** Emergence in 2017, sustained use

- **Pre-period:** Absent before 2017-03-15
- **First:** 2017-03-15 ("symmetric inflation goal")
- **Usage:** 28 statements, 47 total occurrences
- **Context:** Introduction of symmetric 2% inflation target framework

---

## 3. Critical Test Cases for Algorithm Validation

### 3.1 PRIMARY TEST: "Transitory" Removal (Dec 2021)

**Why This Is The Gold Standard Test:**
1. Clear, sustained usage period (Apr-Nov 2021)
2. Abrupt removal (one statement to the next)
3. High historical significance (policy turning point)
4. Well-documented in financial press

**Test Setup:**
```
Training Period: 2008-01-30 to 2021-11-03 (145 statements → 144 after removal)
Test Date:       2021-12-15
Expected Result: Algorithm should flag 'transitory' removal

Ground Truth:
- Last occurrence:  2021-11-03
- First absence:    2021-12-15
- Statement count:  28 statements contain term
- Total uses:       29 occurrences
```

**Verification Context:**
- **2021-11-03:** "Inflation is elevated, largely reflecting factors that are expected to be transitory"
- **2021-12-15:** Term completely absent; replaced with "Supply and demand imbalances... have continued to contribute to elevated levels of inflation"

**Success Criteria:**
- ✅ Algorithm detects removal at 2021-12-15
- ✅ Assigns high confidence/magnitude to shift
- ✅ Identifies term as previously significant (used in recent 5+ statements)

### 3.2 SECONDARY TEST: "Substantial Further Progress" Lifecycle

**Test Type:** Both emergence AND removal detection

**Timeline:**
```
Pre-period:   2020-01-29 to 2020-11-05 (absent)
Emergence:    2020-12-16 (NEW PHRASE)
Sustained:    2021-01-27, 2021-03-17, 2021-04-28, 2021-06-16, 2021-07-28, 2021-09-22
Peak:         2021-11-03 (phrase triggers policy action)
Removal:      2021-12-15 (absent)
```

**Success Criteria:**
- ✅ Detects emergence at 2020-12-16
- ✅ Detects removal at 2021-12-15
- ✅ Recognizes sustained usage period (not a one-off)

### 3.3 VALIDATION TEST: "Symmetric" Emergence (2017)

**Test Type:** Emergence detection + synonym expansion validation

**Timeline:**
```
Pre-period:   2017-02-01 (absent)
Emergence:    2017-03-15 ("symmetric inflation goal")
Sustained:    Appears in 28 subsequent statements
```

**Candidate Expansions to Test:**
- Related terms that should co-emerge: "goal", "objective", "target" (in inflation context)
- Semantic shifts: From "longer-run" to "symmetric" framing

**Success Criteria:**
- ✅ Detects emergence at 2017-03-15
- ✅ Identifies related semantic field (inflation targeting)

---

## 4. Baseline Metrics for Algorithm Calibration

### 4.1 Statistical Considerations

**Corpus Size Constraints:**
- Small N: Only 145 documents
- Sparse vocabulary: 1,572 unique words total
- Low-frequency events: Most terms appear <5 times
- **Implication:** Need robust methods for small samples

**Term Frequency Distribution:**
- Top 10 terms: ~11% of all words
- Long tail: Many terms appear only 1-3 times
- **Implication:** Standard TF-IDF may be unstable

**Temporal Spacing:**
- ~45 days between statements (8 per year)
- **Implication:** Shifts detected have ~6-week granularity
- Cannot detect intra-meeting changes

### 4.2 Recommended Normalization Values

For comparing across algorithms:

```python
# Document length normalization
AVG_DOC_LENGTH = 466.7
MEDIAN_DOC_LENGTH = 448

# Vocabulary baseline
TOTAL_VOCAB = 1572
AVG_YEARLY_VOCAB = 400

# Temporal baseline  
STATEMENTS_PER_YEAR = 8
AVG_DAYS_BETWEEN = 45

# Frequency thresholds (suggested)
MIN_OCCURRENCES = 3      # Term must appear 3+ times to track
MIN_STATEMENTS = 2        # Term must appear in 2+ statements
LOOKBACK_WINDOW = 12      # 12 statements ≈ 1.5 years
```

### 4.3 Shift Detection Baselines

From the 130 known shifts:

**Emergence Characteristics:**
- Avg: Term goes from 0 → 1+ occurrences
- Sustained emergence: Appears in 3+ consecutive statements
- Major emergence: Appears in 5+ statements within 12-month window

**Removal Characteristics:**
- Avg: Term goes from 1+ → 0 occurrences  
- Sustained removal: Absent for 3+ consecutive statements
- Major removal: Previously appeared in 5+ of last 12 statements

---

## 5. Testing Recommendations

### 5.1 Algorithm Evaluation Protocol

**Step 1: Baseline Test**
```
Input:  Corpus of 144 statements (all except 2021-12-15)
Output: Shifts detected in 2021-12-15 statement
Check:  'transitory' should be flagged (removal)
        'substantial further progress' should be flagged (removal)
```

**Step 2: Historical Validation**
```
For each year 2008-2024:
  - Train on all prior years
  - Test on current year statements
  - Compare detections against 130 known shifts
  
Metrics:
  - Precision: % detected shifts that are in ground truth
  - Recall: % of ground truth shifts detected
  - F1 Score
```

**Step 3: Comparative Analysis**
```
Run all 3 proposed methods:
  1. Statistical (TF-IDF, chi-square)
  2. Hybrid (Word2Vec + statistical)
  3. LLM-based
  
Compare on:
  - Detection accuracy (F1 score)
  - Computational cost
  - Interpretability
  - False positive rate
```

### 5.2 Success Criteria

**Minimum Viable Performance:**
- Detect 'transitory' removal (Dec 2021): REQUIRED
- Detect 'substantial further progress' lifecycle: REQUIRED
- Overall F1 > 0.70 on known shifts: DESIRED

**Stretch Goals:**
- Detect multi-word phrase shifts
- Identify semantic substitutions (e.g., 'patient' → 'accommodative')
- Predict shift significance (correlate with market impact)

---

## 6. Data Files

### Available Resources

**Processed Corpus:**
- Location: `/mnt/c/python/FedSpeak/data/processed/`
- Files: `policy_statement_YYYYMMDD.txt` (145 files)
- Format: Plain text, cleaned

**Ground Truth Shifts:**
- Location: `/mnt/c/python/FedSpeak/results/alerts/`
- Files: `ALERT-YYYYMMDD-{emergence|removal}-{term}.json` (130 files)
- Format: JSON with metadata

**Analysis Results:**
- Location: `/tmp/corpus_baseline_analysis.json`
- Contains: Full statistical analysis, timelines, test cases
- Size: ~334 KB

**Summary:**
- Location: `/tmp/corpus_summary.json`
- Contains: Key metrics and test case definitions
- Size: ~2 KB

---

## 7. Key Findings Summary

### 7.1 Corpus Characteristics
1. **Highly structured:** Consistent format, predictable timing
2. **Concise:** Average 466 words, focused language
3. **Stable vocabulary:** Core 200 terms dominate
4. **Temporal consistency:** No major gaps, regular cadence

### 7.2 Shift Patterns
1. **Intermittent vs. Sustained:** Many terms cycle on/off
2. **Policy Signals:** Major shifts align with policy changes
3. **COVID Impact:** 2020-2021 shows unique language patterns
4. **Multi-term Shifts:** Changes often involve multiple related terms

### 7.3 Testing Insights
1. **Best Test Case:** 'transitory' removal is clear, significant, documented
2. **Lifecycle Test:** 'substantial further progress' tests both emergence and removal
3. **Validation:** 'symmetric' emergence in 2017 is well-defined
4. **Challenge Cases:** 'patient' and 'accommodative' have complex patterns

### 7.4 Statistical Challenges
1. **Small N:** 145 documents limits statistical power
2. **Sparse Data:** Many terms appear <5 times
3. **Context Dependency:** Same word means different things in different contexts
4. **Temporal Correlation:** Policy language is autocorrelated over time

---

## 8. Next Steps for Algorithm Development

### Recommended Approach
1. **Start Simple:** Implement basic TF-IDF change detection
2. **Validate:** Test against 'transitory' removal
3. **Iterate:** Add semantic analysis if needed
4. **Compare:** Run all 3 methods on full ground truth set
5. **Select:** Choose method with best accuracy/cost tradeoff

### Key Questions to Answer
1. Can statistical methods alone detect 'transitory' removal?
2. Do Word2Vec embeddings improve multi-word phrase detection?
3. What is the false positive rate on each method?
4. How computationally expensive are LLM approaches?

---

**Analysis Complete**  
Generated: 2025-11-06  
Analyst: Claude (Sonnet 4.5)  
Data Version: 145 statements, 2008-2025

For questions or updates, see: `/mnt/c/python/FedSpeak/BASELINE_ANALYSIS.md`
