# FedSpeak Agent Guide

**Operational guide optimized for AI agents (Claude Code, autonomous systems)**

This guide provides structured protocols for autonomous execution of the FedSpeak system with explicit state checks, success criteria, and decision logic.

---

## Quick Context

**What is FedSpeak:**
- Automated Federal Reserve policy shift detection system
- Uses Word2Vec semantic analysis + multi-signal validation + AI explainability
- Detects when Fed changes messaging about economy (e.g., "transitory" removal Dec 2021)
- Achieves 70-75% precision for Tier 1 (triple-validated) alerts

**System Architecture:**
- **Core Detection**: Word2Vec embeddings (cosine similarity, 1,218 term vocabulary)
- **Market Validation**: FRED API (Treasury yields) + Yahoo Finance (VIX, S&P 500)
- **Media Validation**: GDELT Project (100K+ sources) + FinBERT sentiment
- **AI Explainability**: Claude 3.5 Sonnet (MILA framework, hawkish/dovish classification)
- **Dashboards**: Flask web interface (alerts, Word2Vec explorer, MILA stance viewer)

**Key Capabilities:**
- Real-time monitoring (RSS feed polling every 5 minutes)
- Three-tier alert classification (Gold/Silver/Bronze by signal confidence)
- Interactive semantic similarity search
- Cost-effective AI stance analysis (~$0.003/statement)
- Production-ready (175 tests passing, 83% coverage, Pylint 10.0/10)

---

## Environment Check Protocol

**Before starting, verify environment state:**

```bash
# 1. Check Python version (must be 3.11+)
python --version
# Expected: Python 3.11.x or higher

# 2. Check if in project root
pwd
ls -la | grep -E "src|config|requirements.txt|README.md"
# Expected: See src/, config/, requirements.txt, README.md

# 3. Check virtual environment (recommended)
which python | grep venv_fedspeak_prod && echo "VENV ACTIVE" || echo "VENV NOT ACTIVE"
# Expected: "VENV ACTIVE"

# 4. Check if core dependencies installed
python -c "import pandas, anthropic, gensim, flask, transformers" 2>/dev/null && echo "DEPENDENCIES OK" || echo "NEED INSTALL"
# Expected: "DEPENDENCIES OK"

# 5. Check directory structure
ls -d src/core src/validation src/dashboard data/ logs/ 2>/dev/null && echo "DIRS OK" || echo "NEED CREATE"
# Expected: "DIRS OK"

# 6. Check configuration
test -f config/config.yaml && echo "CONFIG OK" || echo "CONFIG MISSING"
# Expected: "CONFIG OK"

# 7. Check Word2Vec model exists
test -f prototypes/results/fed_word2vec.model && echo "MODEL OK" || echo "MODEL MISSING"
# Expected: "MODEL OK"
```

**If checks fail, run setup first (see Setup Protocol below).**

---

## Setup Protocol

**Execute this protocol if environment checks fail:**

```bash
# Step 1: Verify in project root
test -f requirements.txt || { echo "ERROR: Not in FedSpeak root"; exit 1; }

# Step 2: Create virtual environment (if not exists)
if [ ! -d "venv_fedspeak_prod" ]; then
    python3.11 -m venv venv_fedspeak_prod
    echo "Created virtual environment"
fi

# Step 3: Activate virtual environment
source venv_fedspeak_prod/bin/activate  # Linux/Mac
# Or: venv_fedspeak_prod\Scripts\activate  # Windows

# Step 4: Install dependencies
pip install -r requirements.txt
# Expected: ~3.8GB download (PyTorch, transformers, etc.)
# Duration: 3-5 minutes

# Step 5: Create directory structure (if missing)
mkdir -p data/processed data/alerts data/market_cache data/media_cache data/mila_cache
mkdir -p logs

# Step 6: Verify module imports
python -c "from src.core.shift_detector import ShiftDetector; from src.validation.market_validator import MarketValidator"
# Expected: No output (success)

# Step 7: Check configuration
python -c "import yaml; config = yaml.safe_load(open('config/config.yaml')); print('Config loaded:', len(config), 'sections')"
# Expected: "Config loaded: X sections"

echo "SETUP COMPLETE"
```

