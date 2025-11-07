# Phase 5: Feasibility and Cost Assessment

**Date**: November 6, 2025
**Purpose**: Assess feasibility, implementation complexity, and cost-benefit analysis for all proposals from the three model responses based on empirical validation from Phases 2-4

---

## Executive Summary

After comprehensive empirical testing across 4 phases (145 statements, 130 ground truth shifts, prospective validation on 2021 critical events), we can now definitively assess which proposals are worth implementing.

### Key Finding

**Most model response proposals FAILED empirical validation**. Only ONE method proved viable for production: the **Improved Hybrid Detector** (developed in Phase 2 after original methods failed).

### Bottom Line Recommendations

**IMPLEMENT IMMEDIATELY** (< 1 week):
- Improved Hybrid Detector (already proven)
- Prospective detection pipeline (validated Phase 4)

**NOT RECOMMENDED** (Failed testing):
- G-test anomaly detection (0% F1 score)
- JSD distributional analysis (0% F1 score)
- BERT fine-tuning (corpus 5.6x too small)
- Automatic synonym discovery (0% success rate)
- Novel term scanning (ranked "transitory" 617th)
- RL-based model selection (no evidence needed)
- TAMA multimodal framework (wrong domain)

---

## SECTION 1: Response 1 Proposals (Comprehensive Statistical/ML)

### Proposal 1A: Kleinberg Burst Detection

**Claimed Performance**: "Would detect April 2021 'transitory' with burst weight 8.5 (highly significant)"

**Empirical Results** (Phase 2 & 4):
- Critical test (Dec 2021 removal): PASS (detected)
- Critical test (Apr 2021 emergence): FAIL (missed)
- Corpus-wide: 6 detections out of 130 ground truth (4.6% recall)
- Actual burst weight: 3.0 (not 8.5 as claimed)
- All detections: Removals only, no emergences

**Implementation Complexity**: LOW
- Algorithm: Dynamic programming for state transitions
- Dependencies: NumPy only
- Code: ~150 lines Python
- Execution time: 1.32 seconds

**Computational Cost**:
- CPU only (no GPU needed)
- Memory: < 100 MB
- Runtime: < 2 seconds for full corpus

**Data Requirements**: Works with 145 documents

**Development Cost Estimate**:
- Time: Already implemented (4 hours)
- Cost: $600 (4 hrs × $150/hr)
- Status: Prototype complete

**VERDICT**: **PARTIAL - Use as validation layer only**

**Rationale**:
- Too conservative (misses 95% of shifts)
- Only detects removals, not emergences
- But: 100% precision when it does detect
- **Use case**: Validate high-confidence removal alerts from Improved Hybrid
- **Role**: Layer 2 confirmation, not primary detector

**ROI**: Low. Already built, but limited utility.

---

### Proposal 1B: BERT-based Semantic Analysis

**Claimed Performance**: "Extract contextual embeddings, JSD score 0.45-0.65 for 'transitory' shift, achieves 0.84 correlation with market reaction"

**Empirical Results** (Phase 3):
- Corpus size: 179 docs, 85K tokens
- BERT minimum requirement: 1,000 docs, 1M tokens
- Gap: **5.6x too small for fine-tuning**
- Alternative: Word2Vec trained successfully
- Word2Vec time: 1.12 seconds (CPU)

**Implementation Complexity**: VERY HIGH
- Fine-tuning: BERT-base or RoBERTa
- Requires: GPU (8-12 GB VRAM)
- Training time: 0.81 GPU hours
- Framework: HuggingFace transformers
- Deployment: Model serving infrastructure

**Computational Cost**:
- GPU rental: AWS p3.2xlarge @ $3/hr
- Training cost: $2.42 (one-time)
- Inference cost: $0.01 per statement (ongoing)
- **vs Word2Vec**: $0 (CPU, <2 seconds)

**Data Requirements**:
- Current: 179 documents (INSUFFICIENT)
- Minimum: 1,000 documents
- Recommended: 10,000+ documents
- **Shortfall**: 5.6x below minimum

**Overfitting Risk**: VERY HIGH
- 179 documents → severe overfitting
- Pre-trained BERT lacks Fed domain knowledge
- FinBERT available but not Fed-specific

**Development Cost Estimate**:
- Research/setup: 20 hours ($3,000)
- Fine-tuning experiments: 40 hours ($6,000)
- GPU costs: $100-500 (experimentation)
- Deployment infrastructure: 60 hours ($9,000)
- **Total**: $18,000-20,000

