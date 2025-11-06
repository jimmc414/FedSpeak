# FedSpeak: Federal Reserve Language Shift Detection

FedSpeak automatically detects when the Federal Reserve changes language in its official FOMC communications, identifying semantic shifts, euphemism adoption, and narrative pivots before they become widely recognized.

## Features

- **0-day detection lag**: Detects shifts in the same document they occur
- **Synonym group tracking**: Monitors related terms together (e.g., "transitory" + "transient" + "temporary")
- **Keyword frequency tracking**: Simple, interpretable algorithm using whole-word regex matching
- **Complete automation**: Download, extract, analyze, detect, alert pipeline with progress tracking
- **Smart downloads**: Uses actual FOMC meeting calendar (2008-2025) to minimize 404 errors
- **Resume capability**: Automatically skips previously downloaded documents
- **Historical context**: Links shifts to significance and policy implications
- **AI agent ready**: Comprehensive documentation and prompts for Claude Code automation

<img width="2139" height="1299" alt="image" src="https://github.com/user-attachments/assets/07ba7c00-ce98-44c8-adb2-2a7982e67d58" />


## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -m fedspeak --help
```

### 2. Download Documents

Download FOMC documents for a specific date range:

```bash
python3 -m fedspeak download --start-date 2021-01-01 --end-date 2022-03-01
```

### 3. Extract Text

Extract clean text from downloaded HTML files:

```bash
python3 -m fedspeak extract
```

### 4. Analyze for Shifts

Analyze the corpus and detect language shifts:

```bash
python3 -m fedspeak analyze
```

This will:
- Count keyword occurrences in all documents
- Detect emergence and removal patterns
- Generate alerts with historical context
- Create timeline visualizations

### 5. View Results

Alerts are saved in `results/alerts/`:
- JSON format: `ALERT-YYYYMMDD-{type}-{word}.json`
- Text format: `ALERT-YYYYMMDD-{type}-{word}.txt`
- Visualizations: `results/visualizations/{word}_timeline.png`

## AI Agent Integration

FedSpeak includes comprehensive documentation designed for autonomous operation with Claude Code:

### Documentation for AI Agents

- **AGENT_GUIDE.md**: Complete operational reference with protocols, state detection, and validation criteria. Designed for programmatic execution by AI agents.

- **RUNBOOK.md**: Step-by-step user guide with detailed command examples, troubleshooting, and common use cases.

- **prompts/**: Ready-to-use initialization prompts for fresh Claude Code instances:
  - `AGENT_PROMPT_COMPREHENSIVE.md`: Balanced, complete initialization (recommended)
  - `AGENT_PROMPT_QUICK.md`: Minimal fast-start for experienced agents
  - `AGENT_PROMPT_TASK_SPECIFIC.md`: Template for directed tasks with examples
  - `AGENT_PROMPT_DETAILED.md`: Maximum guidance with step-by-step validation

### Usage with Claude Code

To initialize a fresh Claude Code instance with FedSpeak:

```bash
# Copy one of the prompts from prompts/ directory
cat prompts/AGENT_PROMPT_COMPREHENSIVE.md