---

## API Configuration

**FedSpeak MILA (AI stance analysis) supports two routing modes:**

### Option 1: Anthropic Cloud API (Production)

**When to use:**
- Production deployments
- Want to use Anthropic's cloud infrastructure
- Need guaranteed API availability

**Setup:**
```bash
# Get API key from https://console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_ACTUAL_KEY"

# Or add to config/config.yaml:
# explainability:
#   mila:
#     api_key: "sk-ant-api03-YOUR_ACTUAL_KEY"
```

**Cost:** ~$0.003 per statement (~$0.60 for 200 historical statements, <$5/year ongoing)

**Verification:**
```bash
# Start system and check logs for:
# "MILA initialized with model: claude-3-5-sonnet-20241022 via Anthropic API (cloud)"
```

### Option 2: Claude Code Max Local Routing (Development)

**When to use:**
- Development/testing
- Have Claude Code Max subscription
- Want to avoid API costs
- Working offline or in restricted network

**Setup:**
```bash
# Set placeholder API key (all 9s pattern signals local routing)
export ANTHROPIC_API_KEY="sk-ant-999999999999"

# System automatically detects pattern and routes to Claude Code Max
```

**Cost:** Free (uses your Claude Code Max subscription)

**Verification:**
```bash
# Start system and check logs for:
# "MILA initialized with model: claude-3-5-sonnet-20241022 via Claude Code (local inference)"
# "Local routing active: Using Claude Code Max for inference. API calls will be processed locally (no cloud API costs)."
```

**How it works:**
- API router detects "all 9s" pattern in API key (last segment after final hyphen)
- Routes to local Claude Code Max instead of Anthropic cloud API
- Behavior is identical from user perspective (same inputs/outputs)
- Logged as "Claude Code (local)" vs "Anthropic API (cloud)"

---

## Quick Start

**Get system running in 5 minutes:**

```bash
# Terminal 1: Start dashboard
source venv_fedspeak_prod/bin/activate
python src/dashboard/app.py

# Expected output:
#  * Running on http://127.0.0.1:5000
#  * Restarting with stat
#  * Debugger is active!

# Visit: http://localhost:5000
# Should see: FedSpeak dashboard with navigation (Alerts, Explore, Explainability)


# Terminal 2: Start monitor (in separate terminal)
source venv_fedspeak_prod/bin/activate
python src/monitor.py --continuous --interval 300

# Expected output:
# INFO - Starting FedSpeak monitor in continuous mode (check interval: 300 seconds)
# INFO - Checking for new FOMC statements...
# INFO - No new statements found (last check: ...)
# INFO - Sleeping 300 seconds until next check


# Verify services:
curl http://localhost:5000/api/stats
# Expected: {"total_alerts": X, "tier_1_alerts": Y, ...}
```

**Minimal one-time check (no continuous monitoring):**

```bash
# Run detector once on existing corpus
python src/monitor.py

# Expected: Checks RSS feed once, processes any new statements, exits
```

---

## State Detection Protocol

**Before executing operations, determine current state:**