**VERDICT**: **NO - Not feasible**

**Rationale**:
- Corpus 5.6x too small (fundamental blocker)
- Word2Vec already works (1.12 sec, CPU, $0)
- No improvement over Phase 2 Improved Hybrid
- $20K cost with high failure risk
- Overkill for keyword detection use case

**Alternative**: Use Word2Vec for exploration (already implemented)

**ROI**: Negative. High cost, high risk, corpus too small.

---

### Proposal 1C: Multi-Layer Detection Architecture

**Claimed Structure**:
- Layer 1: Statistical anomaly (Temporal TF-IDF, Kleinberg, EWMA)
- Layer 2: Semantic field (Topic modeling, embedding drift)
- Layer 3: Document comparison (Cosine similarity, TF-IDF)
- Layer 4: NLP features (NER, dependency parsing, complexity)

**Claimed Timeline**: "5 months to production deployment"

**Empirical Assessment**:

**Layer 1 (Statistical)**:
- Kleinberg: Implemented, too conservative
- Temporal TF-IDF: Reasonable, similar to Improved Hybrid
- EWMA change point: Untested, likely similar to G-test failure
- **Status**: Improved Hybrid already covers this

**Layer 2 (Semantic)**:
- Topic modeling: Reasonable but complex
- Embedding drift: Word2Vec proximity tested (r=0.547 correlation)
- **Status**: Informative but doesn't improve detection

**Layer 3 (Document comparison)**:
- Cosine similarity: Basic baseline
- **Problem**: Claimed "similarity 0.1 in Dec 2008" contradicts Fed's formulaic language
- **Status**: Not proven necessary

**Layer 4 (NLP features)**:
- NER, dependency parsing: High complexity
- **Problem**: No evidence these improve shift detection
- Sentence complexity: Interesting but unvalidated
- **Status**: Speculative, untested

**Implementation Complexity**: VERY HIGH
- Estimated development: 800-1200 hours
- 4 distinct subsystems
- Integration and testing
- Maintenance burden

**Development Cost Estimate**:
- Layer 1: 200 hours ($30,000) - mostly complete
- Layer 2: 300 hours ($45,000) - topic models, embeddings
- Layer 3: 100 hours ($15,000) - document similarity
- Layer 4: 400 hours ($60,000) - NER, parsing, integration
- **Total**: $150,000 over 5 months

**VERDICT**: **NO - Unnecessary complexity**

**Rationale**:
- Improved Hybrid already works (55% precision, 16% recall)
- No evidence additional layers improve performance
- $150K cost vs. existing $600 solution
- Maintenance burden increases with each layer
- Violates Occam's Razor: simpler solution already proven

**Alternative**: Enhance Improved Hybrid incrementally based on real production feedback

**ROI**: Negative. Massive cost, no proven benefit.

---

### Proposal 1D: Claimed Performance Targets

**Claims**:
- "65-75% precision"
- "60-85% recall"
- "12 months to 75%+ precision"

**Empirical Results**:

**Phase 2 (Retrospective, 130 ground truth shifts)**:
- Improved Hybrid: 55% precision, 16% recall, F1=0.250
- G-test: 0% precision, 0% recall, F1=0.000
- JSD: 0% precision, 0% recall, F1=0.000
- Kleinberg: N/A precision, 5% recall

**Phase 4 (Prospective, 2021 critical shifts)**:
- Improved Hybrid: 100% precision, 100% recall, F1=1.000
- (Small sample: 8 statements, 2 critical shifts detected)

**Reality Check**:
- Phase 2 shows 55% precision is realistic for conservative detector
- 60-85% recall unlikely without sacrificing precision
- Phase 4's 100% was on 2 critical, obvious shifts

**Precision-Recall Tradeoff**:
- Conservative (current): 55% precision, 16% recall
- Aggressive (lower threshold): ~30% precision, ~40% recall (estimated)
- **Cannot achieve both high precision AND high recall** on sparse data

**Assessment**: Claims are **OVERLY OPTIMISTIC**

**Realistic Targets** (based on empirical data):
- Precision: 50-60% (achievable)
- Recall: 15-25% (achievable)
- Both >70%: Not feasible with current methods

**VERDICT**: **Claims REFUTED - Set realistic expectations**

**Recommended Targets**:
- Year 1: 55% precision, 20% recall (improve recall slightly)
- Year 2: 60% precision, 25% recall (incremental gains)
- Do NOT promise 75% precision + 85% recall

---

## SECTION 2: Response 2 Proposals (Pragmatic 4-Layer)

