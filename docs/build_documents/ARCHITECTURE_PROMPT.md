# FedSpeak - Architecture Document Prompt

## Context

FedSpeak is a validated, ready-to-implement project for detecting Federal Reserve language shifts. **Four deliverables are complete**: corpus analysis, ground truth catalog, detection feasibility, and requirements specification.

## Your Task

Create a comprehensive system architecture document for implementing FedSpeak based on completed exploratory work.

## Essential Reading (in order)

1. **PROJECT_STATUS.md** - Complete project summary and handoff (READ FIRST)
2. **deliverables/requirements.md** - 77 formal requirements to satisfy
3. **deliverables/03-methods.md** - Recommended approach (keyword frequency tracking)
4. **deliverables/02-shifts.md** - What to detect (11 documented shifts)
5. **deliverables/01-corpus.md** - Data sources and extraction methods

## Key Decisions Already Made

**Detection Method**: Simple keyword frequency tracking (100% test accuracy, 0-day lag)
**Corpus**: Fed documents 2008-present (~240 docs, 30 MB)
**Tech Stack**: Python 3.8+, BeautifulSoup, pdfplumber, pandas, matplotlib
**No ML needed**: Word counting sufficient for Fed language shifts
**Deployment**: Batch processing (8 meetings/year), CLI initially

## Architecture Document Structure

Create `/deliverables/architecture.md` with:

### 1. System Overview (10%)
- High-level architecture diagram
- Component interaction
- Data flow from Fed website → alerts → user
- Technology stack summary

### 2. Component Design (40%)

For each component, specify:
- **Inputs**: What it receives
- **Processing**: What it does
- **Outputs**: What it produces
- **Dependencies**: What it needs
- **Error handling**: How failures are managed

**Components to design**:

**2.1 Document Fetcher**
- Downloads FOMC statements/minutes from Fed URLs
- Implements retry logic, rate limiting (1 sec delay)
- Saves to `/data/raw/`
- Tracks metadata (URL, date, status, file size)

**2.2 Text Extractor**
- Parses HTML (BeautifulSoup) and PDF (pdfplumber)
- Version-aware content detection (2008-2012 vs. 2013+)
- Removes boilerplate, preserves policy sections
- Saves to `/data/processed/`

**2.3 Keyword Counter**
- Loads target words from config (11 from Document 02)
- Counts occurrences (case-insensitive, whole word regex)
- Stores time-series data (date, word, count)
- Builds historical baseline

**2.4 Shift Detector**
- Compares current count to baseline (6-month window)
- Detects emergence (0→>0) and removal (>0→0, sustained 3 docs)
- Applies thresholds from requirements
- Generates structured alerts

**2.5 Alert Manager**
- Formats alerts with context from Document 02 catalog
- Includes evidence (before/after counts, timeline)
- Outputs JSON + human-readable formats
- Links to source Fed documents

**2.6 Historical Analyzer**
- Batch processes full corpus (240 docs)
- Validates against known shifts
- Generates summary reports
- Creates timeline visualizations

**2.7 Configuration Manager**
- Loads config from YAML file
- Target keywords with contexts
- Detection thresholds
- File paths, URLs

**2.8 CLI Interface**
- Commands: download, extract, analyze, report
- Argument parsing
- Progress display
- Error reporting

### 3. Data Architecture (15%)

**3.1 File Structure**
```
/data/
  /raw/           # Downloaded HTML/PDF
  /processed/     # Extracted text files
  /metadata/      # Download/extraction status
  /results/       # Detection outputs
```

**3.2 Data Formats**
- Raw documents: HTML, PDF (original format)
- Extracted text: UTF-8 plain text
- Metadata: JSON
- Detection results: CSV
- Alerts: JSON + formatted text
- Config: YAML

**3.3 Schemas**
- Document metadata schema
- Alert JSON schema
- Detection results CSV columns
- Config file structure

### 4. Alert System Design (10%)
- Alert format specification (JSON schema from requirements)
- Alert confidence levels (high/medium/low)
- Context enrichment (Document 02 catalog lookup)
- Evidence packaging (counts, timeline, quotes)
- Delivery mechanism (file output initially, future: email/Slack)