```bash
echo "=== CURRENT STATE ==="

# Check FOMC statement corpus
PROCESSED_COUNT=$(find data/processed -name "*.txt" 2>/dev/null | wc -l)
echo "FOMC statements processed: $PROCESSED_COUNT"

# Check alerts generated
ALERT_COUNT=$(find data/alerts -name "ALERT-*.json" 2>/dev/null | wc -l)
echo "Alerts generated: $ALERT_COUNT"

# Check tier distribution
if [ -f data/alerts/*.json 2>/dev/null ]; then
    echo "Alert tiers:"
    grep -h '"tier":' data/alerts/*.json 2>/dev/null | sort | uniq -c || echo "  No alerts"
fi

# Check market validation cache
MARKET_CACHE_SIZE=$(du -sh data/market_cache 2>/dev/null | cut -f1)
echo "Market data cache: ${MARKET_CACHE_SIZE:-0}"

# Check media validation cache
MEDIA_CACHE_SIZE=$(du -sh data/media_cache 2>/dev/null | cut -f1)
echo "Media data cache: ${MEDIA_CACHE_SIZE:-0}"

# Check MILA cache
MILA_CACHE_COUNT=$(find data/mila_cache -name "*.json" 2>/dev/null | wc -l)
echo "MILA analyses cached: $MILA_CACHE_COUNT"

# Check if services running
curl -s http://localhost:5000/api/stats >/dev/null && echo "Dashboard: RUNNING" || echo "Dashboard: STOPPED"

echo "===================="
```

**Decision logic based on state:**

| State | Recommended Action |
|-------|-------------------|
| PROCESSED_COUNT = 0 | No corpus data - system will download on first run |
| PROCESSED_COUNT > 0, ALERT_COUNT = 0 | Have corpus, no shifts detected (may be valid) |
| Dashboard: STOPPED | Start dashboard: `python src/dashboard/app.py` |
| MILA_CACHE_COUNT = 0 | MILA not yet used or API key not set |

---

## Protocol 1: Running the Dashboard

**Purpose:** Access web interface for alerts, exploration, and analysis

**Prerequisites:**
- Virtual environment activated
- Port 5000 available

**Execution:**

```bash
# Start Flask dashboard
python src/dashboard/app.py

# Expected output:
#  * Serving Flask app 'app'
#  * Debug mode: off
# WARNING: This is a development server. Do not use it in a production deployment.
#  * Running on http://127.0.0.1:5000
# Press CTRL+C to quit
```

**Success Criteria:**

```bash
# Dashboard should be accessible
curl -s http://localhost:5000/ | grep -q "FedSpeak" && echo "DASHBOARD OK" || echo "DASHBOARD FAILED"

# API endpoints should respond
curl -s http://localhost:5000/api/stats | grep -q "total_alerts" && echo "API OK" || echo "API FAILED"

# Expected: Both checks return "OK"
```

**Available Routes:**

| Route | Purpose |
|-------|---------|
| `/` | Main dashboard (recent alerts, filtering, CSV export) |
| `/explore` | Word2Vec Explorer (semantic similarity, policy proximity) |
| `/explainability` | MILA stance viewer (hawkish/dovish analysis) |
| `/api/alerts` | JSON API for alerts (with filtering) |
| `/api/explore/similar` | Semantic similarity search |
| `/api/explainability/stance/<date>` | Get stance analysis for statement |

**Common Issues:**

- `Address already in use` → Port 5000 busy, kill process: `lsof -ti:5000 | xargs kill`
- `ModuleNotFoundError: No module named 'flask'` → Install dependencies: `pip install -r requirements.txt`
- Dashboard loads but shows "No alerts" → Normal if no shifts detected in corpus period

---

## Protocol 2: Running the Monitor

**Purpose:** Poll Fed RSS feed and detect new policy shifts

**Prerequisites:**
- Virtual environment activated
- Dashboard running (optional, for viewing alerts)

**Execution:**

```bash
# One-time check
python src/monitor.py

# Continuous monitoring (checks every 5 minutes)
python src/monitor.py --continuous --interval 300

# Capture exit code
MONITOR_EXIT=$?
```

**Success Criteria:**

```bash
# Exit code should be 0
test $MONITOR_EXIT -eq 0 || { echo "MONITOR FAILED"; exit 1; }

# Check logs for successful execution
tail -20 logs/fedspeak.log | grep -q "Checking for new FOMC statements" && echo "MONITOR OK" || echo "CHECK LOGS"
```

