# Document 03: Detection Feasibility Plan

## Purpose

Test whether different NLP approaches can actually detect the language shifts identified in Document 02. Determine which techniques produce useful signals vs. noise, and which are implementable without excessive complexity.

## Questions to Answer

1. Can simple keyword frequency tracking catch known shifts?
2. Do more sophisticated methods (TF-IDF, embeddings) provide better signal?
3. What time window captures changes without excessive noise?
4. How do we distinguish meaningful shifts from natural language variation?
5. Which approach is implementable without heavy ML infrastructure?
6. What are the tradeoffs between different methods?

## Test Dataset

Based on Document 02 recommendations, select **2-3 test cases** representing different shift types:

### Primary Test Case (Required)
**Recommended: 2021-2022 "Transitory" Inflation Language**
- **Why:** Well-documented, clear disappearance, recent (good data quality)
- **Type:** Deletion/substitution
- **Timeframe:** Q1 2021 - Q4 2022
- **Documents needed:** All FOMC statements and minutes from 12 months before to 12 months after

### Secondary Test Case (Required)
**Choose one that differs from primary:**
- **Option A - Subtle shift:** 2018 "accommodative" removal (gradual change)
- **Option B - Addition:** 2008-2009 QE language introduction (new concept appearing)
- **Option C - Reframing:** 2013 taper language evolution (same concept, different words)

Select based on Document 02 findings about what's well-documented and available.

### Optional Third Test Case
Only if time permits and first two are successful. Should be challenging edge case.

## Approaches to Test

Test 4 different detection methods, ordered from simplest to most complex:

### Approach 1: Simple Keyword Frequency Tracking

**Method:**
- Define target keywords (e.g., "transitory", "accommodative", "quantitative easing")
- Count occurrences in each document
- Plot frequency over time
- Apply threshold: flag when frequency drops to zero or spikes

**Implementation:**
```python
# Pseudocode
for each document in time series:
    count = text.lower().count(target_word)
    store (date, count)

plot time series
identify points where count changes significantly
```

**Questions to answer:**
- Does this clearly show the known shift?
- What's the signal-to-noise ratio?
- Can it detect the shift in the first document it occurs?
- What about related terms? (e.g., "temporary" vs "transitory")

**Strengths/Weaknesses:**
- Strength: Simple, interpretable, fast
- Weakness: Misses semantic shifts, synonyms, context changes

### Approach 2: TF-IDF Change Detection

**Method:**
- Calculate TF-IDF scores for all terms across all documents
- Identify terms with largest score changes period-over-period
- Rank terms by change magnitude
- Check if known shift words appear in top movers

**Questions to answer:**
- Does this surface the known shifts without specifying keywords?
- How many false positives (unimportant word changes)?
- What window size works best?
- Does it capture semantic shifts better than keyword counting?

**Strengths/Weaknesses:**
- Strength: Discovers unexpected changes, no predefined keywords
- Weakness: More complex, harder to interpret, may flag noise

### Approach 3: Semantic Similarity (Word Embeddings)

**Method:**
- Generate document embeddings using pre-trained models
- Measure cosine similarity between consecutive documents
- Flag large similarity drops (documents that differ significantly from previous)

**Implementation options:**
- Option A: Average word2vec
- Option B: Sentence transformers

**Questions to answer:**
- Do semantic shifts show up as similarity drops?
- Is this more sensitive than keyword tracking?
- What threshold separates signal from noise?
- Does this work better for reframing vs. deletions?

**Strengths/Weaknesses:**
- Strength: Captures semantic changes beyond keywords
- Weakness: Less interpretable, requires ML libraries, computationally heavier

### Approach 4: N-gram / Phrase Tracking

**Method:**
- Extract 2-3 word phrases from documents
- Track phrase frequency over time
- Identify appearing/disappearing phrases

**Questions to answer:**
- Does this catch "quantitative easing" appearing better than just "quantitative"?
- How much noise from common phrases?
- What frequency threshold filters noise?

**Strengths/Weaknesses:**
- Strength: Catches multi-word concepts that keyword search misses
- Weakness: More data to process, many common phrases add noise

## Experimental Setup

### Data Preparation
1. Download all relevant documents for test cases (from Document 01 approach)
2. Extract text using methods from Document 01
3. Preprocess:
   - Remove boilerplate (headers, footers, standard disclaimers)
   - Lowercase (for some approaches)
   - Remove punctuation (optional, test both ways)
   - Tokenization
4. Create time-ordered corpus

### Baseline Establishment
Before testing detection:
- Manually verify the known shift exists in the documents
- Record exact documents where shift occurs
- This is ground truth for evaluation

### Testing Protocol
For each approach:
1. Run on primary test case
2. Record results (did it detect? when? false positives?)
3. Tune parameters if needed (window size, thresholds)
4. Run on secondary test case with same parameters
5. Document findings

### Evaluation Metrics

For each approach, measure:

**Detection Success:**
- Did it flag the known shift? (Yes/No)
- Which document did it first detect the shift in?
- How many documents after the actual shift? (lag)

**False Positive Rate:**
- How many alerts for non-shifts?
- What triggered false positives?

**Interpretability:**
- Can you explain why the alert fired?
- Can you show the user what changed?

