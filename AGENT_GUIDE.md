# FedSpeak Agent Guide

**Operational guide optimized for AI agents (Claude Code, autonomous systems)**

This guide is structured for programmatic execution with explicit state checks, success criteria, and decision logic.

---

## Quick Context

**What is FedSpeak:**
- Detects Federal Reserve language shifts in FOMC communications
- Tracks 5 keywords + synonyms (transitory, accommodative, patient, considerable time, full range of tools)
- Uses 4-stage pipeline: Download → Extract → Analyze → Detect
- Outputs: JSON alerts, text alerts, timeline visualizations

**Key capabilities:**
- 0-day detection lag (detects shifts same day they occur)
- 100% validated accuracy on test cases
- Synonym group tracking (e.g., "transitory" + "transient" + "temporary")
- Auto-resume downloads, real FOMC calendar, progress bars

---

## Environment Check Protocol

**Before starting, verify environment state:**

```bash
# 1. Check Python version (must be 3.8+)
python --version
# Expected: Python 3.8.x or higher

# 2. Check if in project root
pwd
ls -la | grep -E "fedspeak|config|requirements.txt"
# Expected: See fedspeak/, config/, requirements.txt

# 3. Check if dependencies installed
python -c "import pandas, beautifulsoup4, matplotlib, tqdm" 2>/dev/null && echo "DEPENDENCIES OK" || echo "NEED INSTALL"
# Expected: "DEPENDENCIES OK"

# 4. Check directory structure
ls -d data/raw data/processed data/metadata results/alerts results/visualizations 2>/dev/null && echo "DIRS OK" || echo "NEED CREATE"
# Expected: "DIRS OK" or directories listed

# 5. Check configuration
test -f config/config.yaml && echo "CONFIG OK" || echo "CONFIG MISSING"
# Expected: "CONFIG OK"
```

**If checks fail, run setup first (see Setup Protocol below).**

---

## Setup Protocol

**Execute this protocol if environment checks fail:**

```bash
# Step 1: Verify in project root
test -f requirements.txt || { echo "ERROR: Not in FedSpeak root"; exit 1; }

# Step 2: Install dependencies
pip install -r requirements.txt
# Validation: python -c "import tqdm" should succeed

# Step 3: Create directory structure
mkdir -p data/raw data/processed data/metadata results/alerts results/visualizations
# Validation: ls -d data/raw should succeed

# Step 4: Verify module imports
python -c "from fedspeak import cli, fetcher, extractor, analyzer, detector, alerter"
# Expected: No output (success)

# Step 5: Check configuration
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
# Expected: No output (success)

echo "SETUP COMPLETE"
```

---

## State Detection Protocol

**Before executing any command, determine current state:**

```bash
# Check what data already exists
echo "=== CURRENT STATE ==="

# Downloaded documents
RAW_COUNT=$(find data/raw -name "*.html" 2>/dev/null | wc -l)
echo "Downloaded documents: $RAW_COUNT"

# Extracted text files
PROCESSED_COUNT=$(find data/processed -name "*.txt" 2>/dev/null | wc -l)
echo "Extracted texts: $PROCESSED_COUNT"

# Metrics file
if [ -f data/metadata/keyword_metrics.csv ]; then
    METRICS_ROWS=$(wc -l < data/metadata/keyword_metrics.csv)
    echo "Metrics rows: $METRICS_ROWS"
else
    echo "Metrics: NOT CREATED"
fi

# Alert files
ALERT_COUNT=$(find results/alerts -name "*.txt" 2>/dev/null | wc -l)
echo "Alerts: $ALERT_COUNT"

echo "===================="
```

**Decision logic based on state:**

| State | Next Action |
|-------|-------------|
| No documents (RAW_COUNT=0) | Execute Download Protocol |
| Documents but no text (PROCESSED_COUNT=0) | Execute Extract Protocol |
| Text but no metrics | Execute Analyze Protocol |
| Metrics but no alerts | Execute Detect Protocol |
| All exist | Execute Update Protocol (download recent) |

---

## Protocol 1: Download Documents

**Purpose:** Fetch FOMC documents from federalreserve.gov