**Expected Output Patterns:**

```
INFO - Starting FedSpeak monitor
INFO - Checking for new FOMC statements...
INFO - Found 1 new statement: policy_statement_20231213a
INFO - Processing statement from 2023-12-13
INFO - Running Word2Vec detection...
INFO - Checking market validation...
INFO - Checking media validation...
INFO - Shift detected: 'patient' removal (Tier 1 - triple validated)
INFO - Alert generated: ALERT-20231213-removal-patient
INFO - Monitor run complete (0 new shifts)
```

**Continuous Mode Behavior:**

- Polls RSS feed every N seconds (default: 300 = 5 minutes)
- Downloads new statements automatically
- Runs full detection pipeline (Word2Vec + market + media + MILA)
- Generates alerts for detected shifts
- Logs all activity to `logs/fedspeak.log`
- Runs indefinitely until stopped (Ctrl+C)

**Common Issues:**

- `404 Not Found` from RSS feed → Fed website issue, retry later
- `FRED API rate limit exceeded` → Market validation skipped, alert may be Tier 2/3 instead of Tier 1
- `ANTHROPIC_API_KEY not found` → MILA disabled, system continues working (just no stance analysis)

---

## Protocol 3: Testing & Validation

**Purpose:** Verify system is working correctly

**Run Full Test Suite:**

```bash
# Activate venv
source venv_fedspeak_prod/bin/activate

# Run all tests
pytest tests/ -v

# Expected: 175 tests passed (100%)
# Duration: ~75 seconds
```

**Success Criteria:**

```bash
# All tests should pass
pytest tests/ -q 2>&1 | tail -1 | grep -q "175 passed" && echo "TESTS OK" || echo "TESTS FAILED"

# Coverage should be >80%
pytest tests/ --cov=src --cov-report=term | grep "TOTAL" | awk '{print $NF}' | sed 's/%//' > /tmp/cov
COV=$(cat /tmp/cov)
test $COV -gt 80 && echo "COVERAGE OK ($COV%)" || echo "COVERAGE LOW ($COV%)"
```

**Test Categories:**

- Core Detector (17 tests): Word2Vec shift detection logic
- Integration (8 tests): Full detection workflows
- Regression (3 tests): Ground truth validation (130 historical shifts)
- Market Validation (10 tests): FRED/Yahoo integration
- Media Validation (13 tests): GDELT/FinBERT integration
- Word2Vec Explorer (28 tests): Semantic similarity
- MILA Framework (15 tests): Claude API integration
- Config/Logging (15 tests): Configuration management
- **NEW: API Router (20+ tests): Routing logic for cloud/local**

**Validate with Known Test Case (December 2021):**

```bash
# The December 2021 "transitory" removal is a known ground truth shift
# Verify it's detected correctly

# Check if alert exists
ALERT_FILE="data/alerts/ALERT-20211215-removal-transitory.json"

if [ -f "$ALERT_FILE" ]; then
    echo "Known shift detected: December 2021 transitory removal"

    # Extract tier
    TIER=$(grep '"tier":' "$ALERT_FILE" | awk '{print $2}' | tr -d ',')
    echo "  Tier: $TIER"

    # Extract confidence
    CONF=$(grep '"confidence":' "$ALERT_FILE" | awk '{print $2}' | tr -d '",')
    echo "  Confidence: $CONF"

    # Verify expected values
    test $TIER -eq 1 && echo "  Tier 1 VERIFIED" || echo "  WARNING: Expected Tier 1, got $TIER"
    test "$CONF" = "high" && echo "  High confidence VERIFIED" || echo "  WARNING: Expected high, got $CONF"
else
    echo "WARNING: December 2021 shift not detected"
    echo "This is expected if you haven't processed 2021 statements yet"
fi
```

---

## Protocol 4: Viewing Results