### 5. Deployment Architecture (10%)
- **Runtime environment**: Python 3.8+ virtual environment
- **Scheduling**: Cron job or manual trigger
- **Installation**: pip install from requirements.txt
- **Configuration**: YAML file setup
- **Initialization**: Download historical corpus
- **Ongoing operation**: Check for new documents weekly

### 6. Testing Strategy (10%)
- **Unit tests**: Each component isolated
- **Integration tests**: Full pipeline (fetch → extract → detect → alert)
- **Validation tests**: Verify 100% accuracy on Document 03 test cases
  - "Transitory" emergence (Apr 2021)
  - "Transitory" removal (Dec 2021)
  - "Accommodative" removal (Sep 2018)
- **Performance tests**: <5 sec/doc, <15 min full corpus
- **Reliability tests**: Network failure, malformed documents

### 7. Error Handling & Logging (5%)
- **Error categories**: Network, parsing, detection, configuration
- **Retry strategies**: Exponential backoff for downloads
- **Logging levels**: DEBUG, INFO, WARNING, ERROR
- **Logging format**: Structured logs with timestamps
- **Error recovery**: Continue on failure, report at end

### 8. Code Organization (5%)
```
/fedspeak/
  /cli/          # Command-line interface
  /fetcher/      # Document download
  /extractor/    # Text extraction
  /detector/     # Shift detection
  /alerts/       # Alert generation
  /utils/        # Shared utilities
  /config/       # Configuration management

/scripts/        # Existing prototypes
/tests/          # Unit and integration tests
/docs/           # Documentation
```

### 9. Security & Compliance (3%)
- **Data privacy**: Public data only, no PII
- **API usage**: Respectful scraping (1 sec delay)
- **robots.txt**: Compliance verification
- **Rate limiting**: Request throttling
- **Error disclosure**: No sensitive data in logs

### 10. Future Extensibility (2%)
- **Plugin architecture**: Easy to add new document types
- **Config-driven detection**: Add keywords without code changes
- **Output adapters**: Support new alert formats
- **Analysis modules**: Historical reports, visualizations

## Requirements Traceability

For each component, reference which requirements it satisfies:
- Document Fetcher → REQ-DA-001 through REQ-DA-010
- Text Extractor → REQ-TP-001 through REQ-TP-007
- Shift Detector → REQ-SD-001 through REQ-SD-010
- Alert Manager → REQ-AG-001 through REQ-AG-008

See `/deliverables/requirements.md` for complete requirement list.

## Success Criteria for Architecture Document

Architecture is complete when:

1. ✓ Every component has clear inputs, processing, outputs
2. ✓ All 77 requirements are mapped to components
3. ✓ Data flow is fully specified (Fed website → user alerts)
4. ✓ File formats and schemas are defined
5. ✓ Error handling strategy covers all failure modes
6. ✓ Testing approach validates against Document 03 test cases
7. ✓ Deployment instructions are actionable
8. ✓ Implementation team can start coding from this document

## Reference Implementations

Working code to inform architecture:
- `/scripts/download_fed_docs.py` - Document fetcher prototype
- `/scripts/extract_and_analyze.py` - Text extractor prototype
- `/scripts/approach_1_keywords.py` - Detector prototype (100% accuracy)

Use these as reference for component design, but create **architecture**, not implementation details.

## What NOT to Include

- ❌ Actual code implementation (that's next phase)
- ❌ Step-by-step coding instructions
- ❌ Pseudocode (architecture describes "what", not "how")
- ❌ UI mockups (CLI is sufficient, specified in requirements)

## Deliverable Format

**File**: `/deliverables/architecture.md`

**Style**:
- Professional technical architecture document
- Diagrams using Mermaid or ASCII art
- Clear section headers
- Tables for structured information (schemas, mappings)
- Traceable to requirements document

**Length**: ~3000-5000 words (comprehensive but concise)

## Begin

1. Read PROJECT_STATUS.md thoroughly (contains all context)
2. Review requirements.md (what you're architecting for)
3. Study approach_1_keywords.py (how detection works in practice)
4. Create architecture.md following the structure above

Good luck! This is the bridge from research to implementation.