**Prerequisites:**
- Internet connection
- `data/raw/` directory exists

**Decision: Date Range Selection**

| Goal | Start Date | End Date | Flag |
|------|-----------|----------|------|
| Test with known shift | 2021-01-01 | 2021-12-31 | --statements-only |
| Recent monitoring | (90 days ago) | (today) | --statements-only |
| Full historical | 2008-01-01 | (today) | --statements-only |
| Complete corpus | 2008-01-01 | (today) | (none - include minutes) |

**Execution:**

```bash
# Example: Test case (2021)
START_DATE="2021-01-01"
END_DATE="2021-12-31"

python -m fedspeak.cli download \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --statements-only

# Capture exit code
DOWNLOAD_EXIT=$?
```

**Success Criteria:**

```bash
# Exit code should be 0
test $DOWNLOAD_EXIT -eq 0 || { echo "DOWNLOAD FAILED"; exit 1; }

# At least 1 file should be downloaded
NEW_COUNT=$(find data/raw -name "*.html" -newer /tmp/download_marker 2>/dev/null | wc -l)
test $NEW_COUNT -gt 0 || echo "WARNING: No new files downloaded"

# Check for expected file pattern
ls data/raw/policy_statement_*.html 2>/dev/null | head -1 || echo "ERROR: No policy statements found"
```

**Expected Output Patterns:**
```
Downloading policy_statement: 100%|████████| 8/8 [00:15<00:00]
  success: 8, failed: 0
[SUCCESS] Download complete!
```

**Resume capability:** Automatically skips existing files. Safe to re-run.

**Common issues:**
- `404 Not Found` for dates <2008 → Use 2008-01-01 as minimum
- `0/X successful` → Check internet connection
- No progress bar → tqdm not installed (still works)

---

## Protocol 2: Extract Text

**Purpose:** Extract clean text from HTML documents

**Prerequisites:**
- Documents exist in `data/raw/`
- `data/processed/` directory exists

**Pre-flight check:**

```bash
# Verify documents exist
RAW_COUNT=$(find data/raw -name "*.html" | wc -l)
test $RAW_COUNT -gt 0 || { echo "ERROR: No documents to extract"; exit 1; }

# Check if extraction already done
PROCESSED_COUNT=$(find data/processed -name "*.txt" | wc -l)
if [ $PROCESSED_COUNT -eq $RAW_COUNT ]; then
    echo "INFO: Extraction already complete ($PROCESSED_COUNT files)"
    read -p "Re-extract? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "SKIPPING EXTRACTION"
        exit 0
    fi
fi
```

**Execution:**

```bash
python -m fedspeak.cli extract

# Capture exit code
EXTRACT_EXIT=$?
```

**Success Criteria:**

```bash
# Exit code should be 0
test $EXTRACT_EXIT -eq 0 || { echo "EXTRACTION FAILED"; exit 1; }

# Output files should exist
PROCESSED_COUNT=$(find data/processed -name "*.txt" | wc -l)
test $PROCESSED_COUNT -gt 0 || { echo "ERROR: No text files created"; exit 1; }

# Verify non-empty files
EMPTY_COUNT=$(find data/processed -name "*.txt" -empty | wc -l)
test $EMPTY_COUNT -eq 0 || echo "WARNING: $EMPTY_COUNT empty text files"

# Check sample file has reasonable word count
SAMPLE_FILE=$(find data/processed -name "*.txt" | head -1)
WORD_COUNT=$(wc -w < "$SAMPLE_FILE")
test $WORD_COUNT -gt 50 || echo "WARNING: Sample file has only $WORD_COUNT words"
```

**Expected Output Patterns:**
```
[EXTRACT] Processing 8 documents...
✓ Extracted 320 words from policy_statement_20210127a.html
...
[SUCCESS] Extraction complete!
  Processed: 8/8 documents
  Success rate: 100%
```

**Common issues:**
- `Insufficient text (X < 100 words)` → Document is very short or extraction failed
- `Could not find main content` → HTML structure not recognized (rare, should auto-fallback)

---

## Protocol 3: Analyze Keywords

**Purpose:** Count keyword frequencies and calculate baselines