**Purpose:** Extract and analyze detection results

**View All Alerts:**

```bash
# List all alerts
find data/alerts -name "ALERT-*.json" | sort

# Count by tier
echo "Tier distribution:"
grep -h '"tier":' data/alerts/*.json 2>/dev/null | awk '{print $2}' | tr -d ',' | sort | uniq -c

# Expected output:
#   15 1
#   23 2
#   42 3
# (15 Tier 1 alerts, 23 Tier 2, 42 Tier 3)
```

**View Specific Alert:**

```bash
# Find alerts by date
SEARCH_DATE="20211215"
ALERT_FILE=$(find data/alerts -name "*${SEARCH_DATE}*" -type f | head -1)

if [ -n "$ALERT_FILE" ]; then
    echo "=== Alert for $SEARCH_DATE ==="
    python -c "
import json
with open('$ALERT_FILE') as f:
    alert = json.load(f)

print('Alert ID:', alert['alert_id'])
print('Term:', alert['term'])
print('Tier:', alert['tier'])
print('Confidence:', alert['confidence'])
print('Market Validated:', alert.get('market_validation', {}).get('validated', False))
print('Media Validated:', alert.get('media_validation', {}).get('validated', False))

if 'mila_analysis' in alert:
    print('\\nMILA Stance:', alert['mila_analysis'].get('stance', 'N/A'))
    print('MILA Confidence:', alert['mila_analysis'].get('confidence', 'N/A'))
"
else
    echo "No alert found for date $SEARCH_DATE"
fi
```

**View Alert via Dashboard API:**

```bash
# Get alert by ID via API
ALERT_ID="ALERT-20211215-removal-transitory"
curl -s "http://localhost:5000/api/alerts/${ALERT_ID}" | python -m json.tool

# Get all Tier 1 alerts
curl -s "http://localhost:5000/api/alerts?tier=1" | python -m json.tool

# Get alerts for specific term
curl -s "http://localhost:5000/api/alerts?term=transitory" | python -m json.tool
```

**Export Alerts to CSV:**

```bash
# Download CSV export
curl -s "http://localhost:5000/api/alerts.csv" > alerts_export.csv

# Verify export
wc -l alerts_export.csv
head -5 alerts_export.csv

# Expected: Header + alert rows
```

---

## Protocol 5: Using Word2Vec Explorer

**Purpose:** Explore semantic relationships in Fed language

**Via Web Interface:**

1. Visit: http://localhost:5000/explore
2. Enter term (e.g., "inflation")
3. View similar terms and policy proximity score

**Via API:**

```bash
# Find similar terms
curl -s "http://localhost:5000/api/explore/similar?word=inflation&topn=10" | python -m json.tool

# Expected output:
# [
#   {"term": "prices", "similarity": 0.87},
#   {"term": "wage", "similarity": 0.82},
#   ...
# ]

# Calculate policy proximity
curl -s "http://localhost:5000/api/explore/proximity?word=transitory" | python -m json.tool

# Expected: {"word": "transitory", "proximity_score": 0.65, ...}

# Word-to-word similarity
curl -s "http://localhost:5000/api/explore/similarity?word1=inflation&word2=employment" | python -m json.tool

# Expected: {"word1": "inflation", "word2": "employment", "similarity": 0.48}
```

**Vocabulary Search (Autocomplete):**

```bash
# Search for terms starting with prefix
curl -s "http://localhost:5000/api/explore/search?q=infla&limit=20" | python -m json.tool

# Expected: ["inflation", "inflationary", "inflated"]
```

---

## Protocol 6: Using MILA Stance Analysis

**Purpose:** Get AI-powered hawkish/dovish classification

**Prerequisites:**
- ANTHROPIC_API_KEY set (cloud or local routing)

**Via Web Interface:**

1. Visit: http://localhost:5000/explainability
2. Select statement date
3. View stance classification, confidence, evidence

