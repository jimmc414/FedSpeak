# Document 02: Ground Truth Catalog Plan

## Purpose

Build a catalog of documented Federal Reserve language shifts that have been identified by financial analysts, economists, and Fed watchers. These become test cases for validating our detection methods and inform what patterns we should look for.

## Questions to Answer

1. What specific language shifts have been documented by credible observers?
2. When did each shift occur (which meetings, which documents)?
3. What was the economic/policy context?
4. Are these substitutions (word A → word B), additions (new concept appears), or deletions (topic vanishes)?
5. Which document types contained the clearest signals?
6. Which shifts would be most valuable to detect going forward?

## Research Sources

### Primary Sources
- **Dave Collum's Year in Review** (2008-2024)
  - Search for sections on Federal Reserve, monetary policy, Fed criticism
  - Look for explicit mentions of Fed language changes
  - Archive location: Peak Prosperity website or Cornell chemistry department page

- **Grant's Interest Rate Observer**
  - If accessible, search archives for Fed language analysis
  - Known for tracking euphemisms and Fed-speak evolution

- **Mises Institute Articles**
  - Austrian economics perspective on Fed communications
  - Search terms: "Federal Reserve language", "Fed euphemism", "FOMC rhetoric"

### Secondary Sources
- **Financial media coverage** (WSJ, Bloomberg, Financial Times)
  - Search for articles about Fed "word changes" or "language shifts"
  - Bloomberg keyword: "Fed drops 'patient'" or similar historical searches
  
- **Economic blogs and commentary**
  - Zero Hedge Fed coverage (skeptical perspective aligns with project goals)
  - Calculated Risk blog (detailed Fed watchers)
  - Macro tourist, Real Vision commentators