**Prerequisites:**
- Extracted texts exist in `data/processed/`
- `data/metadata/` directory exists

**Pre-flight check:**

```bash
# Verify texts exist
PROCESSED_COUNT=$(find data/processed -name "*.txt" | wc -l)
test $PROCESSED_COUNT -gt 0 || { echo "ERROR: No texts to analyze"; exit 1; }

# Check if analysis already done
if [ -f data/metadata/keyword_metrics.csv ]; then
    METRICS_ROWS=$(wc -l < data/metadata/keyword_metrics.csv)
    echo "INFO: Metrics already exist ($METRICS_ROWS rows)"
    read -p "Re-analyze? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "SKIPPING ANALYSIS"
        exit 0
    fi
fi
```

**Execution:**

```bash
python -m fedspeak.cli analyze

# Capture exit code
ANALYZE_EXIT=$?
```

**Success Criteria:**

```bash
# Exit code should be 0
test $ANALYZE_EXIT -eq 0 || { echo "ANALYSIS FAILED"; exit 1; }

# Metrics file should exist
test -f data/metadata/keyword_metrics.csv || { echo "ERROR: Metrics file not created"; exit 1; }

# Metrics should have header + data rows
METRICS_ROWS=$(wc -l < data/metadata/keyword_metrics.csv)
test $METRICS_ROWS -gt 1 || { echo "ERROR: Metrics file is empty"; exit 1; }

# Verify expected columns
head -1 data/metadata/keyword_metrics.csv | grep -q "date,doc_id,doc_type,word,count,is_group,primary_word,baseline" || echo "WARNING: Unexpected columns"

# Check for keyword diversity (should have multiple unique words)
UNIQUE_WORDS=$(cut -d, -f4 data/metadata/keyword_metrics.csv | sort -u | wc -l)
test $UNIQUE_WORDS -gt 5 || echo "WARNING: Only $UNIQUE_WORDS unique words tracked"
```

**Expected Output Patterns:**
```
[ANALYZE] Analyzing 8 documents for 5 keywords...
✓ Analyzed policy_statement_20210127a.txt: {...}
...
[SUCCESS] Analysis complete!
  Documents: 8
  Observations: 120 (8 docs × 15 tracked words)
  Time-series saved: data/metadata/keyword_metrics.csv
```

**Observation count calculation:**
- 5 primary keywords
- Each has ~2-3 synonyms
- Plus 5 GROUP totals
- Total: ~15-20 rows per document

**Common issues:**
- Low observation count → Check if synonyms are configured in config.yaml
- All counts are 0 → Keywords may not appear in this corpus period

---

## Protocol 4: Detect Shifts

**Purpose:** Identify language shift events (emergence/removal)

**Prerequisites:**
- Metrics file exists at `data/metadata/keyword_metrics.csv`
- `results/alerts/` and `results/visualizations/` directories exist

**Pre-flight check:**

```bash
# Verify metrics exist
test -f data/metadata/keyword_metrics.csv || { echo "ERROR: Metrics file missing"; exit 1; }

# Check metrics have sufficient data
METRICS_ROWS=$(wc -l < data/metadata/keyword_metrics.csv)
test $METRICS_ROWS -gt 10 || echo "WARNING: Only $METRICS_ROWS rows (need more for baselines)"

# Check if detection already done
EXISTING_ALERTS=$(find results/alerts -name "*.txt" 2>/dev/null | wc -l)
if [ $EXISTING_ALERTS -gt 0 ]; then
    echo "INFO: $EXISTING_ALERTS alerts already exist"
    echo "Re-running will regenerate alerts"
fi
```

**Execution:**

```bash
python -m fedspeak.cli detect

# Capture exit code
DETECT_EXIT=$?
```

**Success Criteria:**