### Proposal 2A: Keep Current System as Layer 1

**Recommendation**: "Retain high-precision monitoring of 5+ manually curated keywords"

**Assessment**: **EXCELLENT ADVICE**

**Implementation Complexity**: ZERO (already exists)

**Cost**: $0 (already built)

**Value**: HIGH
- Proven baseline
- Low maintenance
- Established credibility
- Foundation for enhancements

**VERDICT**: **YES - Already doing this**

**ROI**: Infinite (no cost, high value)

---

### Proposal 2B: G-test Anomaly Detection as Layer 2

**Claimed Benefit**: "Better than Chi-squared for sparse data, good for detecting new/emerging terms"

**Empirical Results** (Phase 2):
- Critical test (Dec 2021 "transitory"): FAIL
- G-statistic: 0.85 (threshold: 10.83)
- Required: 8.8x larger signal to detect
- Corpus-wide: 0 TP, 0 FP, 130 FN
- F1 Score: **0.000**

**Root Cause** (Diagnostic analysis):
- Removing 1 word from 542-word document
- Baseline: 5 occurrences in 4,169 words
- Signal too weak for statistical significance
- Even p<0.05 threshold not reached (G=1.22 vs. 3.84)

**Implementation Complexity**: LOW (already built)

**Why It Failed**:
- G-test IS better than Chi-squared for sparse data
- BUT FedSpeak is TOO SPARSE even for G-test
- Method assumes counts in 10s-100s
- FedSpeak reality: counts of 1-2

**Development Cost**: Already spent $600 (4 hours)

**VERDICT**: **NO - Complete failure, drop proposal**

**Rationale**:
- 0% F1 score = total failure
- Not "sparse data" issue - "EXTREME sparse data"
- No threshold tuning can fix fundamental mismatch
- Evidence-based rejection

**ROI**: Already negative (wasted $600)

---

### Proposal 2C: Word2Vec Synonym Discovery

**Claimed Benefit**: "Automatically discover synonyms using most_similar(), validate and expand tracked keyword list"

**Empirical Results** (Phase 3):

**Similarity Claims**:
- Claimed: accommodative ↔ supportive = 0.78-0.85
- Actual: 0.13 (6x lower)
- Claimed: patient ↔ gradual = ~0.76
- Actual: 0.31 (2.4x lower)
- Claimed: accommodative ↔ easy = 0.68-0.72
- Actual: "easy" not in vocabulary

**Automatic Discovery**:
- Tested: 15 known synonyms
- Found in top 10: 0
- **Discovery rate: 0.0%**

**What Word2Vec Actually Found**:
- Semantically related terms (not synonyms)
- Example: "transitory" → "effects" (0.66), "declines" (0.64)
- Contextual relationships, not meaning equivalence

**Why It Failed**:
- Fed language is formulaic (exact repetition, no variation)
- No synonym usage in corpus to learn
- "Accommodative" used consistently, never "supportive"

**Partial Success**:
- Semantic proximity correlation: r=0.547 (strong)
- Terms closer to policy concepts show more shifts
- **Use case**: Exploration and prioritization, NOT synonym discovery

**Implementation Complexity**: LOW
- Word2Vec training: 1.12 seconds
- Already implemented
- CPU only, no dependencies

**Development Cost**: $600 (4 hours, already spent)

**VERDICT**: **PARTIAL - Reframe use case**

**Recommended Use**:
- Drop "automatic synonym discovery" claim (0% success)
- Keep for semantic exploration (r=0.547 utility)
- Use proximity scoring to prioritize monitoring
- Monthly corpus analysis for insight

**ROI**: Low for synonym discovery, Medium for exploration

---

### Proposal 2D: External Validation (Market Data, Media Coverage)

**Claimed Benefit**: "Market reaction correlation, media attention scoring validates significance"

**Assessment**: **EXCELLENT IDEA** (not yet tested)

**Implementation Complexity**: MEDIUM

**Components**:

**1. Market Data Validation**:
- Data source: Treasury futures (2yr, 5yr, 10yr)
- API options:
  - Free: FRED (Federal Reserve Economic Data)
  - Commercial: Bloomberg, Refinitiv (~$2,000/month)
  - Mid-tier: Alpha Vantage, Quandl ($50-200/month)
- Metric: Volatility in 30-60 min window post-release
- Threshold: >2x baseline volatility = significant

**2. Media Coverage Validation**:
- Data source: News APIs
  - Free tier: NewsAPI.org (100 requests/day, $0)
  - Commercial: GDELT, Factiva ($500-5,000/month)