**Via API:**

```bash
# Get stance for specific date
curl -s "http://localhost:5000/api/explainability/stance/2021-12-15" | python -m json.tool

# Expected output:
# {
#   "date": "2021-12-15",
#   "stance": "hawkish",
#   "confidence": 88,
#   "score": 0.78,
#   "evidence": ["remove transitory language", "signal faster tapering", ...],
#   "explanation": "The December 2021 statement marks a clear hawkish shift...",
#   "cached": true
# }

# Check API cost
curl -s "http://localhost:5000/api/explainability/cost" | python -m json.tool

# Expected: {"total_cost": 0.47, "calls_made": 156, "calls_cached": 144}
```

**Stance Timeline:**

```bash
# Get stance evolution over time
curl -s "http://localhost:5000/api/visualizations/stance-trend?start_date=2020-01-01&end_date=2024-01-01" | python -m json.tool

# Expected: Array of {"date": "...", "stance": "...", "score": ...}
```

---

## Decision Trees

### Decision Tree 1: System Won't Start

```
System won't start
├─ Check 1: Virtual environment activated?
│  Command: which python | grep venv
│  ├─ Not activated → source venv_fedspeak_prod/bin/activate
│  └─ Activated → Continue
│
├─ Check 2: Dependencies installed?
│  Command: pip list | grep -E "flask|anthropic|gensim"
│  ├─ Missing → pip install -r requirements.txt
│  └─ Installed → Continue
│
├─ Check 3: Port 5000 available?
│  Command: lsof -i:5000
│  ├─ In use → kill process: lsof -ti:5000 | xargs kill
│  └─ Available → Continue
│
└─ Check 4: Check logs
   Command: tail -50 logs/fedspeak.log
   └─ Look for Python exceptions, import errors
```

### Decision Tree 2: MILA Not Working

```
MILA not working
├─ Check 1: API key set?
│  Command: echo $ANTHROPIC_API_KEY
│  ├─ Empty → Set key (cloud: sk-ant-api03-..., local: sk-ant-999999999999)
│  └─ Set → Continue
│
├─ Check 2: Key format valid?
│  Command: python -c "from src.explainability.api_router import APIRouter; print(APIRouter.validate_api_key_format('$ANTHROPIC_API_KEY'))"
│  ├─ Invalid → Fix key format
│  └─ Valid → Continue
│
├─ Check 3: Check routing mode
│  Command: grep "MILA initialized" logs/fedspeak.log | tail -1
│  ├─ "Anthropic API (cloud)" → Verify real API key, check Anthropic status
│  ├─ "Claude Code (local)" → Verify Claude Code CLI authenticated
│  └─ Not found → MILA never initialized, check earlier logs
│
└─ Check 4: Test direct API call
   Command: python -c "from src.explainability.api_router import APIRouter; client = APIRouter.create_client(); print('Client created:', client)"
   └─ If fails → Check detailed error message
```

### Decision Tree 3: No Shifts Detected

```
No shifts detected (expected vs unexpected)
├─ Check 1: Is this expected?
│  ├─ Monitoring last 90 days → Shifts are rare, 0 detections is common
│  ├─ Testing on 2021 corpus → Should detect "transitory" removal Dec 15
│  └─ Full historical corpus → Should detect multiple shifts (2015, 2018, 2021, ...)
│
├─ Check 2: Are statements being processed?
│  Command: find data/processed -name "*.txt" | wc -l
│  ├─ 0 files → No statements downloaded yet, monitor will download on first run
│  └─ >0 files → Statements exist, continue
│
├─ Check 3: Is detector running?
│  Command: grep "Running Word2Vec detection" logs/fedspeak.log
│  ├─ Not found → Detector not running, check monitor logs
│  └─ Found → Detector ran, continue
│
└─ Check 4: Are thresholds too strict?
   Command: grep "similarity.*detected" logs/fedspeak.log
   ├─ Many "below threshold but not significant" → Lower similarity threshold in config
   └─ No candidates → Genuinely no shifts in period (valid)
```