```bash
# Exit code should be 0
test $DETECT_EXIT -eq 0 || { echo "DETECTION FAILED"; exit 1; }

# Check for alerts (may be 0 if no shifts in period)
ALERT_COUNT=$(find results/alerts -name "*.txt" 2>/dev/null | wc -l)
echo "INFO: Generated $ALERT_COUNT alerts"

# If known test case (2021), verify transitory removal detected
if ls results/alerts/*20211215*transitory* 2>/dev/null; then
    echo "SUCCESS: Transitory removal detected (expected for 2021 corpus)"
fi

# Verify alert file structure
if [ $ALERT_COUNT -gt 0 ]; then
    SAMPLE_ALERT=$(find results/alerts -name "*.txt" | head -1)
    grep -q "FEDSPEAK LANGUAGE SHIFT DETECTED" "$SAMPLE_ALERT" || echo "WARNING: Alert format unexpected"

    # Check JSON counterpart exists
    JSON_FILE="${SAMPLE_ALERT%.txt}.json"
    test -f "$JSON_FILE" || echo "WARNING: JSON alert missing"
fi

# Check for visualizations
VIZ_COUNT=$(find results/visualizations -name "*.png" 2>/dev/null | wc -l)
echo "INFO: Generated $VIZ_COUNT visualizations"
```

**Expected Output Patterns:**
```
[DETECT] Loading metrics from data/metadata/keyword_metrics.csv...
✓ REMOVAL: 'transitory' on 2021-12-15
  Baseline: 2.3 → Current: 0
  Confidence: HIGH
[SUCCESS] Detection complete!
  Shifts detected: 1
  Alerts generated: 2 files (JSON + text)
  Visualizations: 1 chart
```

**Zero shifts is valid:** If no shifts occurred in the date range, 0 alerts is correct behavior.

**Common issues:**
- `Insufficient baseline data` warnings → Need more historical documents (3+ docs before detection)
- No shifts detected → May be correct if no shifts in period

---

## Protocol 5: Validate Results

**Purpose:** Verify pipeline produced expected outputs

**Execution:**

```bash
echo "=== VALIDATION REPORT ==="

# 1. Check all stages completed
RAW_COUNT=$(find data/raw -name "*.html" 2>/dev/null | wc -l)
PROCESSED_COUNT=$(find data/processed -name "*.txt" 2>/dev/null | wc -l)
METRICS_EXISTS=$(test -f data/metadata/keyword_metrics.csv && echo "YES" || echo "NO")
ALERT_COUNT=$(find results/alerts -name "*.txt" 2>/dev/null | wc -l)
VIZ_COUNT=$(find results/visualizations -name "*.png" 2>/dev/null | wc -l)

echo "Pipeline Stage Status:"
echo "  Downloaded: $RAW_COUNT documents"
echo "  Extracted: $PROCESSED_COUNT texts"
echo "  Metrics: $METRICS_EXISTS"
echo "  Alerts: $ALERT_COUNT"
echo "  Visualizations: $VIZ_COUNT"

# 2. Verify extraction success rate
if [ $RAW_COUNT -gt 0 ]; then
    EXTRACT_RATE=$(awk "BEGIN {printf \"%.0f\", ($PROCESSED_COUNT/$RAW_COUNT)*100}")
    echo "  Extraction rate: $EXTRACT_RATE%"
    test $EXTRACT_RATE -ge 90 || echo "  WARNING: Low extraction rate"
fi

# 3. Check metrics data quality
if [ "$METRICS_EXISTS" = "YES" ]; then
    METRICS_ROWS=$(wc -l < data/metadata/keyword_metrics.csv)
    echo "  Metrics rows: $METRICS_ROWS"

    # Check for actual keyword usage
    NONZERO_COUNTS=$(awk -F, '$5 > 0 {count++} END {print count}' data/metadata/keyword_metrics.csv)
    echo "  Non-zero counts: $NONZERO_COUNTS"
    test $NONZERO_COUNTS -gt 0 || echo "  WARNING: No keywords found in corpus"
fi

# 4. List detected shifts
if [ $ALERT_COUNT -gt 0 ]; then
    echo ""
    echo "Detected Shifts:"
    for alert in results/alerts/*.txt; do
        # Extract key info from alert
        SHIFT_TYPE=$(grep "Shift Type:" "$alert" | awk '{print $3}')
        WORD=$(grep "Word:" "$alert" | cut -d'"' -f2)
        DATE=$(grep "Document:" "$alert" | awk -F' - ' '{print $2}')
        echo "  - $SHIFT_TYPE of '$WORD' on $DATE"
    done
fi

echo "======================="
```