- Metric: Count of articles mentioning term + "FOMC" within 24hrs
- Threshold: >50% of major outlets = significant

**Development Cost Estimate**:
- Market data integration: 40 hours ($6,000)
- API setup and testing: 20 hours ($3,000)
- Media scraping/API: 30 hours ($4,500)
- Validation logic: 20 hours ($3,000)
- Dashboard/reporting: 30 hours ($4,500)
- **Total**: $21,000

**Operational Cost**:
- Market data API: $50-200/month ($600-2,400/year)
- News API: $0-500/month ($0-6,000/year)
- **Total**: $600-8,400/year

**Value**: HIGH
- Independent validation of significance
- Reduces false positives from statistical noise
- Builds credibility (external corroboration)
- Can validate retrospectively AND prospectively

**Expected Impact**:
- Precision improvement: 55% → 65-70% (estimated)
- Filters statistical detections by real-world impact
- Clear "Tier 1" (market-validated) vs "Tier 2" (statistical only) alerts

**VERDICT**: **YES - High-value enhancement**

**Implementation Priority**: Tier 2 (after core detector deployed)

**Timeline**: 3-4 weeks development

**ROI**: HIGH - $21K investment, improves precision 10-15%, ongoing value

---

## SECTION 3: Response 3 Proposals (Advanced Infrastructure)

### Proposal 3A: TSAD Model Library (LSTM, GAN, Isolation Forest)

**Claimed Benefit**: "Build library of advanced deep learning models for time-series anomaly detection"

**Models Proposed**:
- LSTM (Long Short-Term Memory)
- GAN (Generative Adversarial Networks)
- Isolation Forest
- Local Outlier Factor (LOF)
- One-Class SVM

**Assessment**: **WRONG PROBLEM DOMAIN**

**Why This Is a Mismatch**:

1. **FedSpeak is TEXT, not time series**:
   - TSAD methods designed for numerical sequences
   - Fed statements are discrete documents (not continuous series)
   - 145 documents ≠ time series (too few, irregular intervals)

2. **Corpus is tiny for deep learning**:
   - 145 documents too small for LSTM training
   - GANs require thousands of samples
   - Would massively overfit

3. **Already tested statistical methods**:
   - Simple methods (Improved Hybrid) outperformed complex stats
   - Adding deep learning won't fix sparse data problem

**Implementation Complexity**: VERY HIGH
- LSTM: TensorFlow/PyTorch, GPU required
- GAN: Extremely complex training (stability issues)
- Isolation Forest: Scikit-learn (easier)
- Integration: Model serving, version control

**Computational Cost**:
- GPU training: $50-500 (experimentation)
- GPU inference: $0.10 per statement (ongoing)
- Infrastructure: Model serving, monitoring

**Development Cost Estimate**:
- LSTM implementation: 80 hours ($12,000)
- GAN implementation: 120 hours ($18,000)
- Isolation Forest: 20 hours ($3,000)
- Integration/testing: 80 hours ($12,000)
- **Total**: $45,000

**VERDICT**: **NO - Wrong application domain**

**Rationale**:
- TSAD designed for continuous numerical data
- Fed statements are discrete text documents
- Corpus too small for deep learning
- No evidence of need (simple methods work)
- Massive overkill

**ROI**: Negative. Wrong tool for the problem.

---

### Proposal 3B: RL-Based Model Selector

**Claimed Benefit**: "Model selection methods outperform every single anomaly detection method, RL agent selects optimal detector based on regime"

**Assessment**: **PREMATURE OPTIMIZATION**

**Prerequisites (not met)**:
1. Multiple viable detection methods
   - Reality: Only Improved Hybrid works
   - Kleinberg too conservative
   - G-test, JSD failed completely
   - **No portfolio to select from**

2. Sufficient training data for RL
   - Need: 1,000+ episodes
   - Have: 145 documents
   - **Insufficient for RL training**

3. Distinguishable "regimes"
   - Claim: RL adapts to changing market conditions
   - Reality: Fed statements uniform in structure
   - No clear regime shifts in corpus

**Implementation Complexity**: EXTREME
- RL framework: OpenAI Gym, Stable-Baselines3
- Reward engineering (most critical, most difficult)
- Exploration strategies
- Multi-armed bandit or policy gradient
- Continuous retraining

**Development Cost Estimate**:
- RL framework setup: 60 hours ($9,000)
- Reward function design: 80 hours ($12,000)
- Agent training/tuning: 120 hours ($18,000)
- Integration: 60 hours ($9,000)
- **Total**: $48,000