### Academic/Historical Sources
- **Fed transcripts from 5+ years ago** (they're released with delay)
  - Search for internal discussions about how to phrase communications
  - May reveal intentional language choices
  - Available at: https://www.federalreserve.gov/monetarypolicy/fomc_historical.htm

## Catalog Structure

For each identified language shift, document:

### Shift Metadata
- **Shift ID:** Unique identifier (e.g., SHIFT-2008-QE-01)
- **Shift name:** Descriptive label ("QE Euphemism Adoption")
- **Timeframe:** When the shift occurred (Q4 2008 - Q1 2009)
- **Document type(s):** Where it appeared (FOMC statements, minutes, speeches)

### Language Change Details
- **Before phrase(s):** What language was used previously (or if concept was absent)
- **After phrase(s):** What language replaced it or appeared newly
- **Change type:** Substitution / Addition / Deletion / Reframing
- **Specific examples:** Direct quotes showing before/after

### Context
- **Economic conditions:** What was happening in markets/economy
- **Policy context:** What Fed action accompanied the language change
- **Significance:** Why this shift mattered (what it signaled or obscured)

### Validation
- **Source:** Citation to who documented this shift (link, article, date)
- **Verification status:** Confirmed by checking actual Fed documents vs. just reported
- **Document URLs:** Links to the actual Fed documents showing the shift

## Specific Shifts to Research

Priority historical shifts to investigate:

### 1. Quantitative Easing Era (2008-2009)
- When did "quantitative easing" first appear?
- Previous terms: "credit easing", "asset purchases", or nothing?
- Evolution to "large-scale asset purchases" (LSAP)
- Context: Post-Lehman, need to describe unprecedented bond buying

### 2. Taper Tantrum (2013)
- When did "reduce the pace of purchases" language appear?
- How was the wind-down communicated before explicit announcement?
- Market reaction to language changes

### 3. Policy Stance Changes (2018)
- Removal of "accommodative" from policy stance description
- Shift from "gradual increases" to other language
- Context: Interest rate normalization attempt

### 4. COVID Response (2020)
- "Whatever it takes" → "committed to using our full range of tools"
- Introduction of yield curve control discussion
- "Average inflation targeting" explanation evolution

### 5. Inflation Narrative (2021-2022)
- **CRITICAL SHIFT:** "Transitory" inflation language
  - When it first appeared
  - How long it persisted
  - When it disappeared
  - What replaced it ("persistent price pressures", "elevated inflation")
- This is the most important recent example

### 6. Data Dependency (Various)
- Evolution from "data dependent" to "meeting by meeting"
- Changes in how forward guidance is qualified

### 7. M3 Discontinuation (2006)
- What language preceded the decision to stop publishing M3?
- How was it justified in communications?
- Context: Hiding money supply growth

### 8. Balance Sheet Language
- Shifts in how balance sheet reduction is described
- "Runoff" vs "quantitative tightening" vs other terms

## Analysis Tasks

### 1. Shift Collection
Target: 10-15 well-documented shifts with strong sources

For each shift:
- Locate the original Fed documents
- Extract the relevant text passages
- Verify the shift actually occurred as reported
- Document the context

### 2. Classification
Categorize shifts by type:
- **Substitution:** Word A replaced with Word B
- **Addition:** New concept/phrase introduced
- **Deletion:** Topic stops being mentioned
- **Reframing:** Same concept described differently

Count frequency of each type to understand common patterns.

### 3. Timeline Mapping
Create chronological view:
- When do shifts cluster? (Often around policy regime changes)
- How much lead time before formal policy changes?
- Are there patterns in timing (specific meetings, specific economic conditions)?

### 4. Document Type Analysis
Which document types show shifts earliest?
- Do statements lead minutes?
- Do speeches preview official communications?
- Are transcripts (released later) useful for understanding intent?

### 5. Pattern Identification
Look for meta-patterns:
- Do shifts follow a predictable sequence? (Speeches → Statements → Minutes?)
- Are there warning signs before major shifts?
- Common linguistic techniques (euphemism, technical jargon, vagueness)?

## Deliverable Format

Create `02-shifts.md` with the following sections:

### 1. Executive Summary
- How many shifts were identified and validated?
- What types of shifts are most common?
- Key findings about patterns

### 2. Complete Shift Catalog

Table format:
| Shift ID | Name | Timeframe | Type | Before → After | Source | Status |
|----------|------|-----------|------|----------------|--------|--------|

Followed by detailed write-ups for 5-7 major shifts including:
- Full context
- Direct quotes from Fed documents
- Before/after comparison
- Why it matters

### 3. Shift Classification Analysis
- Distribution by type (substitution/addition/deletion)
- Most common patterns observed
- Examples of each category

### 4. Timeline Visualization
Chronological list or chart showing when shifts occurred relative to:
- Major economic events
- Fed policy changes
- Market reactions

### 5. Document Type Analysis
Which Fed communications show shifts first:
- FOMC statements
- Meeting minutes
- Press conference transcripts
- Board speeches
- Beige Books

### 6. Validation Notes
For each shift:
- Verification status (confirmed by checking actual documents)
- Source credibility assessment
- Any discrepancies between reports and actual documents

### 7. Test Case Selection

**Recommend 2-3 shifts as test cases for Document 03:**

**Primary test case:** Should be:
- Well-documented
- Clear before/after transition
- Occurred in documents from Document 01 analysis
- Representative of common shift patterns

**Secondary test case:** Should be:
- More subtle or complex
- Tests detection limits
- Different type than primary case

Explain why these were chosen.

### 8. Hypothesis & Recommendations

Based on catalog analysis:
- What patterns should the detection tool look for?
- What shift types are most feasible to detect automatically?
- What shift types might require manual analysis?

**Guide for Document 03:**
- Specific shifts to use for testing
- What would constitute successful detection
- What false positives to watch for

## Time Estimate

6-8 hours:
- 2-3 hours: Source research and identification
- 2-3 hours: Document verification and text extraction
- 1-2 hours: Analysis and pattern identification
- 1 hour: Documentation and test case selection

## Tools Needed

- Web browser with good bookmarking
- Access to Fed document archives
- Text editor for quote extraction
- Spreadsheet or markdown tables for catalog
- PDF viewer for reading Fed documents

## Success Criteria

Document 02 is complete when you can answer:
1. "What language shifts should we be able to detect?" (with specific examples)
2. "What do these shifts look like?" (with before/after text)
3. "Which shifts should we test our detection methods against?" (with rationale)

The catalog provides ground truth for evaluating any NLP approach in Document 03.

## Notes on Source Quality

**Strong sources** (prioritize):
- Direct quotes from Fed documents showing the shift
- Analysis from financial professionals who track Fed closely
- Academic papers on Fed communication
- Contemporaneous market commentary

**Weak sources** (use with caution):
- Unsubstantiated claims without document references
- Conspiracy theories without evidence
- Second-hand reports without original sources

Always verify reported shifts by checking actual Fed documents.

---

*This plan may be adjusted based on findings from Document 01 about which documents are most accessible.*