**Success criteria:**
- ✅ Extraction rate ≥ 90%
- ✅ Metrics file exists with >10 rows
- ✅ Non-zero keyword counts present
- ✅ At least 1 alert if testing known shift period (2021)

---

## Protocol 6: View Specific Results

**Purpose:** Extract and display specific alert details

**View alert by date:**

```bash
# Find alerts by date
SEARCH_DATE="20211215"
find results/alerts -name "*${SEARCH_DATE}*" -type f

# Display text alert
cat results/alerts/ALERT-${SEARCH_DATE}-*.txt 2>/dev/null || echo "No alert found for date $SEARCH_DATE"
```

**View alert by keyword:**

```bash
# Find alerts for specific keyword
KEYWORD="transitory"
find results/alerts -name "*${KEYWORD}*" -type f | while read file; do
    echo "=== $file ==="
    cat "$file"
    echo ""
done
```

**Extract JSON alert data:**

```bash
# Parse JSON alert programmatically
ALERT_FILE="results/alerts/ALERT-20211215-removal-transitory.json"

if [ -f "$ALERT_FILE" ]; then
    python -c "
import json
with open('$ALERT_FILE') as f:
    alert = json.load(f)

print('Alert ID:', alert['alert_id'])
print('Shift Type:', alert['shift_type'])
print('Word:', alert['word'])
print('Date:', alert['document']['date'])
print('Change:', alert['change']['change_description'])
print('Confidence:', alert['confidence'])

if 'synonym_details' in alert:
    print('Synonyms tracked:', len(alert['synonym_details']['synonym_counts']))
    print('Synonym usage:', alert['synonym_details']['synonym_counts'])
"
else
    echo "Alert file not found: $ALERT_FILE"
fi
```

**View timeline visualization:**

```bash
# List all visualizations
ls -lh results/visualizations/

# Open visualization (platform-specific)
# Linux: xdg-open results/visualizations/transitory_timeline.png
# Mac: open results/visualizations/transitory_timeline.png
# Windows: start results/visualizations/transitory_timeline.png
```

---

## Protocol 7: Update Detection (Incremental)

**Purpose:** Check for new Fed communications and detect shifts

**Use case:** Run periodically to monitor ongoing Fed communications

**Execution:**

```bash
# Calculate date range (last 90 days)
START_DATE=$(date -d '90 days ago' +%Y-%m-%d 2>/dev/null || date -v-90d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

echo "Updating corpus: $START_DATE to $END_DATE"

# Download (auto-skips existing)
python -m fedspeak.cli download --start-date "$START_DATE" --end-date "$END_DATE" --statements-only

# Check if new files were downloaded
NEW_FILES=$(find data/raw -name "*.html" -mtime -1 | wc -l)

if [ $NEW_FILES -gt 0 ]; then
    echo "Found $NEW_FILES new documents, processing..."

    # Extract new files
    python -m fedspeak.cli extract

    # Re-analyze (updates metrics)
    python -m fedspeak.cli analyze --force

    # Re-detect (regenerates alerts)
    python -m fedspeak.cli detect

    # Check for new alerts
    NEW_ALERTS=$(find results/alerts -mtime -1 -name "*.txt" | wc -l)

    if [ $NEW_ALERTS -gt 0 ]; then
        echo "🚨 NEW LANGUAGE SHIFT DETECTED!"
        echo "Found $NEW_ALERTS new alerts:"
        find results/alerts -mtime -1 -name "*.txt" -exec echo "  - {}" \;
    else
        echo "✓ No new shifts detected"
    fi
else
    echo "No new documents available"
fi
```

---

## Decision Trees

### Decision Tree 1: What to Download?