---

## Error Handling

**Common Errors and Solutions:**

**Error: `ModuleNotFoundError: No module named 'anthropic'`**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error: `ValueError: No API key provided`**
```bash
# Solution: Set API key
export ANTHROPIC_API_KEY="sk-ant-999999999999"  # Local routing
# Or:
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY"  # Cloud API
```

**Error: `FileNotFoundError: [Errno 2] No such file or directory: 'prototypes/results/fed_word2vec.model'`**
```bash
# Solution: Word2Vec model missing (shouldn't happen in production)
# If model is truly missing, system will fail. Check if file exists:
ls -lh prototypes/results/fed_word2vec.model
# Model should be ~1MB. If missing, contact maintainer.
```

**Error: `Address already in use` (port 5000)**
```bash
# Solution: Kill process using port 5000
lsof -ti:5000 | xargs kill

# Then restart dashboard
python src/dashboard/app.py
```

**Error: `FRED API rate limit exceeded`**
```bash
# Solution: Market validation will be skipped temporarily
# System continues working, alerts may be Tier 2/3 instead of Tier 1
# Wait 1 hour for rate limit to reset, or use FRED API key (optional)
```

---

## Monitoring Operations

**Check System Health:**

```bash
# Are services running?
curl -s http://localhost:5000/api/stats >/dev/null && echo "Dashboard: UP" || echo "Dashboard: DOWN"

# Check logs for errors
tail -100 logs/fedspeak.log | grep ERROR
# Expected: No output (or only warnings, not errors)

# Check disk space (cache can grow large)
du -sh data/*
# Expected:
#   50M   data/alerts
#   500M  data/market_cache
#   200M  data/media_cache
#   1M    data/mila_cache
#   10M   data/processed
```

**Log Analysis:**

```bash
# Recent activity
tail -50 logs/fedspeak.log

# Search for specific events
grep "Shift detected" logs/fedspeak.log

# Count detection runs today
TODAY=$(date +%Y-%m-%d)
grep "$TODAY.*Running Word2Vec detection" logs/fedspeak.log | wc -l

# Check MILA usage
grep "MILA analysis" logs/fedspeak.log | tail -20
```

**Performance Metrics:**

```bash
# Average detection time
grep "Detection completed in" logs/fedspeak.log | awk '{print $NF}' | sed 's/s//' | \
awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# Cache hit rates
grep "cache hit" logs/fedspeak.log | wc -l
grep "cache miss" logs/fedspeak.log | wc -l
# Higher hit rate = lower costs
```

---

## Autonomous Execution Template

**Complete autonomous workflow:**

