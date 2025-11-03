# FedSpeak Deployment Guide

**Version**: 1.0
**Last Updated**: November 2, 2025
**Status**: Production Ready

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Scheduling Automated Runs](#scheduling-automated-runs)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## System Requirements

### Software Requirements

- **Python**: 3.8 or higher
- **pip**: Package manager
- **Operating System**: Linux, macOS, or Windows (WSL recommended)

### Hardware Requirements

- **CPU**: Single core sufficient
- **RAM**: 2 GB minimum
- **Disk Space**:
  - Code and dependencies: ~100 MB
  - Data storage: ~50 MB (grows ~2 MB/year)
  - Results: ~10 MB per analysis run

### Network Requirements

- Internet connectivity for downloading Fed documents
- Access to `federalreserve.gov` (no authentication required)
- Bandwidth: Minimal (<5 MB per run)

---

## Installation

### Step 1: Clone or Copy Repository

```bash
# If using git
git clone <repository-url> FedSpeak
cd FedSpeak

# Or extract from archive
unzip FedSpeak.zip
cd FedSpeak
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed**:
- beautifulsoup4==4.12.2 (HTML parsing)
- lxml==5.1.0 (Parser backend)
- pdfplumber==0.10.3 (PDF extraction)
- pandas==2.1.4 (Data handling)
- matplotlib==3.8.2 (Visualizations)
- requests==2.31.0 (HTTP downloads)
- pyyaml==6.0.1 (Configuration)
- pytest==7.4.3 (Testing)

### Step 4: Verify Installation

```bash
# Test CLI loads
python3 -m fedspeak --help

# Run basic tests
pytest tests/test_basic.py -v
```

**Expected output**:
```
Usage: fedspeak [-h] [--config CONFIG] [--log-level {DEBUG,INFO,WARNING,ERROR}]
                {download,extract,analyze,report} ...
```

---

## Configuration

### Configuration File: `config/config.yaml`

The system is configured via YAML. Key sections:

#### 1. Keywords to Track

```yaml
keywords:
  - word: "transitory"
    type: "deletion"
    context: "inflation narrative"
    shift_id: "SHIFT-2021-01"
    enabled: true
    priority: "high"
```

**To add new keywords**:
1. Open `config/config.yaml`
2. Add new entry under `keywords:` section
3. Include: word, type, context, significance
4. Set `enabled: true`

#### 2. Detection Parameters

```yaml
detection:
  sustained_removal_threshold: 3  # Consecutive docs to confirm removal
  baseline_window_months: 6       # Historical window
  min_baseline_samples: 3         # Minimum docs for baseline
  focus_document_type: policy_statement  # Primary doc type
```

**Tuning recommendations**:
- `sustained_removal_threshold: 3` - Good default, increase to reduce false positives
- `baseline_window_months: 6` - Standard Fed meeting cycle (8x/year)
- `focus_document_type` - Use `policy_statement` for clearest signals

#### 3. File Paths

```yaml
corpus:
  data_dir: "data/"
  raw_subdir: "raw/"
  processed_subdir: "processed/"
  metadata_subdir: "metadata/"
```

**Customization**: Change `data_dir` to store data elsewhere

#### 4. Download Settings

```yaml
download:
  delay_seconds: 1        # Rate limiting (respectful to Fed servers)
  retry_attempts: 3       # Max retries
  timeout_seconds: 30     # Request timeout
```

**Important**: Keep `delay_seconds: 1` to respect Fed servers

---

## Running the System

### Basic Workflow

FedSpeak operates in 4 stages:

1. **Download** → 2. **Extract** → 3. **Analyze** → 4. **Report**

### Stage 1: Download Documents

```bash
python3 -m fedspeak download \
  --start-date 2020-01-01 \
  --end-date 2023-12-31
```

**Options**:
- `--start-date YYYY-MM-DD` (required): Start of date range
- `--end-date YYYY-MM-DD` (optional): End of range (default: today)
- `--statements-only`: Download only policy statements (faster)

**Output**: Downloaded files in `data/raw/`

**Duration**: ~2-5 minutes depending on date range

### Stage 2: Extract Text

```bash
python3 -m fedspeak extract
```

**What it does**:
- Parses HTML and PDF documents
- Removes boilerplate (navigation, footers, etc.)
- Extracts policy-relevant text
- Validates word count thresholds

**Output**: Extracted text in `data/processed/*.txt`

**Duration**: ~5-10 seconds for typical corpus

### Stage 3: Analyze for Shifts

```bash
python3 -m fedspeak analyze
```

**What it does**:
1. Counts keyword occurrences in each document
2. Calculates baselines (6-month rolling window)
3. Detects emergence (0 → >0) and removal (>0 → 0)
4. Generates alerts with evidence
5. Creates timeline visualizations

**Output**:
- `data/metadata/keyword_metrics.csv` - Time-series data
- `results/alerts/*.json` and `*.txt` - Alert files
- `results/visualizations/*.png` - Timeline charts

**Duration**: <1 second for typical corpus

### Stage 4: View Report

```bash
python3 -m fedspeak report
```

**What it does**:
- Loads metrics from analysis
- Displays summary statistics
- Shows top keywords by frequency

**Example output**:
```
[REPORT] Generating summary...

[SUMMARY] Corpus Statistics:
  Documents analyzed: 66
  Keywords tracked: 5
  Date range: 2008-12-16 to 2023-03-22

[KEYWORDS] Most Frequent Terms:
  transitory: 42 total occurrences
  accommodative: 38 total occurrences
  patient: 15 total occurrences
  ...

[SUCCESS] Report complete!
```

### Full Pipeline (One Command)

```bash
# Download, extract, and analyze in sequence
python3 -m fedspeak download --start-date 2020-01-01 && \
python3 -m fedspeak extract && \
python3 -m fedspeak analyze && \
python3 -m fedspeak report
```

---

## Scheduling Automated Runs

### Option 1: Cron (Linux/Mac)

Run analysis weekly to check for new FOMC documents:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM)
0 9 * * 1 cd /path/to/FedSpeak && /path/to/venv/bin/python3 -m fedspeak analyze >> logs/cron.log 2>&1
```

### Option 2: Systemd Timer (Linux)

Create `/etc/systemd/system/fedspeak.service`:

```ini
[Unit]
Description=FedSpeak Language Shift Analysis
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/FedSpeak
ExecStart=/path/to/venv/bin/python3 -m fedspeak analyze
StandardOutput=append:/path/to/FedSpeak/logs/systemd.log
StandardError=append:/path/to/FedSpeak/logs/systemd.log
```

Create `/etc/systemd/system/fedspeak.timer`:

```ini
[Unit]
Description=Run FedSpeak weekly
Requires=fedspeak.service

[Timer]
OnCalendar=Mon *-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fedspeak.timer
sudo systemctl start fedspeak.timer
```

### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Monday 9:00 AM
4. Action: Start a program
   - Program: `C:\path\to\FedSpeak\venv\Scripts\python.exe`
   - Arguments: `-m fedspeak analyze`
   - Start in: `C:\path\to\FedSpeak`

### Recommended Schedule

**For production monitoring**:
- Run analysis **weekly** (FOMC meets ~8x per year)
- Run on **Mondays** (most FOMC meetings are Wed, statements published same day)
- Time: **9 AM local** (after market open)

**For development/testing**:
- Run analysis **on-demand** after downloading new documents

---

## Monitoring and Logging

### Log Files

**Log locations**:
- Application logs: `logs/` (if logging to file configured)
- Cron logs: `logs/cron.log` (if using cron)
- Download metadata: `data/metadata/download_log.json`

**Log levels** (set via `--log-level`):
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages

**Example**:
```bash
python3 -m fedspeak analyze --log-level DEBUG
```

### Health Checks

**Manual health check script** (create `scripts/health_check.sh`):

```bash
#!/bin/bash

echo "FedSpeak Health Check"
echo "====================="

# Check Python version
python3 --version || exit 1

# Check dependencies
pip show beautifulsoup4 > /dev/null || exit 1

# Check data directories exist
[ -d data/raw ] || exit 1
[ -d data/processed ] || exit 1
[ -d results/alerts ] || exit 1

# Check recent analysis
if [ -f data/metadata/keyword_metrics.csv ]; then
  echo "Last analysis: $(stat -c %y data/metadata/keyword_metrics.csv)"
else
  echo "WARNING: No analysis found"
  exit 1
fi

echo "Health check PASSED"
```

### Alert Notification

**Email alerts** (requires `mail` or `sendmail`):

Add to analysis script:

```bash
#!/bin/bash
cd /path/to/FedSpeak
python3 -m fedspeak analyze

# Check if new alerts generated
ALERT_COUNT=$(ls -1 results/alerts/*.txt 2>/dev/null | wc -l)

if [ $ALERT_COUNT -gt 0 ]; then
  echo "FedSpeak detected $ALERT_COUNT language shifts!" | \
    mail -s "FedSpeak Alert" your-email@example.com
fi
```

**Slack/Discord webhook** (requires `curl`):

```bash
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

curl -X POST $WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"FedSpeak detected $ALERT_COUNT language shifts!\"}"
```

---

## Troubleshooting

### Common Issues

#### 1. "Module not found" errors

**Cause**: Dependencies not installed or virtual environment not activated

**Fix**:
```bash
source venv/bin/activate  # Activate venv
pip install -r requirements.txt  # Install dependencies
```

#### 2. "404 Not Found" during download

**Cause**: Document doesn't exist for that date (FOMC doesn't meet every day)

**Fix**: This is expected. The system logs warnings but continues. To avoid:
- Use actual FOMC meeting dates
- Check Fed calendar: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

#### 3. "No text files found" during analysis

**Cause**: Extraction step not run or failed

**Fix**:
```bash
# Check if raw files exist
ls data/raw/*.html

# Re-run extraction
python3 -m fedspeak extract
```

#### 4. "Object of type int64 is not JSON serializable"

**Cause**: This bug was fixed in the current version

**Fix**: Update to latest version with bug fixes applied

#### 5. Performance is slow

**Cause**: Old version with O(n²) baseline calculation

**Fix**: Update to latest version with vectorized calculation

#### 6. "Failed to analyze" errors for all documents

**Cause**: Filename parsing issue with .html.txt extensions

**Fix**: Update to latest version with fixed date parsing

### Debug Mode

Run with debug logging to diagnose issues:

```bash
python3 -m fedspeak analyze --log-level DEBUG 2>&1 | tee debug.log
```

Review `debug.log` for detailed error messages.

---

## Maintenance

### Regular Maintenance Tasks

#### Weekly
- ✓ Check for new FOMC documents
- ✓ Run analysis
- ✓ Review alerts

#### Monthly
- ✓ Review log files for errors
- ✓ Check disk space usage
- ✓ Verify scheduled tasks running

#### Quarterly
- ✓ Update dependencies: `pip install --upgrade -r requirements.txt`
- ✓ Review and tune detection parameters
- ✓ Expand keyword catalog if needed
- ✓ Backup data directory

### Updating Keywords

To add keywords for new shifts:

1. Edit `config/config.yaml`
2. Add new keyword entry
3. Re-run analysis:
   ```bash
   python3 -m fedspeak analyze
   ```

### Upgrading Python Version

```bash
# Create new venv with new Python version
python3.11 -m venv venv-new

# Activate and reinstall
source venv-new/bin/activate
pip install -r requirements.txt

# Test
python3 -m fedspeak --help

# If successful, replace old venv
mv venv venv-old
mv venv-new venv
```

### Backup Strategy

**What to backup**:
- `data/raw/` - Downloaded documents (can re-download if needed)
- `data/metadata/keyword_metrics.csv` - Analysis results
- `config/config.yaml` - Custom configuration
- `results/alerts/` - Generated alerts

**Backup script** (example):

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups/fedspeak
tar -czf $BACKUP_DIR/fedspeak-$DATE.tar.gz \
  data/metadata \
  config/config.yaml \
  results/alerts
```

### Performance Monitoring

Track analysis performance over time:

```bash
# Add to analysis script
START_TIME=$(date +%s)
python3 -m fedspeak analyze
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "$(date),${DURATION}s" >> logs/performance.csv
```

---

## Security Considerations

### Data Privacy

- FedSpeak analyzes publicly available Fed documents
- No personal or sensitive data processed
- No authentication credentials required

### Network Security

- Downloads from federalreserve.gov only (no third-party sources)
- Uses HTTPS for all requests
- Implements rate limiting (1 sec delay) to be respectful

### File Permissions

Recommended permissions:

```bash
chmod 755 fedspeak/          # Executable scripts
chmod 644 config/config.yaml # Read-only config
chmod 700 data/              # Private data directory
chmod 700 results/           # Private results
```

---

## Support and Troubleshooting

### Getting Help

1. **Check logs**: `logs/` directory for error messages
2. **Review test report**: `TEST_REPORT.md` for known issues
3. **Debug mode**: Run with `--log-level DEBUG`
4. **Documentation**: Review `README.md` and other docs

### Known Limitations

1. Corpus starts 2008 (pre-2008 documents return 404)
2. Uses 6-week approximation for FOMC dates (not actual calendar)
3. Some historical shifts may not be in corpus date range
4. Press transcripts require manual date handling

### Future Enhancements

See PROJECT_STATUS.md "Future Enhancements" section for planned improvements.

---

## Quick Reference

### Essential Commands

```bash
# Full pipeline
python3 -m fedspeak download --start-date 2020-01-01
python3 -m fedspeak extract
python3 -m fedspeak analyze
python3 -m fedspeak report

# View specific alert
cat results/alerts/ALERT-20211215-removal-transitory.txt

# Check system status
ls -lh data/metadata/keyword_metrics.csv
```

### File Locations

| Data Type | Location |
|-----------|----------|
| Configuration | `config/config.yaml` |
| Downloaded docs | `data/raw/*.html` |
| Extracted text | `data/processed/*.txt` |
| Metrics | `data/metadata/keyword_metrics.csv` |
| Alerts | `results/alerts/*.{json,txt}` |
| Visualizations | `results/visualizations/*.png` |
| Logs | `logs/` |

---

*End of Deployment Guide*