**Implementation Complexity:**
- Lines of code
- External dependencies
- Computational requirements (runtime on test dataset)

**Scalability:**
- Would this work on 1000+ documents?
- Real-time feasibility for monitoring new documents?

## Implementation Details

### Environment Setup
- Python 3.8+
- Virtual environment recommended
- Required libraries:
  - `pandas`, `numpy` (data handling)
  - `nltk` or `spacy` (tokenization)
  - `scikit-learn` (TF-IDF)
  - `gensim` or `sentence-transformers` (embeddings)
  - `matplotlib` or `plotly` (visualization)

### Code Organization
Create separate scripts or notebooks for each approach:
- `approach_1_keywords.py` or `.ipynb`
- `approach_2_tfidf.py` or `.ipynb`
- `approach_3_embeddings.py` or `.ipynb`
- `approach_4_ngrams.py` or `.ipynb`

Each should:
- Load preprocessed data
- Implement the detection method
- Output results
- Generate visualizations
- Include timing metrics

### Visualization Requirements

For each approach, create:
1. **Time series plot:** 
   - X-axis: Document date
   - Y-axis: Metric value (frequency, similarity, TF-IDF score)
   - Mark known shift dates with vertical lines
   - Highlight detected changes

2. **Results table:**
   - Document date | Metric value | Alert fired? | Actual shift?

3. **Confusion matrix style:**
   - True positives (detected actual shifts)
   - False positives (false alarms)
   - False negatives (missed shifts)

## Deliverable Format

Create `03-methods.md` with the following sections:

### 1. Executive Summary
- Which approach performed best?
- Clear recommendation with rationale
- What tradeoffs were considered?

### 2. Test Case Setup
- Description of test cases used
- Data preparation steps
- Ground truth verification
- Sample sizes and date ranges

### 3. Results for Each Approach

For Approaches 1-4, document:

#### Approach X: [Name]
**Method Description:** Brief explanation of the technique

**Implementation:**
- Code snippet (core logic, ~10-20 lines)
- Libraries used
- Runtime on test dataset

**Results:**
- **Primary test case:** Did it detect? Lag? False positives?
- **Secondary test case:** Did it detect? Lag? False positives?
- Visualizations (plots showing detection)

**Analysis:**
- What worked well?
- What failed?
- Why did it succeed/fail?
- Parameter sensitivity (if tuning was needed)

**Scores:**
| Metric | Score |
|--------|-------|
| Detection Success | Yes/No |
| Detection Lag | X documents |
| False Positive Count | N |
| Interpretability | High/Medium/Low |
| Implementation Complexity | 1-5 scale |
| Runtime | X seconds |

### 4. Comparative Analysis

**Summary Table:**
| Approach | Detected? | FP Rate | Interpretable? | Complexity | Recommendation |
|----------|-----------|---------|----------------|------------|----------------|

**Tradeoff Discussion:**
- Simple vs. sophisticated: Is complexity worth it?
- Precision vs. recall: Better to miss shifts or get false alarms?
- Interpretability vs. power: Can users understand why alerts fired?

### 5. Recommendation

**Primary Recommendation:**
"Use [approach] because [specific reasoning based on test results]"

Must include:
- Which approach to implement
- Why it outperforms alternatives
- What parameters to use
- Expected performance characteristics

**Backup Recommendation:**
"If [primary] fails in production, try [backup] because [reason]"

**Rejected Approaches:**
"Do not use [approach] because [specific failure observed in testing]"

### 6. Implementation Roadmap

Based on chosen approach:
- What preprocessing is needed?
- What parameters need tuning on full dataset?
- What alert logic should be used?
- How to present results to users?

### 7. Open Questions & Future Work

- What worked but needs refinement?
- What should be tested with more data?
- What shift types did we NOT test that might require different methods?
- What would hybrid approaches look like?

### 8. Next Steps

**For requirements document:**
- Functional requirements based on chosen approach
- Data requirements (what documents, how often)
- Performance requirements (speed, accuracy thresholds)

**For architecture document:**
- Component breakdown based on detection method
- Data pipeline design
- Alert system design

## Time Estimate

8-10 hours:
- 1-2 hours: Data preparation and baseline establishment
- 4-6 hours: Implementing and testing 4 approaches
- 1-2 hours: Analysis and comparison
- 1 hour: Documentation and recommendations

## Success Criteria

Document 03 is complete when you can answer:
1. "Which NLP method should we use?" (with empirical evidence)
2. "How well does it work?" (with quantified performance)
3. "What are the limitations?" (with specific examples)

The recommendation should be based on actual test results, not theoretical superiority.

## Important Notes

### Iteration Expected
- First parameters probably won't work perfectly
- Tune thresholds, window sizes based on results
- Document what you tried and why you adjusted

### Negative Results Are Valuable
- If an approach doesn't work, document why
- Failed experiments inform what NOT to build
- Better to discover limitations now than after full implementation

### Code Quality
- Code doesn't need to be production-ready
- Focus on getting results, not perfect engineering
- But should be reproducible (save parameters, document steps)

### Visualization is Critical
- Plots make results immediately clear
- Much better than tables of numbers
- Include in deliverable document

---

*This plan assumes Documents 01 and 02 are complete and provides necessary context about data availability and test cases.*