# Paste the contents to a fresh Claude Code session
# The agent will autonomously:
# 1. Read AGENT_GUIDE.md
# 2. Execute environment checks
# 3. Determine system state
# 4. Execute appropriate protocols
# 5. Validate results and report
```

The agent-optimized documentation enables autonomous execution of the complete pipeline, from environment validation through result verification, with minimal human intervention.

## Project Structure

```
FedSpeak/
├── config/
│   └── config.yaml           # Configuration (keywords, synonyms, detection parameters)
├── fedspeak/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── fetcher.py           # Document downloader with FOMC calendar
│   ├── fomc_calendar.py     # Real FOMC meeting dates (2008-2025)
│   ├── extractor.py         # Text extraction
│   ├── analyzer.py          # Keyword frequency tracking with synonym support
│   ├── detector.py          # Shift detection (emergence, removal)
│   ├── alerter.py           # Alert generation with visualizations
│   └── cli.py               # Command-line interface
├── data/
│   ├── raw/                 # Downloaded HTML/PDF documents
│   ├── processed/           # Extracted text files
│   └── metadata/            # Metrics and logs
├── results/
│   ├── alerts/              # Generated alerts (JSON, text)
│   └── visualizations/      # Timeline charts (PNG)
├── prompts/
│   ├── README.md            # Prompt selection guide
│   ├── AGENT_PROMPT_COMPREHENSIVE.md
│   ├── AGENT_PROMPT_QUICK.md
│   ├── AGENT_PROMPT_TASK_SPECIFIC.md
│   └── AGENT_PROMPT_DETAILED.md
├── tests/
│   └── test_*.py            # Test suite (68 tests)
├── AGENT_GUIDE.md           # AI agent operational reference
├── RUNBOOK.md               # Step-by-step user guide
└── requirements.txt         # Python dependencies
```

## Tracked Keywords

FedSpeak tracks 5 high-priority keywords from documented shifts. Each keyword can include synonym groups to track related terms together (e.g., "transitory" includes "transient" and "temporary"). Configure keywords and synonyms in `config/config.yaml`.

1. **transitory** (SHIFT-2021-01)
   - Emerged: April 2021
   - Removed: December 2021
   - Significance: Shift from temporary to persistent inflation framing

2. **accommodative** (SHIFT-2018-01)
   - Removed: September 2018
   - Significance: End of post-crisis accommodation policy

3. **patient** (SHIFT-2015-01)
   - Removed: March 2015
   - Significance: Signal that rate liftoff was imminent

4. **considerable time** (SHIFT-2014-01)
   - Substituted with "patient" in December 2014
   - Significance: Transition toward liftoff preparation

5. **full range of tools** (SHIFT-2020-01)
   - Added: March 2020
   - Significance: Signal of readiness for unconventional policy tools

## Configuration

Edit `config/config.yaml` to:
- Add/remove keywords to track
- Adjust detection parameters
- Configure output formats
- Set logging level

Key parameters:
- `sustained_removal_threshold: 3` - Consecutive zero counts to confirm removal
- `baseline_window_months: 6` - Historical window for baseline calculation
- `focus_document_type: policy_statement` - Primary document type for detection

## Architecture

FedSpeak uses a 6-module pipeline:

1. **DocumentFetcher**: Downloads FOMC documents from federalreserve.gov
   - Uses actual FOMC meeting calendar (2008-2025) from `fomc_calendar.py`
   - Eliminates approximately 80% of 404 errors by targeting real meeting dates
   - Retry logic with exponential backoff
   - Rate limiting (1-second delay)
   - Progress tracking with tqdm progress bars
   - Auto-resume capability (skips existing files)
   - Metadata tracking

2. **TextExtractor**: Extracts clean text from HTML/PDF
   - Version-aware parsing (2008-2012 vs 2013+ formats)
   - Boilerplate removal
   - Word count validation

3. **LanguageAnalyzer**: Counts keyword occurrences with synonym support
   - Regex whole-word matching (`\b{word}\b`)
   - Case-insensitive counting
   - Synonym group tracking (monitors related terms together)
   - Tracks individual synonyms + group totals
   - Time-series construction with group aggregation

4. **ShiftDetector**: Detects emergence and removal
   - Emergence: 0 → >0
   - Removal: >0 → 0 (sustained for 3+ documents)
   - Baseline calculation (6-month rolling window)

5. **AlertGenerator**: Formats alerts with context
   - Historical significance from keyword catalog
   - Evidence assembly (previous occurrences, timeline)
   - JSON and text output formats
   - Timeline visualizations (matplotlib)

6. **CLI**: User-friendly command-line interface
   - `download`, `extract`, `analyze`, `report` commands
   - Progress logging
   - Error handling

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

The project includes 68 tests with approximately 67% code coverage, covering all core modules (fetcher, extractor, analyzer, detector, alerter).

## Example: Detecting "Transitory" Shift

```bash
# Download 2021 documents
python3 -m fedspeak download --start-date 2021-04-01 --end-date 2022-03-01

# Extract text
python3 -m fedspeak extract

# Analyze for shifts
python3 -m fedspeak analyze

# View alert
cat results/alerts/ALERT-20211215-removal-transitory.txt
```

Expected output:
```
======================================================================
  FEDSPEAK LANGUAGE SHIFT DETECTED
======================================================================

Word: "transitory"
Shift Type: REMOVAL
Document: policy_statement - 2021-12-15
Confidence: HIGH

Change:
  1.0 → 0

Historical Significance:
  Fed used "transitory" to describe inflation surge from April-November 2021.
  Removal in December 2021 signaled shift from temporary to persistent
  inflation framing, indicating policy pivot toward rate increases.

Evidence:
  Previous occurrences: 8
    - 2021-09-22: count=1
    - 2021-11-03: count=1
  Sustained absence: Yes

Timeline: results/visualizations/transitory_timeline.png
======================================================================
```

## Documentation

### Primary Guides

- **RUNBOOK.md**: Complete step-by-step user guide with examples, troubleshooting, and common workflows
- **AGENT_GUIDE.md**: Operational reference for AI agents with protocols and validation criteria
- **prompts/**: Ready-to-use prompts for initializing Claude Code instances
- **config/config.yaml**: Configuration reference with inline documentation

### Implementation Details

- **Implementation Guide**: See `deliverables/implementation.md` for complete code documentation
- **Project Objective**: See `planning/00-objective.md`
- **Ground Truth Catalog**: See `deliverables/02-shifts.md`
- **Detection Methods**: See `deliverables/03-methods.md`
- **Architecture**: See `deliverables/architecture.md`

## Requirements

- Python 3.8+
- beautifulsoup4==4.12.2
- lxml==5.1.0
- pdfplumber==0.10.3
- pandas==2.1.4
- matplotlib==3.8.2
- requests==2.31.0
- pyyaml==6.0.1
- tqdm==4.66.1

## License

Academic Research - See LICENSE file for details.

## Author

FedSpeak v1.0 - November 2025
