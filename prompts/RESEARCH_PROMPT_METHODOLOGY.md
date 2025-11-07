# FedSpeak Methodology Research Prompt

## Project Overview

FedSpeak is an automated system that detects language shifts in Federal Reserve FOMC policy communications. It monitors specific keywords and phrases to identify when the Fed changes its policy messaging, potentially signaling important monetary policy pivots.

### Core Objective
Detect when the Federal Reserve **adds, removes, or significantly changes** the frequency of specific policy-relevant terms in their official statements, as these language changes often precede or accompany major policy shifts.

## Current Methodology

### 1. Data Collection
- **Source:** FOMC policy statements (primary) and minutes (secondary)
- **Period:** 2008-present (17+ years of data, 174 documents analyzed)
- **Updates:** Can download new statements as published (0-day lag)
- **Corpus:** ~16MB of raw HTML, 174 processed text documents

### 2. Keyword Selection (Current Approach)

**Manual Curation of Known Historical Shifts:**

The system tracks 5 primary keywords + 15 synonyms = 20 total terms:

1. **transitory** (+ transient, temporary, short-lived)
   - Known shift: December 2021 removal
   - Significance: Inflation narrative pivot

2. **accommodative** (+ supportive, accommodating, easy)
   - Known shift: September 2018 removal
   - Significance: End of post-crisis accommodation

3. **patient** (+ gradual, measured, deliberate)
   - Known shift: March 2015 removal
   - Significance: Pre-liftoff forward guidance

4. **considerable time** (+ extended period, substantial period)
   - Known shift: December 2014 substitution
   - Significance: Timeline guidance transition

5. **full range of tools** (+ all available tools, complete toolkit)
   - Known shift: March 2020 emergence
   - Significance: COVID crisis response readiness

**Selection Criteria:**
- Well-documented in financial press
- Known to have market impact when changed
- Validated by Fed researchers/commentary
- Manually curated from historical analysis

### 3. Detection Algorithm

**Pipeline:** Download → Extract → Analyze → Detect → Alert

**Core Logic:**
```
For each keyword/phrase:
  1. Count occurrences in each document
  2. Calculate 6-month rolling baseline
  3. Detect patterns:
     - EMERGENCE: count goes from 0 → >0 (sustained)
     - REMOVAL: count goes from >0 → 0 (sustained 3+ documents)
  4. Generate alerts with historical context
```

**Key Parameters:**
- Baseline window: 6 months
- Sustained removal threshold: 3 consecutive documents
- Detection lag: 0 days (alerts on publication)
- Focus: Policy statements (not minutes, which lag 3 weeks)

### 4. Validation Approach

**Test Case:** December 15, 2021 "transitory" removal
- Expected: Word used April-November 2021, removed December 2021
- Result: ✅ Detected correctly (baseline 3.8 → 0)
- Interpretation: Fed pivot from temporary to persistent inflation view

**Accuracy:** 100% on known test cases (by design - tracking known shifts)

### 5. Current Results

**Analysis Period:** January 2008 - September 2025 (17.7 years)
- **Total shifts detected:** 108 language changes
- **By keyword:**
  - Transitory: 34 shifts
  - Accommodative: 28 shifts
  - Patient: 28 shifts
  - Considerable time: 11 shifts
  - Full range of tools: 8 shifts

## Critical Limitations (The Core Problem)

### 1. **Retrospective Bias**
- ❌ Only monitors words we ALREADY KNOW were significant
- ❌ Cannot detect novel/emerging language patterns
- ❌ Backward-looking by design
- ❌ Would have missed "transitory" in April 2021 if we weren't already tracking it

### 2. **Manual Curation Bottleneck**
- ❌ Requires human judgment to add new keywords
- ❌ Relies on financial press coverage to identify candidates
- ❌ Lag between shift happening and being added to system
- ❌ No systematic discovery of new meaningful terms

### 3. **Validation Circularity**
- ✅ 100% accurate on known test cases
- ❌ But we're testing against the same shifts we designed it to detect
- ❌ No way to measure false negatives (missed novel shifts)
- ❌ Unknown precision on truly novel patterns

### 4. **Synonym Selection Subjectivity**
- Current synonyms chosen by domain knowledge
- Not empirically derived from corpus
- May miss Fed's actual usage patterns
- Risk of including terms Fed doesn't use (false positives)

## Research Questions

### Question 1: Prospective Keyword Discovery

**Challenge:** How can we automatically identify **emerging** policy-relevant terms BEFORE they become widely recognized as significant?

**Current gap:**
- System would NOT have detected "transitory" as a new keyword in April 2021
- Only tracking it because we know (in retrospect) it was significant
- Need methodology to identify candidates in real-time

**Approaches to evaluate:**

A. **Statistical Anomaly Detection**
- Track ALL words/phrases in corpus
- Identify statistically significant changes in frequency
- Flag sudden emergence or removal of any term
- Filter for policy-relevant context