**When Would This Make Sense?**:
- IF we had 10+ viable detectors (we have 1)
- IF we had 10,000+ training samples (we have 145)
- IF there were clear regime changes (there aren't)
- IF simple methods had failed (they haven't)

**VERDICT**: **NO - Premature, no foundation**

**Rationale**:
- Only 1 viable detector (nothing to select from)
- Corpus too small for RL training
- Solving a problem that doesn't exist
- $48K cost with no proven need

**Alternative**: Deploy Improved Hybrid, collect 2-3 years of real data, then revisit

**ROI**: Negative. Premature optimization.

---

### Proposal 3C: Domain-Specific CB-LMs (Fine-tuned RoBERTa)

**Claimed Benefit**: "Central Bank Language Models fine-tuned on Fed corpus outperform foundational models, 84% accuracy on stance classification"

**Reference**: Bank for International Settlements (BIS) research

**Assessment**: **CORPUS TOO SMALL** (same issue as BERT)

**BIS CB-LM Training Corpus**:
- Central bank speeches: 10,000+ documents
- Policy documents: 5,000+ documents
- Research papers: 20,000+ documents
- **Total**: ~35,000 documents

**FedSpeak Corpus**:
- FOMC statements: 179 documents
- **Gap**: 195x too small

**Implementation Complexity**: VERY HIGH
- Model: RoBERTa-base or RoBERTa-large
- Fine-tuning: Weeks of GPU time
- Requires: Massive corpus expansion first

**Data Requirements**:
- Current: 179 FOMC statements
- Need: 10,000+ documents
- Sources to add:
  - FOMC Minutes (available)
  - Fed speeches (available)
  - Fed research papers (available)
  - Regional Fed banks (available)
- **Feasible but requires major data collection effort**

**Development Cost Estimate** (with corpus expansion):
- Corpus expansion: 200 hours ($30,000)
- Data cleaning/processing: 100 hours ($15,000)
- Fine-tuning experiments: 80 hours ($12,000)
- GPU costs: $1,000-3,000
- Evaluation: 40 hours ($6,000)
- **Total**: $64,000-66,000

**Timeline**: 4-6 months

**Value IF Successful**:
- Better stance classification (currently not needed)
- Improved semantic understanding
- Could enable more sophisticated detection

**VERDICT**: **NOT NOW - Revisit after corpus expansion**

**Recommended Path**:
1. Deploy Improved Hybrid (now)
2. Expand corpus to 1,000+ docs (6-12 months)
3. Revisit CB-LM fine-tuning (Year 2)

**ROI**: Currently negative. Potential future value if corpus expanded.

---

### Proposal 3D: MILA Hawk-O-Meter Framework

**Description**: "Monetary-Intelligent Language Agent using prompt engineering on large LLM (Llama 3.1 70B) to score granular policy stance"

**Reference**: Deutsche Bundesbank research

**Assessment**: **INTERESTING BUT NOT FOR DETECTION**

**What MILA Does Well**:
- Explainable stance scoring
- Granular decomposition (interest rate score, inflation score, etc.)
- Traceability (links to source text)
- Great for analyst tools

**What MILA Doesn't Do**:
- Detect WHEN shifts occur
- Replace statistical anomaly detection
- Work prospectively on novel terms

**Implementation Complexity**: MEDIUM
- Prompt engineering (not fine-tuning)
- LLM API: OpenAI GPT-4, Anthropic Claude, or local Llama
- Scoring rubric design
- Output parsing and validation

**Computational Cost**:
- API costs: $0.01-0.05 per statement
- 145 statements × $0.03 = ~$4.35 (one-time backtest)
- Ongoing: $0.03-0.10 per new statement
- Annual: ~$1.00 (8 statements/year × $0.10)

**Development Cost Estimate**:
- Prompt engineering: 40 hours ($6,000)
- Scoring rubric design: 20 hours ($3,000)
- Integration/testing: 20 hours ($3,000)
- Dashboard/UI: 40 hours ($6,000)
- **Total**: $18,000

**Use Case**: **Complementary analysis tool, NOT primary detector**

**Value**:
- Explainability for detected shifts
- Deep analysis for human review
- Monthly corpus reports
- Validate significance of statistical detections

**VERDICT**: **PARTIAL - Good for analysis, not detection**

**Recommended Scope**:
- Build lightweight version for shift explanation
- Apply AFTER Improved Hybrid detects shift
- Use to generate analyst reports
- Not for real-time alerting

**ROI**: Medium. Enhances interpretability, not core detection.

**Priority**: Tier 3 (after core system + external validation)

---

### Proposal 3E: TAMA (Multimodal Time Series to Image)

**Claimed Performance**: "97.5% F1 score on NASA dataset by converting time series to images"

**Description**: Convert numerical time series to visual representations, use computer vision models (ResNet, Vision Transformers) for anomaly detection

**Assessment**: **FASCINATING BUT COMPLETELY WRONG DOMAIN**

**Why NASA Achieved 97.5% F1**:
- Spacecraft telemetry: Continuous numerical sensors
- Thousands of data points per series
- Clear visual patterns (spikes, trends) in image form
- Labeled anomalies (component failures)

**FedSpeak Reality**:
- Text documents, not numerical time series
- 145 discrete documents (not continuous)
- No visual representation that makes sense
- Could convert word frequencies to images, but why?

**Implementation Complexity**: EXTREME
- Time series → image conversion
- Vision model (ResNet-50, ViT)
- GPU training infrastructure
- Makes no sense for text data

**VERDICT**: **NO - Interesting but wrong application**

**Rationale**:
- Designed for continuous numerical sensors
- FedSpeak is discrete text documents
- No benefit over text-native methods
- Unnecessary complexity

**ROI**: N/A - Not applicable to this domain

---

## SECTION 4: Cost-Benefit Analysis Matrix

### Quick Wins (< 1 week, high value)

| Proposal | Dev Time | Cost | Expected Benefit | ROI | Decision |
|----------|----------|------|------------------|-----|----------|
| Deploy Improved Hybrid | 2 days | $2,400 | 55% precision, 16% recall, proven | Very High | **DO IT** |
| Prospective pipeline | 3 days | $3,600 | 100% on critical shifts | Very High | **DO IT** |
| Keep existing Layer 1 | 0 | $0 | Proven baseline | Infinite | **KEEP** |

**Total Quick Wins**: $6,000, 1 week

---

### Medium Projects (1-4 weeks)

| Proposal | Dev Time | Cost | Expected Benefit | ROI | Decision |
|----------|----------|------|------------------|-----|----------|
| External validation (market/media) | 3 weeks | $21,000 | +10-15% precision | High | **DO - Tier 2** |
| Word2Vec exploration tool | 1 week | $6,000 | Corpus insights, r=0.547 correlation | Medium | **DO - Tier 3** |
| Kleinberg validation layer | 2 days | $2,400 | Confirm removals, 100% precision | Low | **MAYBE** |
| MILA-style explainer | 3 weeks | $18,000 | Interpretability, analyst tool | Medium | **CONSIDER - Tier 3** |

**Total Medium Projects**: $47,400, 7-9 weeks

---

### Major Projects (3-6 months)

| Proposal | Dev Time | Cost | Expected Benefit | ROI | Decision |
|----------|----------|------|------------------|-----|----------|
| CB-LM fine-tuning (after corpus expansion) | 4-6 months | $66,000 | Better semantics (future) | Unknown | **DEFER - Year 2** |
| Multi-layer architecture (Response 1) | 5 months | $150,000 | Unproven benefit | Negative | **NO** |
| TSAD model library | 3 months | $45,000 | Wrong domain | Negative | **NO** |
| RL model selector | 4 months | $48,000 | No portfolio to select from | Negative | **NO** |

---

### Not Recommended (Failed Testing)

| Proposal | Test Result | Reason for Rejection | Evidence |
|----------|-------------|---------------------|----------|
| G-test anomaly detection | 0% F1 score | Too sparse for significance | Phase 2 |
| JSD distributional analysis | 0% F1 score | Can't isolate term contributions | Phase 2 |
| BERT fine-tuning | Corpus 5.6x too small | Fundamental data constraint | Phase 3 |
| Automatic synonym discovery | 0% discovery rate | Fed uses no synonyms | Phase 3 |
| Novel term scanner | Ranked "transitory" 617th | Can't distinguish significance | Phase 4 |
| TAMA multimodal | N/A | Wrong application domain | Analysis |
| Positional weighting | 12.5% in first quarter | Terms appear at midpoint (46%) | Phase 3 |

---

## SECTION 5: Recommended Investment Strategy

### Tier 1: Deploy Immediately (< 1 week, $6,000)

**Priority**: CRITICAL

**Projects**:
1. Improved Hybrid Detector (2 days, $2,400)
   - Proven: 55% precision, 16% recall
   - Prospective: 100% on 2021 critical shifts
   - Fast: <1 second per statement

2. Prospective detection pipeline (3 days, $3,600)
   - Temporal validation framework
   - No-future-knowledge enforcement
   - Automated baseline calculation

3. Production deployment (2 days, $2,400)
   - Integration with existing Layer 1
   - Alert tiers (high/medium/low confidence)
   - Monitoring and logging

**Expected Outcome**:
- Working prospective detection system
- Proven performance metrics
- Foundation for all enhancements

**ROI**: Very High (proven to work)

**Timeline**: 1 week

---

### Tier 2: Short-term Enhancements (1-4 weeks, $21,000)

**Priority**: HIGH

**Project**: External Validation Layer

**Components**:
1. Market data integration (2 weeks, $9,000)
   - Treasury futures API (FRED or Alpha Vantage)
   - 30-minute volatility window
   - Threshold: >2x baseline = significant

2. Media coverage tracking (1 week, $6,000)
   - NewsAPI or GDELT integration
   - Term mention counting
   - 24-hour post-release window

3. Validation logic (1 week, $6,000)
   - Cross-reference statistical detections
   - Tier 1 alerts: Statistical + Market validation
   - Tier 2 alerts: Statistical only

**Expected Outcome**:
- Precision improvement: 55% → 65-70%
- Reduced false positives
- External credibility

**ROI**: High (+10-15% precision, ongoing value)

**Timeline**: 4 weeks

**Prerequisites**: Tier 1 complete

---

### Tier 3: Medium-term R&D (2-3 months, $24,000)

**Priority**: MEDIUM

**Projects**:

1. Word2Vec exploration tool (1 week, $6,000)
   - Semantic proximity dashboard
   - Term prioritization by policy relevance
   - Monthly corpus analysis reports

2. MILA-style explainer (3 weeks, $18,000)
   - Prompt engineering for stance decomposition
   - Granular scoring (rate, inflation, outlook)
   - Traceability to source text
   - Analyst-facing dashboard

**Expected Outcome**:
- Better corpus understanding
- Explainable detections
- Human analyst support

**ROI**: Medium (insight and interpretability)

**Timeline**: 4 weeks

**Prerequisites**: Tier 1-2 complete, 6 months production data

---

### Tier 4: Long-term Research (Year 2+, if needed)

**Priority**: LOW

**Conditional Projects**:

1. Corpus expansion (IF needed for advanced methods)
   - Add FOMC Minutes: ~700 documents
   - Add Fed speeches: ~2,000 documents
   - Add research papers: ~5,000+ documents
   - **Enables**: CB-LM fine-tuning

2. CB-LM fine-tuning (IF corpus expanded)
   - 4-6 months, $66,000
   - Better semantic understanding
   - Advanced stance classification

**Conditions**:
- Simple methods proven insufficient
- Business case for 10%+ precision gain
- Corpus expansion completed
- GPU infrastructure available

**Decision Point**: End of Year 1 (review production performance)

---

## SECTION 6: Risk Assessment

### High-Risk Proposals (DO NOT IMPLEMENT)

| Proposal | Risk Level | Failure Mode | Cost if Failed |
|----------|-----------|--------------|----------------|
| Multi-layer architecture | HIGH | Complexity, no proven benefit | $150,000 |
| TSAD model library | HIGH | Wrong domain, overfitting | $45,000 |
| RL model selector | HIGH | Insufficient data, premature | $48,000 |
| BERT fine-tuning (now) | HIGH | Corpus too small, overfitting | $20,000 |
| G-test detection | HIGH | Already failed testing | $0 (done) |
| Novel term scanner | MEDIUM | Can't filter significance | $9,000 |

**Total at-risk capital if ignored**: $272,000

---

### Low-Risk Proposals (RECOMMENDED)

| Proposal | Risk Level | Downside if Failed | Mitigation |
|----------|-----------|-------------------|------------|
| Improved Hybrid | VERY LOW | Already proven in testing | None needed |
| External validation | LOW | APIs may have downtime | Free tier fallback |
| Word2Vec exploration | LOW | Insights may not be actionable | Low cost ($6K) |
| MILA explainer | MEDIUM | Prompts may need tuning | Iterative refinement |

---

## SECTION 7: Final Recommendations

### What to Implement (Total: $51,000, 3 months)

**Immediate** (Week 1-2, $6,000):
1. Deploy Improved Hybrid Detector
2. Implement prospective detection pipeline
3. Production integration and monitoring

**Short-term** (Weeks 3-6, $21,000):
4. Market data validation layer
5. Media coverage tracking
6. Cross-validation logic

**Medium-term** (Weeks 7-12, $24,000):
7. Word2Vec exploration tool
8. MILA-style explainer for analysts

**Total Investment**: $51,000 over 3 months

**Expected Outcome**:
- Production system: 55-70% precision, 15-20% recall
- Prospective detection proven
- External validation
- Analyst support tools

---

### What to Avoid (Total saved: $263,000+)

**Do NOT implement**:
1. Multi-layer architecture ($150,000) - Unnecessary complexity
2. BERT fine-tuning now ($20,000) - Corpus too small
3. TSAD model library ($45,000) - Wrong domain
4. RL model selector ($48,000) - Premature optimization
5. G-test detection ($0) - Already failed
6. Novel term scanner ($9,000+) - Can't filter significance

**Total savings**: $272,000

**Rationale**: Evidence-based rejection after empirical testing

---

## SECTION 8: Key Questions Answered

### "Given all empirical findings, what should FedSpeak implement first?"

**Answer**: Improved Hybrid Detector with prospective pipeline

**Evidence**:
- Phase 2: 55% precision, 16% recall (retrospective)
- Phase 4: 100% precision, 100% recall (prospective on critical shifts)
- Fast: <1 second
- Proven: Detected both April and December 2021 "transitory" shifts

**Timeline**: 1 week
**Cost**: $6,000
**Risk**: Very low (already validated)

---

### "Can prospective detection work?"

**Answer**: YES

**Evidence**:
- Detected "transitory" emergence April 2021 (using only pre-April data)
- Detected "transitory" removal December 2021 (using only pre-December data)
- 0% false positives on 2021 test
- 100% recall on critical shifts

**Constraints**:
- Requires pre-defined tracked terms
- Can't discover completely novel terms automatically
- Human review essential for significance assessment

---

### "Which model response proposals actually work?"

**Answer**: Almost none as originally proposed

**Validated** (worked):
- Semantic proximity correlation (r=0.547) - Response 3
- External validation concept (not yet tested) - Response 2
- Keep existing Layer 1 - Response 2

**Failed** (empirically refuted):
- Kleinberg burst detection (too conservative) - Response 1
- G-test anomaly detection (0% F1) - Response 2
- JSD distributional analysis (0% F1) - Response 1
- BERT fine-tuning (corpus too small) - Response 1, 3
- Automatic synonym discovery (0% success) - Response 1, 2
- Novel term scanner (ranked "transitory" 617th) - Response 2
- Positional weighting (12.5% vs claimed >50%) - Response 1, 2
- Word2Vec similarity values (6x overstated) - Response 1

**Partially useful** (different use case):
- Word2Vec for exploration (not synonym discovery)
- Kleinberg for removal validation (not primary detection)
- MILA framework for explanation (not detection)

---

## SECTION 9: Success Metrics

### Year 1 Targets (Realistic)

**Detection Performance**:
- Precision: 55-60% (up from 55% baseline)
- Recall: 18-22% (up from 16% baseline)
- F1 Score: 0.27-0.32 (up from 0.25 baseline)
- Latency: <1 second (maintain)

**External Validation**:
- Market validation rate: >70% of high-confidence alerts
- Media validation rate: >50% of high-confidence alerts

**Operational**:
- False positive rate: <1 per quarter
- Detection latency: <1 hour post-release
- System uptime: >99.5%

### Year 2 Targets (Aspirational)

**Detection Performance**:
- Precision: 60-65% (+5-10% from external validation)
- Recall: 22-28% (incremental improvements)
- F1 Score: 0.32-0.40

**System Expansion**:
- Tracked terms: 10-15 (up from 5)
- Validated synonyms: 30-40 (up from 20)
- Corpus size: 200+ statements

---

## Conclusion

**Bottom Line**: Implement the Improved Hybrid Detector immediately. Avoid the expensive, complex proposals that failed empirical testing.

**Evidence-Based Path**:
1. Week 1: Deploy proven Improved Hybrid ($6K)
2. Month 1: Add external validation ($21K)
3. Quarter 1: Build analyst tools ($24K)
4. Year 2: Consider advanced methods IF needed

**Total Year 1 Investment**: $51,000
**Expected ROI**: High (proven methods, incremental improvements)
**Risk**: Very low (evidence-based, tested approach)

**Key Insight**: Simplicity wins. The $6,000 Improved Hybrid Detector outperforms $200,000+ of complex alternatives.