```
User goal?
├─ Test system
│  └─ Download 2021 (known shifts)
│     Command: download --start-date 2021-01-01 --end-date 2021-12-31 --statements-only
│
├─ Monitor recent Fed communications
│  └─ Download last 90 days
│     Command: download --start-date $(date -d '90 days ago' +%Y-%m-%d) --statements-only
│
├─ Historical analysis (specific era)
│  ├─ COVID era → 2020-01-01 to 2023-12-31
│  ├─ Post-crisis → 2009-01-01 to 2015-12-31
│  └─ Custom range → Use specific dates
│
└─ Complete corpus
   └─ Download 2008 to present
      Command: download --start-date 2008-01-01 --statements-only
      Note: Takes ~60 min, ~500MB
```

### Decision Tree 2: Troubleshooting No Shifts Detected

```
No shifts detected
├─ Check 1: Are there enough documents?
│  Command: find data/raw -name "*.html" | wc -l
│  ├─ <3 documents → Need more for baseline calculation
│  └─ ≥3 documents → Continue
│
├─ Check 2: Do keywords appear in corpus?
│  Command: grep -h "transitory\|patient\|accommodative" data/processed/*.txt | wc -l
│  ├─ 0 matches → Keywords not in this period (valid result)
│  └─ >0 matches → Continue
│
├─ Check 3: Is date range covering known shifts?
│  Known shifts: Dec 2021 (transitory), Sep 2018 (accommodative), Mar 2015 (patient)
│  └─ If date range doesn't include these → No shifts expected (valid result)
│
└─ Check 4: Are baselines calculated?
   Command: grep -v "^baseline$" data/metadata/keyword_metrics.csv | grep -v ",0.0$" | wc -l
   ├─ All baselines 0.0 → Need more historical data
   └─ Some non-zero → Check detection parameters in config
```

---

## Configuration Adjustments

**Common configuration changes:**

**Add new keyword:**

```bash
# Edit config
cat >> config/config.yaml << 'EOF'

  - word: "soft landing"
    type: "addition"
    context: "economic outlook"
    shift_id: "SHIFT-2024-01"
    significance: "Describes Fed goal to reduce inflation without recession"
    enabled: true
    priority: "medium"
    synonyms:
      - "smooth transition"
      - "gradual adjustment"
EOF

# Re-analyze to pick up new keyword
python -m fedspeak.cli analyze --force
python -m fedspeak.cli detect
```

**Adjust detection sensitivity:**

```bash
# Make detection more sensitive (lower thresholds)
# Edit detection section in config/config.yaml:
#   sustained_removal_threshold: 2  (was 3)
#   min_baseline_samples: 2         (was 3)

# Re-run detection
python -m fedspeak.cli detect
```

---

## Testing Protocol

**Run unit tests:**

```bash
# All tests
pytest tests/ -v

# Expected: 68 passed

# With coverage
pytest tests/ --cov=fedspeak --cov-report=term

# Expected: ~67% coverage
```

**Validate with known test case:**

```bash
# Download 2021, should detect transitory removal on Dec 15
python -m fedspeak.cli download --start-date 2021-01-01 --end-date 2021-12-31 --statements-only
python -m fedspeak.cli extract
python -m fedspeak.cli analyze
python -m fedspeak.cli detect

# Verify expected alert exists
test -f results/alerts/ALERT-20211215-removal-transitory.txt && echo "✓ TEST PASSED" || echo "✗ TEST FAILED"
```

---

## Error Handling

**Capture and handle errors:**

```bash
# Run with error handling
if python -m fedspeak.cli download --start-date 2021-01-01 --end-date 2021-12-31 --statements-only; then
    echo "Download succeeded"
else
    EXIT_CODE=$?
    echo "Download failed with code $EXIT_CODE"

    # Check common issues
    if ! ping -c 1 www.federalreserve.gov &>/dev/null; then
        echo "Network issue: Cannot reach Federal Reserve website"
    fi

    # Check disk space
    DISK_FREE=$(df . | tail -1 | awk '{print $4}')
    if [ $DISK_FREE -lt 100000 ]; then
        echo "Disk space low: Only ${DISK_FREE}KB available"
    fi

    exit $EXIT_CODE
fi
```

---

## Performance Expectations

