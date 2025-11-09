# FedSpeak User Guide

**Version**: 1.0
**Last Updated**: November 9, 2025
**Audience**: Analysts, Researchers, Policy Observers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding the System](#understanding-the-system)
4. [Using the Dashboard](#using-the-dashboard)
5. [Interpreting Alerts](#interpreting-alerts)
6. [Word2Vec Explorer](#word2vec-explorer)
7. [MILA Stance Analysis](#mila-stance-analysis)
8. [Alert Tiers & Confidence Levels](#alert-tiers--confidence-levels)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Introduction

### What is FedSpeak?

FedSpeak is an automated system that detects and analyzes language shifts in Federal Reserve FOMC (Federal Open Market Committee) policy statements. It monitors every new FOMC statement, identifies statistically significant changes in language usage, and enriches alerts with:

- **Market validation** (treasury yields, VIX, S&P 500 reactions)
- **Media coverage analysis** (news volume, source diversity, sentiment)
- **LLM-powered stance classification** (hawkish/dovish/neutral)
- **Semantic similarity tools** (Word2Vec exploration)

### Why Use FedSpeak?

**For Policy Analysts**:
- Detect subtle shifts in Fed communication before markets fully react
- Track evolution of key policy terms ("transitory," "accommodative," etc.)
- Understand multi-signal validation (language + markets + media + LLM)

**For Researchers**:
- Analyze historical language shifts (200+ FOMC statements since 2006)
- Explore semantic relationships in Federal Reserve policy language
- Access structured data exports for quantitative research

**For Investors**:
- High-precision alerts (Tier 1: 70-75% precision)
- Early warning system for policy pivots
- Multi-dimensional validation reduces false positives

### System Capabilities

**What FedSpeak Detects**:
- ✅ **Emergence**: Term appears in statement (previously absent)
- ✅ **Escalation**: Term frequency increases significantly
- ✅ **Removal**: Term disappears from statement
- ✅ **De-escalation**: Term frequency decreases significantly

**What FedSpeak Provides**:
- Real-time monitoring (RSS feed checked every 5 minutes)
- Automated email alerts (configurable)
- Interactive web dashboard with filtering and export
- Historical analysis and visualization
- API access for programmatic queries

### Working with Claude Code

**Claude Code as Your Assistant:**

Claude Code (Anthropic's official CLI AI assistant) can help you use FedSpeak in two distinct and independent ways:

**1. As an Autonomous Operator**
Claude Code can set up, run, monitor, and maintain FedSpeak on your behalf. Simply ask Claude Code to operate the system and it will handle all technical details:
- Environment setup and dependency installation
- Configuration and API key setup
- Starting and monitoring services
- Troubleshooting issues
- Analyzing results and generating reports

**2. As the AI Inference Provider**
When configured with the "all 9s" API key pattern (`sk-ant-999999999999`), Claude Code Max provides the AI analysis for MILA stance classification instead of calling Anthropic's cloud API. This:
- Eliminates API costs during development
- Enables offline operation
- Provides the same quality hawkish/dovish analysis

**These roles are independent**: Claude Code can operate FedSpeak regardless of whether it's also providing the AI inference. You can use either role, both, or neither depending on your needs.

For detailed autonomous operation protocols, see [AGENT_GUIDE.md](../AGENT_GUIDE.md).

---

## Getting Started

### Accessing the System

**Dashboard URL**: `http://localhost:5000` (local development)

**Available Interfaces**:
1. **Main Dashboard** (`/`) - View and filter alerts
2. **Word2Vec Explorer** (`/explore`) - Semantic analysis tools
3. **MILA Stance Analysis** (`/explainability`) - LLM-powered insights

### First Time Setup (User Perspective)

1. **Open your browser** → Navigate to http://localhost:5000
2. **Review the main dashboard** → See recent alerts
3. **Explore the Word2Vec tool** → Click "Word2Vec Explorer" in navigation
4. **Check stance analysis** → Click "Stance Analysis" (if MILA is enabled)

**Note**: If you get a "Service Unavailable" error, the system administrator needs to start the dashboard:
```bash
python src/dashboard/app.py
```

### Dashboard Overview

**Navigation Bar**:
```
┌────────────────────────────────────────────────────────────┐
│  FedSpeak  |  Dashboard  |  Word2Vec  |  Stance Analysis │
└────────────────────────────────────────────────────────────┘
```

**Main Dashboard Components**:
- **Filter Panel**: Filter by confidence, tier, shift type, term, date range
- **Alert List**: Cards showing recent detections
- **Pagination**: Navigate through alerts (default: 20 per page)
- **Export Buttons**: CSV and JSON export

**Keyboard Shortcuts**:
- `Ctrl+F` or `Cmd+F`: Search within page
- `Click on alert card`: View full alert details

---

## Understanding the System

### How FedSpeak Works

```
1. RSS Monitoring (Every 5 minutes)
   ↓
2. New Statement Detection
   ↓
3. Statistical Shift Detection
   ├→ Emergence (term appears)
   ├→ Escalation (frequency increases)
   ├→ Removal (term disappears)
   └→ De-escalation (frequency decreases)
   ↓
4. Multi-Signal Validation
   ├→ Market Data (FRED + Yahoo Finance)
   ├→ Media Coverage (GDELT + FinBERT)
   └→ LLM Stance (Claude 3.5 Sonnet)
   ↓
5. Tier Assignment (1, 2, or 3)
   ↓
6. Alert Distribution (Email + Dashboard)
```

### Monitored Terms

FedSpeak tracks high-priority policy terms including:

**Inflation-Related**:
- "transitory" - Describes temporary inflation (removed Dec 2021 = major shift)
- "elevated" - Inflation level descriptor
- "persistent" - Inflation duration descriptor

**Policy Stance**:
- "accommodative" - Supportive monetary policy
- "patient" - Gradual approach to rate changes
- "restrictive" - Tightening monetary policy

**Forward Guidance**:
- "considerable time" - Time horizon for policy changes
- "data-dependent" - Policy contingent on economic data

**Employment/Growth**:
- "maximum employment" - Employment goal
- "inflation expectations" - Anchoring expectations

**Complete list**: See `config/config.yaml` under `keywords` section

### Shift Detection Algorithm

**Improved Hybrid Detector** (validated):
- **Precision**: 53.8% overall, 70-75% for Tier 1 alerts
- **Recall**: 16.2% (conservative, low false positive rate)
- **Methodology**: Bayesian-inspired hypothesis testing with context windows

**How it works**:
1. Calculate baseline frequency (rolling average of previous 5 statements)
2. Compare current frequency to baseline
3. Use Bayesian hypothesis testing to determine if shift is statistically significant
4. Classify shift type (emergence, escalation, removal, de-escalation)
5. Assign confidence level (high, medium, low)

**Example**:
- Term: "transitory"
- Baseline (Nov 2021): 2 mentions per statement (average of previous 5)
- Current (Dec 2021): 0 mentions
- **Detection**: Removal, High Confidence
- **Tier**: 1 (validated by markets + media + MILA)

---

## Using the Dashboard

### Main Dashboard

**Accessing**: http://localhost:5000

#### Filtering Alerts

**Filter Panel** (top of page):

1. **Confidence**: `All | High | Medium | Low`
   - **High**: Most reliable (used for Tier 1/2)
   - **Medium**: Moderate confidence
   - **Low**: Low confidence (informational only)

2. **Tier**: `All | Tier 1 | Tier 2 | Tier 3`
   - **Tier 1**: Triple validated (statistical + market + media) - 70-75% precision
   - **Tier 2**: Dual validated (statistical + market OR statistical + media) - 55-65% precision
   - **Tier 3**: Single signal (statistical only) - 30-45% precision

3. **Shift Type**: `All | Emergence | Escalation | Removal | De-escalation`

4. **Term**: Dropdown of all monitored terms

5. **Date Range**: From/to date pickers

**Example Use Cases**:

**Use Case 1: Find high-precision alerts**
```
Filters: Tier = "Tier 1", Confidence = "High"
Result: Highest quality alerts (70-75% precision)
```

**Use Case 2: Track evolution of "transitory"**
```
Filters: Term = "transitory", All tiers
Result: All detections for "transitory" across history
```

**Use Case 3: See recent emergent terms**
```
Filters: Shift Type = "Emergence", Last 6 months
Result: New terms appearing in FOMC language
```

#### Reading Alert Cards

**Alert Card Components**:

```
┌───────────────────────────────────────────────┐
│ SHIFT DETECTED                                │
│                                               │
│ Term: "transitory"                            │
│ Type: Removal                                 │
│ Date: December 15, 2021                       │
│                                               │
│ Confidence: HIGH    Tier: 1 (Tier 1)         │
│                                               │
│ Change: 2.0 → 0                               │
│ Market Validated: ✓                           │
│ Media Validated: ✓                            │
│ MILA: Hawkish (score: 0.78)                   │
│                                               │
│ [View Details]                                │
└───────────────────────────────────────────────┘
```

**Card Elements**:
- **Term**: Which policy term changed
- **Type**: Emergence | Escalation | Removal | De-escalation
- **Date**: FOMC statement date (YYYYMMDD format)
- **Confidence**: Statistical confidence (High/Medium/Low)
- **Tier**: Multi-signal tier (1/2/3)
- **Change**: Previous avg → Current count (e.g., "2.0 → 0" means removed)
- **Market Validated**: ✓ if market data confirms shift
- **Media Validated**: ✓ if media coverage confirms shift
- **MILA**: LLM stance classification (if available)

#### Alert Details Page

**Accessing**: Click "View Details" on any alert card

**Details Page Sections**:

1. **Alert Summary**
   - Alert ID, timestamp, shift type, term
   - Confidence level and tier assignment

2. **Change Statistics**
   - Previous average frequency
   - Current count
   - Percent change
   - Statistical significance score

3. **Market Validation** (if available)
   - Treasury yield changes (2-year, 10-year)
   - VIX change (volatility index)
   - S&P 500 change
   - Overall market score
   - Validated: Yes/No

4. **Media Coverage** (if available)
   - News article count
   - Source diversity (number of unique news sources)
   - Hybrid sentiment score (GDELT + FinBERT)
   - Validated: Yes/No

5. **MILA Stance Analysis** (if available)
   - Stance: Hawkish | Dovish | Neutral
   - Score: -1.0 (very dovish) to +1.0 (very hawkish)
   - Confidence: LLM confidence in classification
   - Key phrases: Terms that influenced classification
   - Explanation: Why the LLM classified this way

6. **Detection Metadata**
   - Baseline window used
   - Hypothesis test results
   - Bayesian factors

#### Exporting Data

**CSV Export**:
1. Apply filters to select desired alerts
2. Click "Export CSV" button
3. Opens `alerts.csv` in your downloads

**CSV Columns**:
- alert_id, timestamp, term, shift_type
- document_date, confidence, tier
- previous_avg, current_count, change_pct
- market_validated, media_validated
- mila_stance, mila_score

**JSON Export**:
1. Apply filters
2. Click "Export JSON" button (or use API: `/api/alerts`)
3. Full alert data including all metadata

**Use Cases**:
- Import into Excel/R/Python for analysis
- Create custom visualizations
- Merge with proprietary data
- Historical backtesting

#### Pagination

**Controls**: Bottom of alert list
- "Previous" / "Next" buttons
- Page number (e.g., "Page 2 of 15")
- Alerts per page: Configurable in `config.yaml` (default: 20)

---

## Interpreting Alerts

### Confidence Levels

**High Confidence**:
- **What it means**: Statistical evidence is very strong
- **Precision**: 50-60% (standalone), 70-75% (with multi-signal validation)
- **When to act**: Review immediately, especially if Tier 1
- **Example**: "transitory" removal in Dec 2021

**Medium Confidence**:
- **What it means**: Statistical evidence is moderate
- **Precision**: 30-45%
- **When to act**: Monitor for follow-up signals
- **Example**: Minor term frequency changes

**Low Confidence**:
- **What it means**: Weak statistical evidence
- **Precision**: 10-25%
- **When to act**: Informational only, low priority
- **Example**: Single-occurrence terms

### Tier System (Multi-Signal Validation)

**Tier 1: Triple Validated** (🥇 Gold Standard)
- **Signals**: Statistical + Market + Media
- **Precision**: 70-75%
- **Meaning**: High statistical confidence + market reaction + media coverage
- **Action**: High priority, likely significant policy shift
- **Example**: Dec 2021 "transitory" removal
  - Statistical: High confidence
  - Market: Treasury yields rose, VIX increased
  - Media: 100+ articles, 30+ sources, hawkish sentiment
  - MILA: Hawkish stance (score: 0.78)

**Tier 2: Dual Validated** (🥈 Strong Evidence)
- **Signals**: Statistical + (Market OR Media)
- **Precision**: 55-65%
- **Meaning**: High statistical confidence + one external signal
- **Action**: Medium priority, monitor closely
- **Example**: Minor policy language adjustments with some market reaction

**Tier 3: Single Signal** (🥉 Informational)
- **Signals**: Statistical only OR low confidence
- **Precision**: 30-45%
- **Meaning**: Statistical detection without external confirmation
- **Action**: Low priority, context-dependent
- **Example**: Technical term changes, minor wording shifts

### Shift Types

**Emergence** (🟢 New Term Appears)
- **What it means**: Term was absent, now present
- **Interpretation**: Fed introducing new concept/priority
- **Example**: "transitory" emergence in April 2021
  - Fed acknowledging inflation surge
  - Signaled temporary view of inflation

**Escalation** (🔼 Frequency Increases)
- **What it means**: Term used more frequently
- **Interpretation**: Fed emphasizing existing concept
- **Example**: "inflation" mentions increase
  - Rising concern about inflation
  - Elevated priority in policy discussions

**Removal** (🔴 Term Disappears)
- **What it means**: Term was present, now absent
- **Interpretation**: Fed de-prioritizing or abandoning concept
- **Example**: "transitory" removal in Dec 2021
  - Fed abandoning temporary inflation narrative
  - Shift to acknowledging persistent inflation
  - **Major market impact**

**De-escalation** (🔽 Frequency Decreases)
- **What it means**: Term used less frequently
- **Interpretation**: Fed reducing emphasis on concept
- **Example**: "accommodative" de-escalation
  - Gradual normalization of policy stance
  - Preparing markets for less supportive policy

### Recommended Actions by Alert Type

**Tier 1 + High Confidence + Removal/Emergence**:
- ✅ Review immediately
- ✅ Read full FOMC statement
- ✅ Check market reaction (yields, VIX, equity futures)
- ✅ Review MILA explanation for policy implications
- ✅ Consider portfolio implications

**Tier 2 + High Confidence**:
- ✅ Review within 24 hours
- ✅ Monitor for follow-up signals
- ✅ Check if media coverage increases
- ⚠️ Not necessarily actionable yet

**Tier 3 or Low Confidence**:
- ℹ️ Informational only
- ℹ️ Track for patterns
- ⚠️ Do not trade on these alone

### False Positive Examples

FedSpeak is designed to minimize false positives, but they still occur:

**Common False Positives**:
1. **Technical language changes**: "Committee" → "FOMC" (same meaning)
2. **Contextual synonyms**: "elevated" → "high" (similar meaning)
3. **Seasonal terminology**: "year-end" appearing in December statements
4. **Data artifacts**: OCR errors in historical statements

**How to Identify**:
- Check MILA explanation (LLM often catches semantic equivalence)
- Read full statement in context
- Compare to previous statements
- Look for Tier 1/2 validation (multi-signal reduces false positives)

---

## Word2Vec Explorer

### What is Word2Vec?

Word2Vec is a machine learning model that learns semantic relationships between words by analyzing how they're used in context. FedSpeak includes a Word2Vec model trained on 200+ FOMC statements (2006-2023).

**What it enables**:
- Find semantically similar terms
- Discover synonyms used by the Fed
- Calculate "policy proximity" (how close a term is to core policy concepts)
- Explore term evolution over time

### Accessing Word2Vec Explorer

**URL**: http://localhost:5000/explore

**Interface Components**:
1. **Search Bar**: Enter term to analyze
2. **Autocomplete**: Real-time suggestions as you type
3. **Similar Words Chart**: Top 10 most similar terms (bar chart)
4. **Policy Proximity Gauge**: How policy-relevant the term is (0-1 scale)

### Using the Explorer

**Step 1: Enter a term**
```
Search box: Type "inflation"
Autocomplete suggests: inflation, price, elevated, transitory
```

**Step 2: View similar words**
```
Similar Words (top 5):
1. prices       (0.89 similarity)
2. price        (0.85 similarity)
3. elevated     (0.78 similarity)
4. wage         (0.72 similarity)
5. cost         (0.68 similarity)
```

**Interpretation**:
- Similarity score: 0-1 (1 = identical, 0 = unrelated)
- High similarity (>0.7): Strong semantic relationship
- Medium (0.5-0.7): Moderate relationship
- Low (<0.5): Weak relationship

**Step 3: Check policy proximity**
```
Policy Proximity: 0.82 (High)
```

**Policy Proximity Scale**:
- **0.8-1.0**: Core policy term (inflation, employment, rates)
- **0.6-0.8**: Policy-relevant (wages, prices, growth)
- **0.4-0.6**: Moderately relevant (consumer, business, household)
- **0.0-0.4**: Weakly relevant (technical, procedural terms)

### Use Cases

**Use Case 1: Find Fed synonyms**
```
Question: "What terms does the Fed use instead of 'inflation'?"
Steps:
1. Search "inflation"
2. View similar words: prices, elevated, cost, wage
3. Interpretation: Fed uses multiple terms to describe inflation dynamics
```

**Use Case 2: Understand term relationships**
```
Question: "Is 'transitory' related to policy stance?"
Steps:
1. Search "transitory"
2. Check policy proximity: 0.45 (Moderate)
3. Similar words: temporary, short-lived, sustained (opposite)
4. Interpretation: Descriptive term, not core policy lever
```

**Use Case 3: Discover emerging themes**
```
Question: "What's semantically close to 'labor'?"
Steps:
1. Search "labor"
2. Similar words: employment, job, worker, wage, hiring
3. Interpretation: Fed views labor through employment/wage lens
```

### Limitations

**What Word2Vec Cannot Do**:
- ❌ Understand context (e.g., "patient" the adjective vs. "patient" the noun)
- ❌ Detect sentiment (hawkish vs. dovish requires MILA)
- ❌ Track temporal changes (model is static, trained on all data)

**When to use MILA instead**:
- Need sentiment/stance analysis (hawkish/dovish)
- Want explanation of policy implications
- Require confidence scores

---

## MILA Stance Analysis

### About Claude Code's Inference Role

When MILA is configured to use "Claude Code Max Local Routing," Claude Code Max (the AI assistant you may already be talking to) becomes the inference engine that analyzes FOMC statements. This is completely separate from Claude Code's ability to operate FedSpeak on your behalf.

**Two Independent Relationships:**
- **Claude Code as operator**: Can set up and run FedSpeak autonomously (see [Working with Claude Code](#working-with-claude-code))
- **Claude Code as inference provider**: Performs MILA stance analysis when configured with "all 9s" API key

Both, either, or neither can be active depending on your configuration. For example:
- Claude Code can operate FedSpeak while MILA uses Anthropic's cloud API
- You can manually operate FedSpeak while Claude Code provides MILA inference
- Claude Code can do both (operate the system AND provide inference)
- Neither (you operate manually and use cloud API)

### MILA Configuration

MILA requires an Anthropic API key. FedSpeak supports two routing modes:

**Option 1: Anthropic Cloud API (Production)**
- Set `ANTHROPIC_API_KEY="sk-ant-api03-YOUR_ACTUAL_KEY"` (get from https://console.anthropic.com)
- Cost: ~$0.003 per statement (<$5/year ongoing)
- Best for: Production deployments, guaranteed uptime

**Option 2: Claude Code Max Local Routing (Development)**
- Set `ANTHROPIC_API_KEY="sk-ant-999999999999"` (all 9s signals local routing)
- Cost: Free (uses Claude Code Max subscription)
- Best for: Development, testing, avoiding API costs

The system automatically detects which mode to use based on the API key pattern. If no key is set, MILA is disabled (other features continue working).

### What is MILA?

**MILA** (Monetary Insight via LLM Analysis) uses Claude 3.5 Sonnet to classify FOMC statements as:
- **Hawkish**: Tightening bias (raise rates, reduce stimulus)
- **Dovish**: Easing bias (lower rates, increase stimulus)
- **Neutral**: Balanced, no clear directional bias

**How it works**:
1. Fed statement is sent to Claude 3.5 Sonnet
2. LLM analyzes language, context, and policy implications
3. Returns stance, score (-1 to +1), confidence, and explanation
4. Results cached for 365 days (FOMC statements are immutable)

### Accessing MILA Dashboard

**URL**: http://localhost:5000/explainability

**Requirements**: `ANTHROPIC_API_KEY` environment variable must be set

**If not configured**:
- Dashboard shows "503 Service Unavailable"
- Contact system administrator to set API key

### Using MILA Dashboard

**Main Interface**:

1. **Statement Selector**: Dropdown with 200+ FOMC statements
2. **Stance Gauge**: Visual indicator (hawkish ← → dovish)
3. **Stance Details**:
   - Stance: Hawkish | Neutral | Dovish
   - Score: -1.0 (very dovish) to +1.0 (very hawkish)
   - Confidence: LLM confidence (0-1)
4. **Key Phrases**: Terms that influenced classification
5. **Explanation**: Why the LLM classified this way
6. **Historical Timeline**: Stance evolution over time

**Example Analysis**:

```
Statement: December 15, 2021
Stance: Hawkish
Score: 0.78
Confidence: 0.92

Key Phrases:
- "faster taper"
- "transitory no longer appropriate"
- "inflation risks elevated"
- "committee prepared to adjust"

Explanation:
The statement signals a clear hawkish shift. The removal of
"transitory" indicates the Fed no longer views inflation as
temporary. The "faster taper" language and discussion of
"adjusting the stance of policy" suggest rate increases are
forthcoming. Elevated inflation risks and preparedness to
act reinforce the tightening bias.
```

**Interpretation**:
- **Score 0.78**: Clearly hawkish (>0.5)
- **Confidence 0.92**: LLM is very confident
- **Key Phrases**: Support hawkish interpretation
- **Explanation**: Actionable policy insight

### Stance Score Interpretation

**Hawkish Range** (0.5 to 1.0):
- **0.8-1.0**: Very hawkish (imminent tightening)
- **0.5-0.8**: Moderately hawkish (tightening bias)

**Dovish Range** (-1.0 to -0.5):
- **-1.0 to -0.8**: Very dovish (imminent easing)
- **-0.8 to -0.5**: Moderately dovish (easing bias)

**Neutral Range** (-0.5 to 0.5):
- **-0.5 to -0.2**: Slightly dovish lean
- **-0.2 to 0.2**: Truly neutral (balanced)
- **0.2 to 0.5**: Slightly hawkish lean

**Historical Context**:
- 2008 Financial Crisis: Very dovish (-0.9 to -1.0)
- 2015-2018 Normalization: Moderately hawkish (0.5-0.7)
- 2019-2020 Pandemic: Very dovish (-0.8 to -1.0)
- 2021-2023 Inflation Fight: Very hawkish (0.7-0.9)

### Statement Comparison Tool

**Accessing**: http://localhost:5000/explainability/compare

**Features**:
1. **Dual Statement Selector**: Choose two statements to compare
2. **Side-by-Side Stance Cards**: Compare scores and stances
3. **Text Comparison**: View full text side-by-side
4. **Diff View**: Git-style diff highlighting changes
5. **Toggle View**: Switch between side-by-side and diff

**Use Case**: Track stance evolution

```
Compare:
- Statement A: November 3, 2021 (Score: 0.45 - Neutral/Slightly Hawkish)
- Statement B: December 15, 2021 (Score: 0.78 - Hawkish)

Diff highlights:
- Added: "faster taper", "prepared to adjust"
- Removed: "transitory", "accommodative"

Interpretation: Clear hawkish shift in one month
```

### MILA Limitations

**What MILA Cannot Do**:
- ❌ Predict future policy (only analyzes current statement)
- ❌ Guarantee accuracy (70-80% accuracy on stance classification)
- ❌ Replace human judgment (use as tool, not oracle)

**When MILA is Most Useful**:
- ✅ Quickly assess overall tone of new statement
- ✅ Identify key phrases for manual review
- ✅ Track stance evolution over time
- ✅ Generate hypotheses for deeper analysis

---

## Alert Tiers & Confidence Levels

### Understanding the Tier System

**Why Tiers Matter**:
- Not all detections are equally reliable
- Multi-signal validation improves precision
- Tier system helps prioritize alerts

**Tier Assignment Logic**:

```
IF statistical_confidence == "high":
    IF market_validated AND media_validated:
        tier = 1  # Triple signal (70-75% precision)
    ELSE IF market_validated OR media_validated:
        tier = 2  # Dual signal (55-65% precision)
    ELSE:
        tier = 3  # Single signal (30-45% precision)
ELSE:  # medium or low confidence
    tier = 3  # Low confidence (30-45% precision)
```

### Precision vs. Recall Trade-off

FedSpeak is tuned for **high precision** (low false positives):
- **Precision**: 53.8% overall, 70-75% for Tier 1
- **Recall**: 16.2% (intentionally low)

**What this means**:
- ✅ Most Tier 1 alerts are real shifts (low false positive rate)
- ⚠️ Some real shifts may not trigger alerts (higher false negative rate)
- 💡 Trade-off is intentional: better to miss some shifts than flood analysts with false alarms

**Practical Impact**:
- Trust Tier 1 alerts (70-75% reliable)
- Use Tier 2 as "watch list" (55-65% reliable)
- Tier 3 is informational (30-45% reliable)

### Historical Performance

**Validation Data** (130 ground truth shifts):
- **Overall Precision**: 53.8%
- **Overall Recall**: 16.2%
- **F1 Score**: 0.249

**December 2021 Prospective Test**:
- **Recall**: 100% (detected "transitory" removal)
- **Precision**: N/A (only one shift in test period)

**Tier 1 Performance** (estimated from backtests):
- **Precision**: 70-75%
- **Recall**: ~10-12%
- **Interpretation**: Very reliable when it fires, but conservative

---

## Best Practices

### For Policy Analysts

**Daily Routine**:
1. Check dashboard for new Tier 1 alerts
2. Review any high-confidence detections
3. For Tier 1 alerts:
   - Read full FOMC statement
   - Check MILA explanation
   - Review market validation data
   - Compare to previous statement using comparison tool

**Weekly Routine**:
1. Review Tier 2 alerts from past week
2. Check Word2Vec for emerging term relationships
3. Export alert data for weekly report
4. Monitor historical stance timeline for trends

**When New FOMC Statement Released**:
1. Wait 2-6 hours for full multi-signal validation
2. Check dashboard for alerts
3. If Tier 1 alert:
   - Immediate review
   - Draft briefing note
   - Share with team
4. If Tier 2:
   - Monitor for follow-up signals
   - Add to watchlist
5. If Tier 3 or no alert:
   - Review statement manually (system may have missed shift)
   - Use MILA to check overall stance

### For Researchers

**Data Export**:
1. Use API endpoint for programmatic access
2. Export full dataset as JSON
3. Merge with proprietary data sources
4. Run custom statistical analyses

**Backtesting**:
1. Export all Tier 1 alerts
2. Cross-reference with market data
3. Calculate precision/recall for your use case
4. Adjust tier thresholds if needed (in config.yaml)

**Validation**:
1. Manually review sample of Tier 1 alerts
2. Check for false positives/negatives
3. Compare MILA stance to your own classification
4. Provide feedback for system improvement

### For Investors

**Risk Management**:
- ⚠️ Never trade solely on FedSpeak alerts
- ✅ Use as one input among many
- ✅ Cross-reference with other Fed communication (press conferences, minutes)
- ✅ Monitor for confirmation in market data

**Alert Integration**:
1. Set up email alerts for Tier 1 only
2. Create watchlist for Tier 2 alerts
3. Use MILA stance as sentiment indicator
4. Track stance evolution as leading indicator

**When to Act**:
- Tier 1 + Removal/Emergence → High priority
- Tier 1 + Escalation → Medium priority
- Tier 2 → Monitor
- Tier 3 → Ignore (unless you have specific use case)

---

## FAQ

**Q: How often does FedSpeak check for new statements?**
A: Every 5 minutes. FOMC typically publishes 8-10 statements per year.

**Q: Why am I not seeing any alerts?**
A: FOMC statements are infrequent (~8-10/year). Check the date range filter or view "All time" to see historical alerts.

**Q: What does "cached" mean in MILA?**
A: MILA caches results for 365 days. If you see "cached: true", it means the analysis was done previously and retrieved from cache (no new API call).

**Q: Why is MILA showing "Service Unavailable"?**
A: MILA requires an Anthropic API key. Contact your system administrator to configure `ANTHROPIC_API_KEY`.

**Q: Can I add custom terms to monitor?**
A: Yes, edit `config/config.yaml` and add terms to the `keywords` section. Requires system restart.

**Q: How accurate is the tier system?**
A: Tier 1 is 70-75% precise (based on backtests). Tier 2 is 55-65%. Tier 3 is 30-45%.

**Q: What if I find a false positive?**
A: Review the alert details, check MILA explanation, and compare to the full statement. False positives are expected (~25-30% for Tier 1).

**Q: Can I export all alerts to Excel?**
A: Yes, click "Export CSV" to download all filtered alerts as a CSV file compatible with Excel.

**Q: What's the difference between confidence and tier?**
A: **Confidence** is statistical (from detector). **Tier** combines statistical + market + media signals.

**Q: Why did FedSpeak miss a shift I noticed manually?**
A: FedSpeak has 16.2% recall (intentionally conservative). It's tuned for precision over recall to minimize false positives.

**Q: Can I get alerts via email?**
A: Yes, if email is configured. Contact your system administrator to enable email distribution.

**Q: How much does MILA cost to run?**
A: ~$0.60 for initial 200 statement analysis, ~$0.03/month ongoing (cached results).

**Q: Is the Word2Vec model updated automatically?**
A: No, it's trained on historical data (2006-2023). Contact administrator to retrain with new data.

**Q: What does a negative MILA score mean?**
A: Negative = dovish, Positive = hawkish. Score ranges from -1.0 (very dovish) to +1.0 (very hawkish).

**Q: Can I use the API programmatically?**
A: Yes, see [API Documentation](API_DOCUMENTATION.md) for full endpoint reference.

**Q: What is Claude Code and how does it relate to FedSpeak?**
A: Claude Code is Anthropic's official CLI AI assistant. It has two relationships with FedSpeak:
   1. **As autonomous operator**: Claude Code can set up, run, and maintain FedSpeak on your behalf
   2. **As inference provider**: When API key is set to "sk-ant-999999999999", Claude Code Max provides the AI analysis for MILA
   These roles are independent - you can use either, both, or neither.

**Q: Can Claude Code run FedSpeak for me automatically?**
A: Yes! Claude Code can autonomously operate the entire FedSpeak system. Just ask Claude Code to set up and monitor FedSpeak, and it will handle environment setup, configuration, monitoring, and analysis. See AGENT_GUIDE.md for technical details.

**Q: What's the difference between Claude Code operating FedSpeak vs. providing inference?**
A:
   - **Operating**: Claude Code acts as the human user, running commands and managing the system
   - **Inference**: Claude Code acts as the AI model that analyzes FOMC statements (when configured with "all 9s" API key)
   They're separate roles that can be used independently or together.

**Q: If I'm using Claude Code to operate FedSpeak, should I use local routing?**
A: It's recommended for development. Set `ANTHROPIC_API_KEY="sk-ant-999999999999"` to:
   - Avoid API costs during development/testing
   - Use your existing Claude Code Max subscription
   - Keep everything local (no cloud API calls)
   For production, you may want cloud API routing for guaranteed availability.

---

## Support & Feedback

**For questions or issues**:
1. Check this User Guide first
2. Review [Production Runbook](PRODUCTION_RUNBOOK.md) for technical details
3. Check GitHub issues: https://github.com/jimmc414/FedSpeak/issues
4. Create new issue with detailed description

**Providing Feedback**:
- Found a false positive? Please report it with alert ID
- Suggestions for new features? Open a feature request
- Questions about usage? Open a discussion

---

**End of User Guide**

*Version 1.0 | Last Updated: November 9, 2025*
*For technical details, see: Production Runbook | API Documentation*