```bash
#!/bin/bash
set -e  # Exit on error

echo "=== FedSpeak Autonomous Execution ==="

# 1. Environment check
echo "[1/7] Checking environment..."
python -c "from src.core.shift_detector import ShiftDetector" || {
    echo "ERROR: Module import failed"
    echo "ACTION: Run 'pip install -r requirements.txt'"
    exit 1
}

# 2. Configuration check
echo "[2/7] Checking configuration..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set"
    echo "MILA will be disabled. Set to 'sk-ant-999999999999' for local routing."
    echo "Continuing without MILA..."
fi

# 3. Start dashboard (background)
echo "[3/7] Starting dashboard..."
python src/dashboard/app.py &
DASHBOARD_PID=$!
sleep 3  # Wait for startup

# Verify dashboard is running
curl -s http://localhost:5000/api/stats >/dev/null || {
    echo "ERROR: Dashboard failed to start"
    kill $DASHBOARD_PID 2>/dev/null
    exit 1
}
echo "Dashboard started (PID: $DASHBOARD_PID)"

# 4. Run monitor once
echo "[4/7] Running shift detection..."
python src/monitor.py

# 5. Check results
echo "[5/7] Analyzing results..."
ALERT_COUNT=$(find data/alerts -name "ALERT-*.json" 2>/dev/null | wc -l)
echo "Total alerts: $ALERT_COUNT"

if [ $ALERT_COUNT -gt 0 ]; then
    # Get tier distribution
    echo "Alert tier distribution:"
    grep -h '"tier":' data/alerts/*.json | awk '{print $2}' | tr -d ',' | sort | uniq -c

    # Show recent shifts
    echo ""
    echo "Recent shifts detected:"
    find data/alerts -name "ALERT-*.json" -mtime -7 | while read alert; do
        python -c "
import json
with open('$alert') as f:
    a = json.load(f)
print(f\"  {a['alert_id']}: {a['term']} ({a['tier']}, {a['confidence']})\")
"
    done
fi

# 6. Run tests
echo "[6/7] Running validation tests..."
pytest tests/ -q --tb=no 2>&1 | tail -5

# 7. Cleanup
echo "[7/7] Cleanup..."
kill $DASHBOARD_PID 2>/dev/null || true

echo ""
echo "=== EXECUTION COMPLETE ==="
echo "Dashboard PID: $DASHBOARD_PID (stopped)"
echo "Alerts: $ALERT_COUNT"
echo "Logs: logs/fedspeak.log"
exit 0
```

---

## API Reference Quick Guide

**Dashboard API:**
- `GET /api/alerts` - List alerts (supports filtering: ?tier=1&confidence=high&start_date=2021-01-01)
- `GET /api/alerts/<alert_id>` - Get specific alert
- `GET /api/alerts.csv` - Export all alerts to CSV
- `GET /api/stats` - System statistics

**Word2Vec Explorer API:**
- `GET /api/explore/similar?word={term}&topn=10` - Find similar terms
- `GET /api/explore/proximity?word={term}` - Calculate policy proximity
- `GET /api/explore/similarity?word1={term1}&word2={term2}` - Word-to-word similarity
- `GET /api/explore/vocabulary` - Model statistics
- `GET /api/explore/search?q={query}&limit=20` - Autocomplete search

**MILA Explainability API:**
- `GET /api/explainability/stance/<date>` - Get stance analysis for statement
- `GET /api/explainability/cost` - API cost tracking
- `GET /api/visualizations/stance-trend?start_date={date}&end_date={date}` - Stance timeline

See API_DOCUMENTATION.md for complete reference with examples.

---

## Summary Checklist

**Before executing autonomous workflow:**
- [ ] Python 3.11+ installed
- [ ] Virtual environment activated (venv_fedspeak_prod)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] ANTHROPIC_API_KEY set (cloud or local routing)
- [ ] Directories exist (data/, logs/)
- [ ] Word2Vec model exists (prototypes/results/fed_word2vec.model)
- [ ] Port 5000 available

**After system start:**
- [ ] Dashboard accessible (http://localhost:5000)
- [ ] API endpoints responding (`/api/stats`)
- [ ] Monitor running (check logs/fedspeak.log)
- [ ] No errors in logs (`grep ERROR logs/fedspeak.log`)

**Validation:**
- [ ] Run test suite (`pytest tests/` → 175 passed)
- [ ] Check known shift (December 2021 "transitory" detected)
- [ ] Verify routing mode (check logs for "via Anthropic API (cloud)" or "via Claude Code (local)")

---

**Last Updated:** November 9, 2025
**System Version:** FedSpeak v1.0 (Word2Vec + Multi-Signal + MILA)
**Optimized for:** Claude Code, autonomous AI agents, DevOps automation
**Companion Guides:**
- USER_GUIDE.md (human analysts)
- PRODUCTION_RUNBOOK.md (operations/deployment)
- API_DOCUMENTATION.md (API reference)
- LAYMAN_GUIDE.md (non-technical overview)