| Operation | Documents | Expected Time | Disk Usage |
|-----------|-----------|---------------|------------|
| Download | 8 (1 year) | ~15-30 sec | ~2MB |
| Download | 150 (full corpus) | ~60 min | ~500MB |
| Extract | 8 | <1 sec | ~200KB |
| Extract | 150 | <10 sec | ~5MB |
| Analyze | 8 | <1 sec | ~50KB |
| Analyze | 150 | <1 sec | ~1MB |
| Detect | 8 | <1 sec | ~100KB |
| Detect | 150 | <2 sec | ~5MB |

**Bottleneck:** Download is rate-limited to 1 second per document (respect Fed servers)

---

## Agent Workflow Template

**Complete autonomous execution:**

```bash
#!/bin/bash
set -e  # Exit on error

echo "=== FedSpeak Autonomous Execution ==="

# 1. Environment check
echo "[1/6] Checking environment..."
python -c "from fedspeak import cli" || { echo "ERROR: Module import failed"; exit 1; }

# 2. Download
echo "[2/6] Downloading documents..."
python -m fedspeak.cli download --start-date 2021-01-01 --end-date 2021-12-31 --statements-only

# 3. Extract
echo "[3/6] Extracting text..."
python -m fedspeak.cli extract

# 4. Analyze
echo "[4/6] Analyzing keywords..."
python -m fedspeak.cli analyze

# 5. Detect
echo "[5/6] Detecting shifts..."
python -m fedspeak.cli detect

# 6. Report
echo "[6/6] Generating report..."
ALERT_COUNT=$(find results/alerts -name "*.txt" 2>/dev/null | wc -l)

echo ""
echo "=== EXECUTION COMPLETE ==="
echo "Alerts generated: $ALERT_COUNT"

if [ $ALERT_COUNT -gt 0 ]; then
    echo ""
    echo "Shifts detected:"
    for alert in results/alerts/*.txt; do
        grep "Word:" "$alert" | head -1
        grep "Shift Type:" "$alert" | head -1
        grep "Document:.*-" "$alert" | head -1
        echo "---"
    done
fi

exit 0
```

---

## API Response Formats

**For programmatic parsing:**

**JSON Alert Structure:**
```json
{
  "alert_id": "ALERT-20211215-removal-transitory",
  "timestamp": "2024-01-15T14:30:00",
  "shift_type": "removal",  // "emergence" or "removal"
  "word": "transitory",
  "document": {
    "doc_id": "monetary20211215a",
    "doc_type": "policy_statement",
    "date": "2021-12-15"
  },
  "change": {
    "previous_count": 2.3,
    "current_count": 0,
    "change_description": "2.3 → 0",
    "synonym_breakdown": {
      "transitory": 2,
      "transient": 1,
      "temporary": 0
    }
  },
  "synonym_details": {
    "primary_word": "transitory",
    "synonyms_present": ["transitory", "transient"],
    "synonym_counts": {...},
    "total_synonyms_tracked": 3
  },
  "confidence": "high",
  "visualization": "results/visualizations/transitory_timeline.png"
}
```

**Metrics CSV Structure:**
```csv
date,doc_id,doc_type,word,count,is_group,primary_word,baseline
2021-12-15,monetary20211215a,policy_statement,transitory,0,False,transitory,2.3
2021-12-15,monetary20211215a,policy_statement,transient,0,False,transitory,0.8
2021-12-15,monetary20211215a,policy_statement,transitory_GROUP,0,True,transitory,3.1
```

---

## Summary Checklist

**Before executing pipeline:**
- [ ] Python 3.8+ installed
- [ ] In project root (requirements.txt exists)
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] Directories created (data/, results/)
- [ ] Config exists (config/config.yaml)

**After each stage:**
- [ ] Download: Files in data/raw/, >0 documents
- [ ] Extract: Files in data/processed/, extraction rate >90%
- [ ] Analyze: keyword_metrics.csv exists, >10 rows
- [ ] Detect: Alerts in results/alerts/, visualizations in results/visualizations/

**Validation:**
- [ ] Run pytest tests/ (68 passed expected)
- [ ] Test known case: 2021 corpus detects transitory removal Dec 15

---

**Last Updated:** 2025-01-06
**Optimized for:** Claude Code, autonomous AI agents
**Companion to:** RUNBOOK.md (human-oriented guide)
