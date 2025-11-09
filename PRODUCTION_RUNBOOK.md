# FedSpeak Production Runbook

**Version**: 1.0
**Last Updated**: November 9, 2025
**System**: FedSpeak FOMC Language Shift Detection
**Status**: Production-Ready (Local Development + Cloud-Ready)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Deployment](#deployment)
4. [Service Management](#service-management)
5. [Configuration Management](#configuration-management)
6. [Monitoring & Logs](#monitoring--logs)
7. [Common Operations](#common-operations)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Maintenance](#maintenance)

---

## System Overview

### What is FedSpeak?

FedSpeak is an automated system for detecting and analyzing language shifts in Federal Reserve FOMC policy statements. It monitors the Federal Reserve RSS feed, runs statistical shift detection on new statements, and enriches alerts with multi-signal validation (market data + media coverage + LLM stance analysis).

### Key Components

1. **Core Detector** (`src/core/detector.py`)
   - Statistical language shift detection using Improved Hybrid Detector algorithm
   - Monitors term frequency changes with Bayesian-inspired hypothesis testing
   - Validated: 53.8% precision, 16.2% recall on 130 ground truth shifts

2. **RSS Monitor** (`src/monitoring/rss_monitor.py`)
   - Polls Federal Reserve press_monetary.xml feed every 5 minutes
   - Automatically downloads and processes new FOMC policy statements
   - Tracks processed statements to avoid duplicates

3. **Multi-Signal Validation** (`src/validation/`)
   - **Market Validator**: FRED API (treasury yields) + Yahoo Finance (VIX, S&P500)
   - **Media Validator**: GDELT Project (news coverage) + FinBERT (sentiment analysis)
   - **Three-tier system**: Tier 1 (70-75% precision), Tier 2 (55-65%), Tier 3 (30-45%)

4. **MILA Framework** (`src/explainability/`)
   - LLM-powered hawkish/dovish stance analysis using Claude 3.5 Sonnet
   - Automatic enrichment for high-confidence alerts
   - Comprehensive cost tracking (~$0.60 one-time, ~$0.03/month ongoing)

5. **Word2Vec Explorer** (`src/exploration/`)
   - Semantic similarity analysis for term exploration
   - Policy proximity scoring with 9 seed terms
   - Interactive dashboard for corpus exploration

6. **Flask Dashboard** (`src/dashboard/app.py`)
   - Main dashboard with filtering, pagination, CSV export
   - Word2Vec exploration interface
   - MILA explainability dashboard with stance visualization
   - JSON API endpoints for programmatic access

7. **Alert Distribution** (`src/distribution/`)
   - File-based deduplication
   - SMTP email distribution (configurable)
   - JSON + human-readable text format

### System Requirements

**Minimum**:
- Python 3.11+
- 4GB RAM
- 10GB disk space (for data cache)
- Internet connection (RSS feed, API calls)

**Recommended**:
- Python 3.11+
- 8GB RAM (for FinBERT model)
- 20GB disk space
- Stable internet connection

---

## Architecture

### High-Level Flow

```
┌─────────────────┐
│  Fed RSS Feed   │ (Every 5 minutes)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RSS Monitor    │ → Downloads new statements
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Core Detector   │ → Detects language shifts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Multi-Signal Val │ → Market + Media validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MILA Analysis   │ → LLM stance classification
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Alert System    │ → Dedup + Email + Dashboard
└─────────────────┘
```

### Directory Structure

```
FedSpeak/
├── src/                           # Source code
│   ├── core/                      # Core detection algorithm
│   │   └── detector.py           # ImprovedDetector class
│   ├── monitoring/                # RSS feed monitoring
│   │   └── rss_monitor.py        # RSSMonitor class
│   ├── validation/                # Multi-signal validation
│   │   ├── market_validator.py   # Market data validation
│   │   ├── media_validator.py    # Media coverage validation
│   │   ├── fred_client.py        # FRED API client
│   │   ├── yahoo_client.py       # Yahoo Finance client
│   │   └── sentiment_analyzer.py # FinBERT sentiment
│   ├── external/                  # External data sources
│   │   ├── gdelt_client.py       # GDELT news API
│   │   └── media_cache.py        # Media data cache
│   ├── explainability/            # MILA framework
│   │   ├── mila_analyzer.py      # Claude 3.5 Sonnet integration
│   │   ├── mila_cache.py         # Stance cache
│   │   └── cost_tracker.py       # API cost tracking
│   ├── exploration/               # Word2Vec tools
│   │   ├── word2vec_service.py   # Word2Vec explorer
│   │   └── policy_proximity.py   # Policy proximity scorer
│   ├── dashboard/                 # Flask web interface
│   │   └── app.py                # Main Flask app
│   ├── distribution/              # Alert distribution
│   │   ├── deduplicator.py       # Alert deduplication
│   │   └── email_sender.py       # Email sender
│   ├── config/                    # Configuration
│   │   └── settings.py           # Settings loader
│   ├── exceptions.py              # Custom exceptions
│   └── monitor.py                 # Main orchestrator
├── data/                          # Data directory
│   ├── processed/                 # FOMC statements
│   ├── market_cache/              # Market data cache
│   │   ├── dgs2/                  # 2-year treasury yields
│   │   ├── dgs10/                 # 10-year treasury yields
│   │   ├── vix/                   # VIX data
│   │   └── spy/                   # S&P 500 data
│   ├── media_cache/               # Media coverage cache
│   │   ├── gdelt/                 # GDELT news data
│   │   └── sentiment/             # FinBERT sentiment
│   └── mila_cache/                # MILA stance cache
│       ├── stance/                # Stance analysis results
│       └── cost_tracking.json     # API cost tracking
├── results/                       # Output directory
│   └── alerts/                    # Generated alerts
├── logs/                          # Log files
├── templates/                     # Flask HTML templates
├── config/                        # Configuration files
│   └── config.yaml               # Main configuration
├── tests/                         # Test suite (175 tests)
├── prototypes/                    # Research prototypes
│   └── results/                   # Trained models
│       └── fed_word2vec.model    # Word2Vec model (993KB)
└── requirements.txt               # Python dependencies
```

### Data Flow

1. **RSS Monitoring** → Polls Federal Reserve feed every 5 minutes
2. **Statement Download** → Saves to `data/processed/`
3. **Shift Detection** → Runs Improved Hybrid Detector on configured terms
4. **Market Validation** → Fetches treasury yields, VIX, S&P 500 (cached)
5. **Media Validation** → Searches GDELT news, analyzes sentiment with FinBERT (cached)
6. **Tier Assignment** → Determines alert tier (1/2/3) based on multi-signal validation
7. **MILA Analysis** → If high-confidence, runs LLM stance classification (cached)
8. **Alert Generation** → Creates JSON + text alerts in `results/alerts/`
9. **Deduplication** → Checks if alert already exists
10. **Distribution** → Sends email (if enabled) + updates dashboard

---

## Deployment

### Local Development (Current Setup)

**Prerequisites**:
```bash
# Verify Python version
python3 --version  # Should be 3.11+

# Verify virtual environment
ls venv_fedspeak_prod/

# Verify dependencies
venv_fedspeak_prod/bin/pip list | head -20
```

**Installation**:
```bash
# Clone repository
git clone https://github.com/jimmc414/FedSpeak.git
cd FedSpeak

# Create virtual environment
python3.11 -m venv venv_fedspeak_prod

# Install dependencies
venv_fedspeak_prod/bin/pip install -r requirements.txt

# Verify installation
venv_fedspeak_prod/bin/pytest tests/ -q
# Should show: 175 passed
```

**Environment Variables**:
```bash
# Optional: ANTHROPIC_API_KEY for MILA
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: FRED_API_KEY for market validation
export FRED_API_KEY="your-fred-key"

# Optional: Email SMTP (if using email distribution)
export SMTP_PASSWORD="your-smtp-password"
```

**Directory Setup**:
```bash
# Create required directories
mkdir -p data/processed
mkdir -p data/market_cache/{dgs2,dgs10,vix,spy}
mkdir -p data/media_cache/{gdelt,sentiment}
mkdir -p data/mila_cache/{stance}
mkdir -p results/alerts
mkdir -p logs
```

### Production Deployment (Cloud-Ready)

**Option 1: AWS EC2**

```bash
# Launch EC2 instance (t3.medium or larger)
# Ubuntu 22.04 LTS, 8GB RAM, 20GB disk

# SSH into instance
ssh -i your-key.pem ubuntu@ec2-instance

# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Clone and setup
git clone https://github.com/jimmc414/FedSpeak.git
cd FedSpeak
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="..."
export FRED_API_KEY="..."

# Test
pytest tests/ -q

# Run monitor
python src/monitor.py --continuous --interval 300
```

**Option 2: Docker** (production-ready container)

```dockerfile
# Dockerfile (create this file)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p data/processed data/market_cache data/media_cache \
    data/mila_cache/stance results/alerts logs

# Expose Flask port
EXPOSE 5000

# Default command
CMD ["python", "src/monitor.py", "--continuous", "--interval", "300"]
```

```bash
# Build Docker image
docker build -t fedspeak:latest .

# Run monitor
docker run -d \
  --name fedspeak-monitor \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  -e ANTHROPIC_API_KEY="..." \
  -e FRED_API_KEY="..." \
  fedspeak:latest

# Run dashboard
docker run -d \
  --name fedspeak-dashboard \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  fedspeak:latest \
  python src/dashboard/app.py
```

**Option 3: systemd Service** (for Linux servers)

```ini
# /etc/systemd/system/fedspeak-monitor.service
[Unit]
Description=FedSpeak FOMC Monitor
After=network.target

[Service]
Type=simple
User=fedspeak
Group=fedspeak
WorkingDirectory=/opt/fedspeak
Environment="PATH=/opt/fedspeak/venv/bin"
Environment="ANTHROPIC_API_KEY=sk-ant-..."
Environment="FRED_API_KEY=..."
ExecStart=/opt/fedspeak/venv/bin/python src/monitor.py --continuous --interval 300
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
# Setup systemd service
sudo systemctl daemon-reload
sudo systemctl enable fedspeak-monitor
sudo systemctl start fedspeak-monitor
sudo systemctl status fedspeak-monitor
```

---

## Service Management

### Starting Services

**Monitor (Continuous RSS Monitoring)**:
```bash
# Local development
venv_fedspeak_prod/bin/python src/monitor.py --continuous --interval 300

# Production (systemd)
sudo systemctl start fedspeak-monitor

# Docker
docker start fedspeak-monitor
```

**Dashboard (Flask Web Interface)**:
```bash
# Local development (http://localhost:5000)
venv_fedspeak_prod/bin/python src/dashboard/app.py

# Production (with gunicorn)
venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 'src.dashboard.app:app'

# Docker
docker start fedspeak-dashboard
```

### Stopping Services

```bash
# Monitor
# Local: Ctrl+C
# systemd: sudo systemctl stop fedspeak-monitor
# Docker: docker stop fedspeak-monitor

# Dashboard
# Local: Ctrl+C
# systemd: sudo systemctl stop fedspeak-dashboard
# Docker: docker stop fedspeak-dashboard
```

### Restarting Services

```bash
# systemd
sudo systemctl restart fedspeak-monitor

# Docker
docker restart fedspeak-monitor
```

### Checking Status

```bash
# systemd
sudo systemctl status fedspeak-monitor

# Docker
docker ps | grep fedspeak
docker logs fedspeak-monitor --tail 100
```

---

## Configuration Management

### Main Configuration (`config/config.yaml`)

**Location**: `config/config.yaml`

**Key Sections**:

1. **Keywords** - Terms to monitor for shifts
2. **Monitoring** - RSS feed settings
3. **Distribution** - Email/alert settings
4. **Market Validation** - FRED/Yahoo Finance settings
5. **Media Validation** - GDELT/FinBERT settings
6. **Explainability** - MILA/LLM settings

**Example Configuration**:
```yaml
# Monitored keywords
keywords:
  - word: "transitory"
    enabled: true
    priority: "high"
  - word: "accommodative"
    enabled: true
    priority: "high"

# RSS monitoring
monitoring:
  rss_url: "https://www.federalreserve.gov/feeds/press_monetary.xml"
  check_interval_seconds: 300  # 5 minutes
  data_dir: "data/processed"

# Email distribution
distribution:
  email:
    enabled: false  # Set to true for production
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_email: "fedspeak@example.com"
    recipients:
      - "analyst1@example.com"
      - "analyst2@example.com"

# Market validation (Phase 5)
market_validation:
  enabled: true
  fred_api_key: "${FRED_API_KEY}"  # From environment variable
  tier_1_threshold: 0.6  # Score ≥0.6 + ≥2 indicators
  cache_dir: "data/market_cache"

# Media validation (Phase 6)
media_validation:
  enabled: true
  gdelt:
    timeout_seconds: 30
    max_results: 100
  finbert:
    model_name: "yiyanghkust/finbert-tone"
    top_n_articles: 20
  cache_dir: "data/media_cache"

# MILA (Phase 8)
explainability:
  mila:
    enabled: true
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-5-sonnet-20241022"
    temperature: 0.1
    budget_alert_threshold: 500.0  # USD
    cache_dir: "data/mila_cache"
```

### Environment Variables

**Setting Environment Variables**:
```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-..."
export FRED_API_KEY="your-fred-key"

# Windows
set ANTHROPIC_API_KEY=sk-ant-...
set FRED_API_KEY=your-fred-key

# Docker
docker run -e ANTHROPIC_API_KEY="..." fedspeak:latest

# systemd (in service file)
Environment="ANTHROPIC_API_KEY=..."
```

**Verifying Configuration**:
```bash
# Test configuration loading
venv_fedspeak_prod/bin/python -c "
from src.config.settings import get_settings
settings = get_settings()
print(f'Keywords: {len(settings.get(\"keywords\", []))}')
print(f'Market validation: {settings.get(\"market_validation.enabled\", False)}')
"
```

### Secrets Management

**Local Development**:
- Use `.env` file (git-ignored)
- Source with `source .env`

**Production**:
- Use AWS Secrets Manager, HashiCorp Vault, or similar
- Never commit secrets to git
- Rotate API keys regularly

---

## Monitoring & Logs

### Log Locations

```bash
# Application logs
logs/fedspeak.log          # Main application log
logs/fedspeak.log.1        # Rotated log (daily rotation)

# System logs (if using systemd)
sudo journalctl -u fedspeak-monitor -f

# Docker logs
docker logs fedspeak-monitor --follow
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages (RSS checks, detections, etc.)
- **WARNING**: Warning messages (API failures, validation issues)
- **ERROR**: Error messages (unexpected failures)
- **CRITICAL**: Critical system errors

### Viewing Logs

```bash
# Tail main log
tail -f logs/fedspeak.log

# Search for errors
grep ERROR logs/fedspeak.log

# Filter by component
grep "MarketValidator" logs/fedspeak.log

# Last 100 lines
tail -100 logs/fedspeak.log
```

### Key Log Messages

**Normal Operation**:
```
INFO: FOMCMonitor initialized. Monitoring 4 terms
INFO: Email distribution: disabled
INFO: Market validation: enabled
INFO: Media validation: enabled
INFO: MILA stance analysis: enabled
INFO: === Starting FOMC Monitor Check ===
INFO: No new statements found
INFO: === Check Complete: 0 alerts generated ===
```

**New Statement Detected**:
```
INFO: Downloaded 1 new statements: ['20231101']
INFO: Running detection for term: 'transitory'
INFO: Found 1 shifts for 'transitory' in new statements
INFO: Market validation: True (score: 0.72)
INFO: Media validation: True (coverage: 85, sources: 25, sentiment: -0.45)
INFO: MILA analysis: hawkish (score: 0.78, confidence: 0.92)
INFO: Alert tier: 1 (tier_1) - Statistical: high, Market: True, Media: True
INFO: Saved alert to results/alerts/ALERT-20231101-emergence-transitory.json
```

**Warnings**:
```
WARNING: FRED API request failed: HTTPError 429
WARNING: Market validation failed for ALERT-...: Rate limit exceeded
WARNING: MILA disabled (missing ANTHROPIC_API_KEY)
```

### Metrics to Monitor

1. **RSS Feed Checks**: Every 5 minutes (should see ~288/day)
2. **New Statements**: ~2-4 per month (FOMC schedule)
3. **Detections**: Varies (depends on language shifts)
4. **Tier 1 Alerts**: High precision (70-75%), expect 1-2/year
5. **API Costs**: MILA ~$0.03/month, FRED free, GDELT free
6. **Cache Hit Rates**: Market >90%, Media >80%, MILA >95%

### Health Checks

```bash
# Quick health check
venv_fedspeak_prod/bin/python -c "
from src.monitor import FOMCMonitor
monitor = FOMCMonitor()
print('✓ Monitor initialized successfully')
"

# Full health check (including API connectivity)
venv_fedspeak_prod/bin/python -c "
from src.validation import MarketValidator, MediaValidator
from src.explainability import MILAAnalyzer

# Test market validation
market = MarketValidator()
print(f'Market validation: {\"enabled\" if market.enabled else \"disabled\"}')

# Test media validation
media = MediaValidator()
print(f'Media validation: {\"enabled\" if media.enabled else \"disabled\"}')

# Test MILA
mila = MILAAnalyzer()
print(f'MILA: {\"enabled\" if mila.is_enabled() else \"disabled\"}')
"
```

---

## Common Operations

### Running a Manual Check

```bash
# Check RSS feed once (don't run continuous)
venv_fedspeak_prod/bin/python src/monitor.py

# Output shows:
# - Number of new statements found
# - Detections and alerts generated
# - Files saved
```

### Starting Continuous Monitoring

```bash
# Run in foreground (Ctrl+C to stop)
venv_fedspeak_prod/bin/python src/monitor.py --continuous --interval 300

# Run in background (Linux/Mac)
nohup venv_fedspeak_prod/bin/python src/monitor.py --continuous --interval 300 > logs/monitor.out 2>&1 &

# Check if running
ps aux | grep "src/monitor.py"
```

### Accessing the Dashboard

```bash
# Start Flask dashboard
venv_fedspeak_prod/bin/python src/dashboard/app.py

# Open browser to:
# http://localhost:5000          # Main dashboard
# http://localhost:5000/explore  # Word2Vec explorer
# http://localhost:5000/explainability  # MILA stance analysis
```

### Exporting Alerts

**Via Dashboard**:
- Visit http://localhost:5000
- Apply filters (date range, confidence, tier)
- Click "Export CSV" button

**Via API**:
```bash
# Get all alerts as JSON
curl http://localhost:5000/api/alerts > alerts.json

# Get CSV export
curl http://localhost:5000/api/alerts.csv > alerts.csv

# Filter by tier
curl "http://localhost:5000/api/alerts?tier=1" > tier1_alerts.json
```

**From Files**:
```bash
# Find all Tier 1 alerts
grep -l "\"tier\": 1" results/alerts/*.json

# Extract alert summaries
jq '{alert_id, term, date: .document.date, tier, confidence}' results/alerts/ALERT-*.json
```

### Running Tests

```bash
# Run all tests
venv_fedspeak_prod/bin/pytest tests/ -v

# Run specific test file
venv_fedspeak_prod/bin/pytest tests/test_detector.py -v

# Run with coverage report
venv_fedspeak_prod/bin/pytest tests/ --cov=src --cov-report=html

# Quick test (quiet mode)
venv_fedspeak_prod/bin/pytest tests/ -q
# Should show: 175 passed
```

### Clearing Cache

```bash
# Clear market cache (to re-fetch data)
rm -rf data/market_cache/*
mkdir -p data/market_cache/{dgs2,dgs10,vix,spy}

# Clear media cache
rm -rf data/media_cache/*
mkdir -p data/media_cache/{gdelt,sentiment}

# Clear MILA cache (only if model/prompt changed)
rm -rf data/mila_cache/stance/*

# Note: Clearing MILA cache will incur API costs to re-analyze statements
```

### Updating Configuration

```bash
# Edit configuration
nano config/config.yaml

# Verify syntax
venv_fedspeak_prod/bin/python -c "
import yaml
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)
print('✓ Configuration valid')
"

# Restart services for changes to take effect
# (monitor must be restarted, dashboard usually hot-reloads)
```

---

## Troubleshooting

### Common Issues

#### 1. "No new statements found" (expected)

**Symptom**: Monitor runs but no alerts generated

**Cause**: FOMC only publishes ~8-10 statements per year

**Solution**: This is normal. Check Federal Reserve calendar:
```bash
# Manually check RSS feed
curl https://www.federalreserve.gov/feeds/press_monetary.xml | grep -i "policy"
```

#### 2. "MILA disabled (missing ANTHROPIC_API_KEY)"

**Symptom**: Dashboard shows 503 error on /explainability

**Cause**: ANTHROPIC_API_KEY not set

**Solution**:
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Restart dashboard
venv_fedspeak_prod/bin/python src/dashboard/app.py
```

#### 3. "Market validation failed: Rate limit exceeded"

**Symptom**: Market validation warnings in logs

**Cause**: FRED or Yahoo Finance rate limit hit

**Solution**: Market data is cached, so this is temporary:
```bash
# Check cache contents
ls -lh data/market_cache/dgs2/

# If cache exists, validation will use cached data
# Rate limits reset after 1 hour (FRED) or 1 day (Yahoo)
```

#### 4. "ModuleNotFoundError: No module named 'torch'"

**Symptom**: Media validation tests fail

**Cause**: torch/transformers not installed

**Solution**:
```bash
# Install missing dependencies
venv_fedspeak_prod/bin/pip install torch transformers

# Verify
venv_fedspeak_prod/bin/python -c "import torch; print(torch.__version__)"
```

#### 5. "FinBERT model download failed"

**Symptom**: First media validation is slow or fails

**Cause**: FinBERT model (~400MB) downloads on first use

**Solution**: Wait for download to complete (one-time only):
```bash
# Monitor download
tail -f logs/fedspeak.log | grep "finbert"

# Model caches to: ~/.cache/huggingface/
```

#### 6. "Dashboard shows no alerts"

**Symptom**: Dashboard is empty

**Cause**: No alerts generated yet OR alert age filter

**Solution**:
```bash
# Check if alerts exist
ls -l results/alerts/

# If empty, run manual detection on historical data
venv_fedspeak_prod/bin/python -c "
from src.monitor import FOMCMonitor
monitor = FOMCMonitor()
alerts = monitor.check_once()
print(f'Generated {len(alerts)} alerts')
"

# Dashboard filters alerts by age (default: 90 days)
# Check config.yaml: alerts.max_age_days
```

#### 7. "Email sending failed"

**Symptom**: Alerts generated but email not sent

**Cause**: SMTP configuration incorrect or email disabled

**Solution**:
```bash
# Check email configuration
grep -A 10 "distribution:" config/config.yaml

# Test SMTP (Python debug server)
# Terminal 1:
python -m smtpd -c DebuggingServer -n localhost:1025

# Terminal 2: Update config to use localhost:1025, run monitor
# Emails will print to Terminal 1
```

#### 8. "Git push rejected"

**Symptom**: Cannot push changes to GitHub

**Cause**: Remote has changes not in local

**Solution**:
```bash
# Pull latest changes
git pull --rebase origin master

# Resolve conflicts if any
git status

# Push
git push origin master
```

### Performance Issues

#### Slow Dashboard

**Symptom**: Dashboard takes >5 seconds to load

**Cause**: Too many alerts OR large statement files

**Solution**:
```bash
# Check alert count
ls results/alerts/*.json | wc -l

# If >1000 alerts, consider archiving old ones:
mkdir -p results/alerts_archive
mv results/alerts/ALERT-202[0-2]*.json results/alerts_archive/

# Or adjust max_age_days in config.yaml
```

#### High Memory Usage

**Symptom**: Process uses >4GB RAM

**Cause**: FinBERT model loaded + Word2Vec model + Flask

**Solution**:
```bash
# Check memory usage
ps aux | grep python

# Reduce FinBERT batch size in config.yaml:
# media_validation.finbert.batch_size: 4  # Default: 8

# Or disable media validation if not needed:
# media_validation.enabled: false
```

### Data Issues

#### Missing Statement Files

**Symptom**: Detector fails with "File not found"

**Cause**: Statement files not downloaded

**Solution**:
```bash
# Check data directory
ls -l data/processed/

# Manually download missing statement
# Visit: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
# Or re-run RSS monitor to re-download
```

#### Corrupt Cache Files

**Symptom**: JSON decode errors in logs

**Cause**: Cache file corrupted (disk full, interrupted write)

**Solution**:
```bash
# Find corrupt file from error message
# Example: "JSONDecodeError in data/market_cache/dgs2/2021-12-15.json"

# Remove corrupt file
rm data/market_cache/dgs2/2021-12-15.json

# Re-run - will re-fetch from API
```

---

## Rollback Procedures

### Rolling Back Code

```bash
# Check git history
git log --oneline --graph -10

# Rollback to previous commit
git reset --hard <commit-hash>

# Example: Rollback to before Phase 9
git reset --hard 6a9228a

# If already pushed to remote
git push --force origin master  # DANGEROUS - only if sole user
```

### Rolling Back Configuration

```bash
# Restore previous config
git checkout HEAD~1 config/config.yaml

# Or restore from backup
cp config/config.yaml.backup config/config.yaml
```

### Restoring Data

```bash
# Restore from backup (if you have one)
tar -xzf fedspeak_backup_2025-11-08.tar.gz -C /

# Or re-download statements
rm data/processed/*.txt
python src/monitor.py  # Will re-download all statements from RSS
```

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor logs for errors: `grep ERROR logs/fedspeak.log`
- Check alert generation: `ls -lt results/alerts/ | head -10`

**Weekly**:
- Review cache sizes: `du -sh data/*_cache/`
- Check API cost: Visit dashboard `/explainability`, review cost widget
- Verify tests pass: `pytest tests/ -q`

**Monthly**:
- Clean old cache files: `find data/ -name "*.json" -mtime +90 -delete`
- Review and archive old alerts: `mv results/alerts/ALERT-2024*.json results/archive/`
- Update dependencies: `pip list --outdated`

**Quarterly**:
- Review configuration: Check for new keywords to monitor
- Validate tier thresholds: Run backtests on recent data
- Security audit: Rotate API keys, review access logs

### Backup Procedures

**What to Back Up**:
```bash
# Configuration
config/config.yaml

# Data (statements and cache)
data/processed/
data/market_cache/
data/media_cache/
data/mila_cache/

# Alerts
results/alerts/

# Logs (last 30 days)
logs/fedspeak.log*

# Trained models
prototypes/results/fed_word2vec.model
```

**Backup Script**:
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backups/fedspeak"
mkdir -p $BACKUP_DIR

# Create tarball
tar -czf $BACKUP_DIR/fedspeak_$DATE.tar.gz \
  config/ \
  data/ \
  results/ \
  logs/*.log \
  prototypes/results/

# Keep last 30 days
find $BACKUP_DIR -name "fedspeak_*.tar.gz" -mtime +30 -delete

echo "Backup complete: $BACKUP_DIR/fedspeak_$DATE.tar.gz"
```

**Automated Backups** (cron):
```bash
# Run daily at 2 AM
0 2 * * * /opt/fedspeak/backup.sh >> /var/log/fedspeak_backup.log 2>&1
```

### Dependency Updates

```bash
# Check for outdated packages
venv_fedspeak_prod/bin/pip list --outdated

# Update specific package
venv_fedspeak_prod/bin/pip install --upgrade anthropic

# Update all packages (CAREFUL - test thoroughly)
venv_fedspeak_prod/bin/pip install --upgrade -r requirements.txt

# Run tests after updates
venv_fedspeak_prod/bin/pytest tests/ -q
```

### Log Rotation

**Automatic** (built-in):
- Logs rotate daily automatically
- Keep last 7 days
- Location: `logs/fedspeak.log.1`, `logs/fedspeak.log.2`, etc.

**Manual**:
```bash
# Compress old logs
gzip logs/fedspeak.log.*

# Archive logs older than 30 days
find logs/ -name "fedspeak.log.*.gz" -mtime +30 -exec mv {} logs/archive/ \;
```

### Database Maintenance

**Note**: FedSpeak uses file-based storage (no traditional database). Maintenance involves:

```bash
# Clean up duplicate alerts (if any)
cd results/alerts/
for f in *.json; do
  CHECKSUM=$(md5sum "$f" | awk '{print $1}')
  echo "$CHECKSUM $f"
done | sort | uniq -w32 -d  # Shows duplicates

# Rebuild cache statistics
venv_fedspeak_prod/bin/python -c "
from src.validation.cache import MarketDataCache
from src.external.media_cache import MediaDataCache
from src.explainability.mila_cache import MILAStanceCache

market_cache = MarketDataCache()
media_cache = MediaDataCache()
mila_cache = MILAStanceCache()

print('Market cache:', market_cache.get_stats())
print('Media cache:', media_cache.get_stats())
print('MILA cache:', mila_cache.get_stats())
"
```

---

## Support & Resources

### Documentation

- **User Guide**: `docs/USER_GUIDE.md` - For analysts using the system
- **API Documentation**: `docs/API_DOCUMENTATION.md` - API reference
- **Phase Completion Reports**: `docs/PHASE_*_COMPLETION.md` - Implementation details

### Code Resources

- **GitHub Repository**: https://github.com/jimmc414/FedSpeak
- **Issue Tracker**: https://github.com/jimmc414/FedSpeak/issues

### External Resources

- **Federal Reserve RSS**: https://www.federalreserve.gov/feeds/
- **FOMC Statements**: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- **FRED API Docs**: https://fred.stlouisfed.org/docs/api/
- **GDELT API Docs**: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- **Claude API Docs**: https://docs.anthropic.com/

### Getting Help

**For issues or questions**:
1. Check this runbook first
2. Review relevant phase completion document in `docs/`
3. Check GitHub issues
4. Create new issue with detailed description and logs

---

**End of Production Runbook**

*Last Updated: November 9, 2025*
*Version: 1.0*
*System: FedSpeak v1.0 (All 3 Tiers Complete)*