B. **Semantic Field Analysis**
- Identify clusters of related policy terms
- Monitor entire semantic fields (e.g., "time-related forward guidance")
- Detect when Fed shifts between related concepts
- Capture substitution patterns automatically

C. **Comparative Analysis**
- Compare current statement to previous N statements
- Identify any phrases that appear/disappear
- Weight by position (early paragraphs = more important?)
- Filter by economic/policy relevance

D. **Topic Modeling Approaches**
- LDA or similar to identify topics per document
- Track topic distribution changes over time
- Detect shifts in topic emphasis
- Map topics to policy dimensions

E. **NLP-Based Approaches**
- Word embeddings to find semantically similar emerging terms
- Named entity recognition for policy-specific phrases
- Dependency parsing to identify meaningful phrase structures
- Sentiment/tone analysis around key concepts

**Specific question:** What methodology would have flagged "transitory" as a significant NEW term when it first emerged in April 2021, without prior knowledge that it would become important?

### Question 2: Synonym Discovery

**Challenge:** How to empirically derive synonyms rather than relying on domain expertise?

**Current approach:**
- Synonyms chosen by "what sounds similar"
- Not validated against actual Fed usage patterns
- Risk of false positives (words Fed doesn't use)

**Approaches to evaluate:**

A. **Co-occurrence Analysis**
- Find words that appear in similar contexts
- Measure semantic similarity in actual usage
- Validate candidates against corpus frequency

B. **Contextual Embeddings**
- Use BERT/similar to find contextually similar terms
- Cluster words by Fed usage patterns
- Identify true functional synonyms

C. **Temporal Correlation**
- Find words whose usage patterns correlate
- May indicate synonymous or related concepts
- Test if they predict same policy signals

**Specific question:** Given "accommodative," what empirical method would identify "supportive" as a synonym by analyzing the corpus, rather than relying on human judgment?

### Question 3: Real-Time Significance Assessment

**Challenge:** How to distinguish meaningful shifts from routine language variation?

**Current approach:**
- All tracked words assumed significant (by definition)
- No mechanism to assess importance of detected shifts
- Binary alert (shift detected or not)

**Dimensions to consider:**

A. **Context Importance**
- Position in statement (early paragraphs = more weight?)
- Surrounding language (cautionary vs. confident tone?)
- Association with rate decisions vs. assessment language

B. **Historical Precedent**
- Is this a reintroduction of old language?
- Is this a novel term or established vocabulary?
- Does historical pattern suggest significance?

C. **Intensity Metrics**
- Frequency change magnitude
- Persistence (how many consecutive documents?)
- Acceleration (gradual vs. sudden change?)

D. **External Validation**
- Correlation with market reactions
- Coverage in financial press
- Fed official commentary/speeches

**Specific question:** On April 28, 2021, when "transitory" first appeared, what signals would indicate this is a SIGNIFICANT new term vs. routine language variation?

### Question 4: Optimal Detection Parameters

**Challenge:** Current parameters (6-month baseline, 3-document threshold) were chosen somewhat arbitrarily.

**Current settings:**
- Baseline window: 6 months
- Sustained removal: 3 consecutive documents at count=0
- Minimum baseline samples: 3 documents

**Questions:**
- Are these optimal for different types of shifts?
- Should parameters vary by keyword type (e.g., crisis terms vs. routine guidance)?
- Can parameters be learned from historical data?
- Trade-off between speed (early detection) vs. accuracy (avoiding false positives)?

**Specific question:** Would dynamic parameters (e.g., shorter baseline for crisis periods, longer for stable periods) improve detection quality?

### Question 5: Multi-Document Context

**Challenge:** Currently analyzes each document independently. Might miss broader patterns.

**Current limitation:**
- Statement analyzed in isolation
- No cross-reference to minutes, speeches, testimony
- No incorporation of broader Fed communication ecosystem

**Approaches to evaluate:**

A. **Cross-Document Consistency**
- Track language in statements vs. minutes vs. speeches
- Detect when official statement diverges from other communication
- Identify "trial balloon" language in speeches before statement adoption

B. **Narrative Arc Analysis**
- Track evolution of concepts across multiple meetings
- Identify gradual vs. sudden shifts
- Detect building momentum toward language change

C. **Meeting-to-Meeting Deltas**
- Highlight all language changes document-to-document
- Cluster changes by theme
- Identify comprehensive "messaging pivots"

**Specific question:** Would analyzing statements in sequence (narrative progression) vs. individually improve shift detection?

### Question 6: Validation Strategy

**Challenge:** How to validate prospective detection when we don't know ground truth?

**Current validation:**
- Test against known historical shifts (circular)
- 100% accuracy by design (testing what we trained for)
- No measure of false negatives (missed novel shifts)

**Proposed approaches:**

A. **Backtesting with Held-Out Period**
- Remove knowledge of shifts in recent period (e.g., 2020-2025)
- Run discovery algorithm on earlier data only
- Test if it would have predicted known recent shifts

B. **Expert Validation**
- Present flagged candidates to Fed watchers/economists
- Assess whether detected shifts are meaningful
- Build precision/recall metrics from expert judgments

C. **Market Reaction Validation**
- Correlate detected shifts with market volatility
- Significant shifts should coincide with market moves
- Use market reaction as ground truth proxy

D. **Media Coverage Validation**
- Track financial press coverage of Fed statements
- Significant shifts should generate press attention
- Use journalist attention as significance indicator

**Specific question:** How can we measure the quality of prospective detection without relying on the same historical analysis that informed our keyword choices?

## Proposed Improvement Directions

### Direction 1: Hybrid Approach

**Combine curated keywords with unsupervised discovery:**

```
Layer 1: Known Keywords (current system)
  - Track the 5 validated keywords
  - High confidence, interpretable alerts

Layer 2: Supervised Discovery
  - Machine learning on historical shifts
  - Learn features of "policy-significant" language
  - Apply to new documents

Layer 3: Unsupervised Monitoring
  - Track ALL meaningful phrases statistically
  - Flag anomalies for human review
  - Build candidate pipeline

Layer 4: Validation Loop
  - Expert review of candidates
  - Market reaction correlation
  - Promote validated candidates to Layer 1
```

### Direction 2: Semantic Monitoring

**Track concepts rather than exact words:**

Instead of monitoring "accommodative," monitor the semantic field:
- Policy stance descriptors
- Supportiveness/restrictiveness language
- Dovish/hawkish signals (even if Fed doesn't use those terms)

Use embeddings to:
- Identify when Fed shifts between related concepts
- Detect semantic drift in terminology
- Capture meaning even if wording changes

### Direction 3: Differential Analysis

**Focus on document-to-document changes:**

For each new statement:
1. Identify ALL added/removed phrases (vs. previous statement)
2. Score each change by likely significance
3. Present top N candidates for review
4. Learn from user feedback on significance

### Direction 4: Multi-Modal Signals

**Incorporate non-textual signals:**

- Statement length changes
- Paragraph structure reorganization
- Vote dissents and commentary
- Press conference Q&A topics
- Market reaction (immediate and sustained)
- Subsequent Fed official commentary

## Specific Evaluation Request

Given the full FedSpeak codebase and 17+ years of corpus data (2008-2025):

### Task 1: Retrospective Discovery Test
**Question:** If you ONLY had data through 2020 and did NOT know about the "transitory" shift, what methodology would have:
1. Identified "transitory" as a significant emerging term in April 2021?
2. Flagged its December 2021 removal as policy-significant?
3. Distinguished it from routine language variation?

Please propose a specific algorithm, estimate its precision/recall, and explain how to validate it.

### Task 2: Synonym Validation
**Question:** For the existing 5 keywords, how would you:
1. Empirically validate the chosen synonyms?
2. Discover additional synonyms we may have missed?
3. Identify "false" synonyms (terms we included but shouldn't have)?

Please provide a concrete methodology with code-level detail.

### Task 3: Real-Time Candidate Generation
**Question:** For the most recent statement (September 17, 2025), what methodology would:
1. Identify candidate terms that MIGHT be emerging as significant?
2. Score their likelihood of being policy-relevant?
3. Determine when to escalate them to full monitoring?

Please propose specific features and thresholds.

### Task 4: Validation Framework
**Question:** How should we measure the system's effectiveness at prospective detection?
1. What metrics beyond "accuracy on known shifts"?
2. How to estimate false negative rate (missed shifts)?
3. What external validation sources to incorporate?

Please design a comprehensive validation framework.

## Resources Available

### Corpus
- 174 FOMC policy statements (2008-2025)
- 29 FOMC minutes (partial coverage)
- Cleaned text format, easily parseable
- Metadata: date, document type, word counts

### Current System
- Working Python codebase
- Keyword configuration system
- Detection algorithms
- 108 detected historical shifts as training data
- Visualization capabilities

### Validation Data
- Known shift dates and significance
- Historical context documentation
- Market reaction data (could be incorporated)
- Financial press coverage (could be scraped)

## Desired Outputs

1. **Theoretical Framework:** Rigorous methodology for prospective detection
2. **Algorithm Specifications:** Concrete, implementable approaches
3. **Validation Design:** How to test and measure quality
4. **Trade-off Analysis:** Precision vs. recall, speed vs. accuracy
5. **Implementation Roadmap:** Prioritized improvements with expected impact

## Key Constraint

**Primary Value Proposition:** The system must provide **actionable, real-time alerts** on language shifts as they happen, not just retrospective analysis.

Success = detecting a truly novel, policy-significant language shift BEFORE it becomes widely recognized, with high enough confidence to be useful to Fed watchers, economists, and market participants.

## Meta-Question

**Is the fundamental approach viable?** Or does the inherent noise in language, combined with the rarity of truly significant shifts, make reliable prospective detection impossible without human judgment?

If prospective detection is feasible, what's the theoretical best-case precision/recall we could achieve, and what methodology would get us there?

---

**How would you approach improving this system to maximize its prospective value while maintaining high accuracy?**
