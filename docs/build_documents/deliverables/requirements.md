# FedSpeak: Requirements Specification

**Version**: 1.0
**Date**: October 31, 2025
**Status**: Draft for Review

---

## 1. Introduction

### 1.1 Project Purpose

FedSpeak is a system for automatically detecting when the Federal Reserve changes how it describes economic conditions, policy actions, or forward guidance in its official communications. The system identifies semantic shifts, euphemism adoption, topic emergence/suppression, and narrative pivots before they become widely recognized, providing early signals of policy direction changes.

**Source**: `/planning/00-objective.md`

### 1.2 Scope

The system SHALL analyze Federal Reserve communications including:
- FOMC (Federal Open Market Committee) meeting minutes
- FOMC policy statements
- Press conference transcripts (future enhancement)
- Beige Book reports (future enhancement)

The system SHALL analyze historical documents from 2008 to present and monitor new publications going forward.

**Source**: Document 01 - Corpus availability analysis confirmed 2008+ data accessible

### 1.3 Target Users

The system is designed for:
- Financial analysts tracking Federal Reserve narrative management
- Institutional investors monitoring policy credibility signals
- Austrian economists and institutional skeptics
- Market participants requiring early warning of Fed communication shifts

Users need actionable signals before communication shifts become consensus observations.

**Source**: `/planning/00-objective.md`

### 1.4 Success Criteria

The system SHALL be considered successful when it:

1. **Detects known historical shifts**: Correctly identifies documented language changes from 2008-2023 including:
   - 2008 QE euphemism adoption
   - 2013 taper communication evolution
   - 2018 "accommodative" stance removal
   - 2021 "transitory" inflation narrative shift

2. **Flags new semantic patterns**: Detects language shifts within 1-2 meetings of their emergence (0-day lag target based on Document 03 testing)

3. **Maintains low false positive rate**: Does not alert on trivial word substitutions (<5% false positive rate based on Document 03 testing)

4. **Generates actionable signals**: Provides context and historical comparison for detected shifts

**Source**: `/planning/00-objective.md`, Document 03 - Detection testing validated 100% accuracy with 0-day lag

---

## 2. Functional Requirements

### 2.1 Data Acquisition

**REQ-DA-001**: The system SHALL download FOMC meeting minutes from `https://www.federalreserve.gov/monetarypolicy/fomcminutes[YYYYMMDD].htm`

**REQ-DA-002**: The system SHALL download FOMC policy statements from `https://www.federalreserve.gov/newsevents/pressreleases/monetary[YYYYMMDD]a.htm`

**REQ-DA-003**: The system SHALL extract text from HTML documents using the BeautifulSoup library with LXML parser

**Source**: Document 01, Section 2.1 - HTML extraction method validated

**REQ-DA-004**: The system SHALL extract text from PDF documents using the pdfplumber library

**Source**: Document 01, Section 2.2 - PDF extraction method validated

**REQ-DA-005**: The system SHALL handle Fed website format variations from 2008-present using version-aware content detection strategies

**Source**: Document 01, Section 4.4 - Format evolution timeline documented

**REQ-DA-006**: The system SHALL maintain a corpus of documents dating from January 2008 to present

**Rationale**: Pre-2008 documents return 404 errors with current URL patterns (Document 01, Section 5.1)

**REQ-DA-007**: The system SHOULD check for new FOMC documents within 24 hours of scheduled meeting dates

**Rationale**: FOMC statements published immediately after meetings; minutes published 3 weeks later

**REQ-DA-008**: The system SHALL include a 1-second delay between document download requests to respect server resources

**Source**: Document 01, Section 7.1 - Download script implementation

**REQ-DA-009**: The system SHALL save download metadata including URL, date, file size, and status for each document

**Source**: Document 01, Section 7.1 - Metadata tracking for corpus management

**REQ-DA-010**: The system SHALL retry failed downloads up to 3 times with exponential backoff

**Rationale**: Network resilience for production operation

### 2.2 Text Processing

**REQ-TP-001**: The system SHALL remove navigation elements including:
- Site breadcrumbs
- Social media links
- Header and footer boilerplate
- JavaScript and CSS code blocks

**Source**: Document 01, Section 2.1 - HTML extraction noise removal

**REQ-TP-002**: The system SHALL remove standard Fed disclaimers and legal boilerplate text

**Source**: Document 01, Section 4.1 - Structural analysis identified boilerplate patterns

**REQ-TP-003**: The system SHALL preserve complete text from the following sections:
- For FOMC minutes: "Committee Policy Action" section
- For policy statements: Entire statement body (paragraphs 1-5)

**Source**: Document 02, Section 4.2 - Policy statement structure analysis

**REQ-TP-004**: The system SHALL use cascading content detection strategies to extract main text:
1. First attempt: `<div id="article">` (modern format 2013+)
2. Fallback: `<div id="leftText">` (legacy format 2008-2012)
3. Final fallback: `<body>` tag

**Source**: Document 01, Section 2.1 - Version-aware extraction code

**REQ-TP-005**: The system SHALL normalize whitespace by:
- Replacing multiple newlines with double newline
- Replacing multiple spaces with single space
- Stripping leading/trailing whitespace

**Source**: Document 01, Section 2.1 - Text cleaning implementation

**REQ-TP-006**: The system SHALL save extracted text in plain UTF-8 encoded files with `.txt` extension

**Source**: Document 01, Section 7.2 - Extraction output format

**REQ-TP-007**: The system SHOULD NOT remove section headings as they provide structural context

**Rationale**: Headings like "Committee Policy Action" help identify policy-relevant sections

### 2.3 Language Shift Detection

**REQ-SD-001**: The system SHALL implement keyword frequency tracking as the primary detection method

**Source**: Document 03, Section 5.1 - Approach 1 recommended based on 100% test accuracy

**REQ-SD-002**: The system SHALL track occurrences of the following target words from the Document 02 catalog:

| Keyword | Shift Type | Context | Document 02 Reference |
|---------|------------|---------|----------------------|
| "transitory" | Deletion | Inflation narrative | SHIFT-2021-01 |
| "accommodative" | Deletion | Policy stance | SHIFT-2018-01 |
| "patient" | Deletion | Forward guidance | SHIFT-2015-01 |
| "considerable time" | Substitution | Forward guidance | SHIFT-2014-01 |
| "full range of tools" | Addition | Crisis response | SHIFT-2020-01 |

**Source**: Document 02, Section 1 - Complete shift catalog table

**REQ-SD-003**: The system SHALL count word occurrences using case-insensitive whole-word matching (regex `\b{word}\b`)

**Source**: Document 03, Section 2.1 - Implementation details

**REQ-SD-004**: The system SHALL detect **emergence** when:
- Previous count = 0
- Current count > 0
- Condition: First occurrence in time-ordered corpus

**Source**: Document 03, Section 2.1 - Detection algorithm

**REQ-SD-005**: The system SHALL detect **removal** when:
- Previous count > 0
- Current count = 0
- Sustained condition: Count remains 0 for 3 consecutive documents

**Rationale**: Prevents false alerts from single-document absences

**Source**: Document 03, Section 6.1 - Alert logic with sustained removal threshold

**REQ-SD-006**: The system SHALL compare each new document to a historical baseline calculated from the previous 6 months of documents

**Source**: Document 03, Section 6.1 - Baseline calculation approach

**REQ-SD-007**: The system SHALL focus primary detection on **policy statements** rather than minutes

**Rationale**: Statements show clearest shift signals; minutes lag by 3 weeks and include historical discussion

**Source**: Document 02, Section 5 - Document type analysis; Document 03, Section 1.3 - Ground truth verification

**REQ-SD-008**: The system SHOULD track both single words and multi-word phrases (e.g., "transitory factors", "full range of tools")

**Source**: Document 03, Section 5.2 - Backup recommendation for phrase tracking

**REQ-SD-009**: The system MUST NOT flag changes in:
- Economic condition descriptions (e.g., "housing market strengthened" vs. "weakened")
- Attendance lists and voting records
- Administrative procedural text

**Rationale**: These vary naturally with economic conditions and are not policy language shifts

**Source**: Document 02, Section 8 - False positives to avoid

**REQ-SD-010**: The system SHALL log detection decisions including:
- Word checked
- Current count
- Previous count (baseline)
- Date
- Shift type (emergence/removal/none)
- Alert generated (yes/no)

**Rationale**: Audit trail for reviewing false positives and system accuracy

### 2.4 Alert Generation

**REQ-AG-001**: The system SHALL generate alerts when a shift is detected per REQ-SD-004 or REQ-SD-005

**REQ-AG-002**: Alerts MUST include the following elements:
- Shift type (emergence or removal)
- Target word or phrase
- Document date and type
- Count change (e.g., "0 → 1" or "1 → 0")
- Shift context from Document 02 catalog
- URL link to source Fed document

**Source**: Document 03, Section 6.3 - User presentation format

**REQ-AG-003**: Alerts SHALL include historical significance explanation when available from Document 02 catalog

Example:
```
Historical Significance: Fed used "transitory" to describe inflation surge.
Removal signals shift from temporary to persistent inflation framing.
```

**Source**: Document 03, Section 6.3 - Alert format example

**REQ-AG-004**: The system SHALL provide a "View Historical Usage" option showing:
- Timeline chart of word frequency over past 12 months
- List of all documents where word appeared
- Dates of previous shifts for same word

**REQ-AG-005**: The system SHALL NOT generate alerts for:
- Words appearing in procedural sections (attendance, voting records)
- One-time mentions that do not recur in subsequent documents
- Words below minimum frequency threshold (single occurrence in isolation)

**REQ-AG-006**: Alerts SHALL be output in structured JSON format for programmatic consumption

**REQ-AG-007**: Alerts SHOULD be human-readable when displayed in plain text format

**REQ-AG-008**: The system SHALL rate alert confidence as:
- **High**: Matches known pattern from Document 02 catalog exactly
- **Medium**: New word following known pattern (e.g., similar to documented shift)
- **Low**: Uncertain pattern requiring manual review

### 2.5 Historical Analysis

**REQ-HA-001**: The system SHALL analyze the complete corpus of FOMC statements and minutes from January 2008 to present

**Source**: Document 01, Section 6.1 - Recommended corpus scope

**REQ-HA-002**: The system SHALL correctly identify the following test case shifts when run on historical corpus:

| Shift | Expected Detection Date | Document 02 ID |
|-------|------------------------|----------------|
| "Transitory" emergence | April 28, 2021 | SHIFT-2021-01 |
| "Transitory" removal | December 15, 2021 | SHIFT-2021-01 |
| "Accommodative" removal | September 26, 2018 | SHIFT-2018-01 |

**Source**: Document 03, Section 1.3 - Ground truth verification

**REQ-HA-003**: The system SHALL generate a historical report summarizing:
- All detected shifts in corpus
- Timeline visualization of keyword frequencies
- Shift clustering analysis (periods of high shift activity)

**REQ-HA-004**: The system SHALL support re-running detection on the full historical corpus with updated parameters

**Rationale**: Allows tuning thresholds and adding new keywords without losing historical analysis

**REQ-HA-005**: The system SHOULD identify previously undocumented shifts for manual review

**Approach**: Flag documents with unusual word frequency patterns as candidates

**Source**: Document 03, Section 7.5 - Future hybrid approach consideration

---

## 3. Non-Functional Requirements

### 3.1 Performance

**REQ-PERF-001**: Document processing SHALL complete within 5 seconds per document

**Source**: Document 03, Section 5.1 - Expected production performance

**REQ-PERF-002**: The system SHALL process the full historical corpus (240 documents, 2008-2023) in under 15 minutes

**Calculation**: 240 docs × 5 sec = 20 minutes maximum; target 15 minutes

**Source**: Document 01, Section 5.4 - Full corpus estimates

**REQ-PERF-003**: Alert generation SHALL have latency of less than 1 minute after new document becomes available

**Source**: Document 03, Section 8.1 - Performance requirements

**REQ-PERF-004**: Text extraction from HTML SHALL complete in under 0.5 seconds per document

**Source**: Document 01, Section 5.4 - Observed performance

**REQ-PERF-005**: Text extraction from PDF SHALL complete in under 1 second per document

**Source**: Document 01, Section 5.4 - Observed performance

**REQ-PERF-006**: The system SHALL support concurrent processing of multiple documents

**Rationale**: Batch processing of historical corpus or catching up after downtime

### 3.2 Reliability

**REQ-REL-001**: The system SHALL handle network failures gracefully by:
- Catching and logging HTTP exceptions
- Retrying with exponential backoff (1s, 2s, 4s delays)
- Continuing to next document after 3 failed attempts
- Reporting failed downloads for manual review

**Source**: Document 01, Section 7.1 - Download script error handling

**REQ-REL-002**: The system MUST validate extracted text for completeness by checking:
- Minimum word count threshold (>100 words for statements, >1000 for minutes)
- Presence of expected section markers
- No extraction errors logged

**Rationale**: Prevents analysis of malformed or incomplete extractions

**REQ-REL-003**: The system SHALL save extraction metadata including:
- Extraction timestamp
- Word count
- Success/failure status
- Error messages if applicable

**Source**: Document 01, Section 7.2 - Extraction output format

**REQ-REL-004**: The system SHALL continue operating if individual document processing fails

**Behavior**: Log error, skip document, continue with next in queue

**REQ-REL-005**: The system SHALL maintain data integrity by:
- Atomic file writes (write to temp, then rename)
- Validation before overwriting existing extractions
- Backup of corpus metadata

### 3.3 Accuracy

**REQ-ACC-001**: The system SHALL achieve a detection rate of at least 95% for shifts in the Document 02 catalog

**Target**: 100% based on Document 03 testing; 95% minimum acceptable

**Source**: Document 03, Section 2.4 - Test results showed 100% detection

**REQ-ACC-002**: False positive rate MUST NOT exceed 5% of total alerts generated

**Source**: Document 03, Section 5.1 - Expected production performance

**REQ-ACC-003**: Detection lag SHALL NOT exceed 0 days (shift detected in same document it occurs)

**Source**: Document 03, Section 2.4 - Achieved 0-day lag in testing

**REQ-ACC-004**: The system SHALL distinguish between sustained shifts and single-document variations

**Implementation**: Require 3 consecutive documents to confirm removal (REQ-SD-005)

**REQ-ACC-005**: Precision (true positives / total alerts) SHALL be at least 95%

**REQ-ACC-006**: Recall (detected shifts / actual shifts) SHALL be at least 95%

**Source**: Document 03, Section 2.4 - Metrics framework

### 3.4 Maintainability

**REQ-MAINT-001**: Code SHALL be written in Python 3.8 or higher

**REQ-MAINT-002**: The system SHALL use only the following dependencies:
- `beautifulsoup4` (HTML parsing)
- `lxml` (HTML parser backend)
- `pdfplumber` (PDF extraction)
- `pandas` (data handling)
- `matplotlib` (visualization)
- Standard library modules (`re`, `json`, `pathlib`, `datetime`)

**Source**: Document 01, Section 7.3 - Reusable code dependencies; Document 03, Section 2.2 - Implementation libraries

**REQ-MAINT-003**: All dependencies MUST be documented in `requirements.txt` with version pins

**REQ-MAINT-004**: Configuration MUST be externalized to a separate config file (YAML or JSON format)

**Parameters to externalize**:
- Target keywords and their contexts
- Detection thresholds (sustained removal = 3 docs)
- Document URLs and patterns
- File paths for corpus storage

**REQ-MAINT-005**: The system SHALL provide command-line interface with the following operations:
- `download`: Fetch new documents
- `extract`: Extract text from downloaded documents
- `analyze`: Run shift detection
- `report`: Generate summary report

**REQ-MAINT-006**: Code SHALL follow PEP 8 style guidelines

**REQ-MAINT-007**: Functions SHALL include docstrings explaining purpose, parameters, and return values

**REQ-MAINT-008**: The system SHALL include unit tests for:
- Text extraction functions
- Word counting logic
- Shift detection rules
- Alert generation

**Coverage target**: 80% code coverage minimum

### 3.5 Usability

**REQ-USE-001**: Alerts SHALL be human-readable with clear explanations

Example:
```
LANGUAGE SHIFT DETECTED

Word: "transitory"
Shift Type: Removal
Document: FOMC Statement, December 15, 2021

Change: Word was present in 8 previous statements (April-November 2021)
        Now absent from December statement

Context: Inflation narrative
```

**Source**: Document 03, Section 6.3 - User presentation

**REQ-USE-002**: The system SHALL provide evidence for why each alert fired, including:
- Exact word counts (before and after)
- List of documents where word appeared previously
- Timeline visualization

**REQ-USE-003**: Historical context MUST be included with alerts using information from Document 02 catalog

**REQ-USE-004**: The system SHALL provide a summary dashboard showing:
- Total documents in corpus
- Number of shifts detected
- Timeline of shifts
- Alert history

**REQ-USE-005**: Visualizations SHALL use clear date formatting (e.g., "Dec 2021" not "20211215")

**REQ-USE-006**: Error messages SHALL be actionable, indicating what went wrong and how to fix it

Example: "Failed to download [URL]: 404 Not Found. Document may not exist. Check date format."

**REQ-USE-007**: The system SHOULD provide progress indicators for long-running operations

Example: "Processing document 45 of 240..." with progress bar

---

## 4. Data Requirements

### 4.1 Data Sources

**REQ-DATA-001**: The system SHALL use the following primary data sources:

| Document Type | URL Pattern | Format | Availability |
|---------------|-------------|--------|--------------|
| FOMC Minutes | `https://www.federalreserve.gov/monetarypolicy/fomcminutes[YYYYMMDD].htm` | HTML | 2008-present |
| Policy Statements | `https://www.federalreserve.gov/newsevents/pressreleases/monetary[YYYYMMDD]a.htm` | HTML | 2008-present |

**Source**: Document 01, Section 2 - Document inventory

**REQ-DATA-002**: The system SHALL NOT require API keys or authentication

**Rationale**: Fed documents are publicly accessible

**REQ-DATA-003**: The system SHALL handle both HTML and PDF formats

**Formats**:
- HTML: Primary format for statements and minutes (2008+)
- PDF: Legacy format and press transcripts

**Source**: Document 01, Section 2.1-2.2 - Extraction results

### 4.2 Data Storage

**REQ-DATA-004**: The system SHALL store raw downloaded documents in `/data/raw/` directory

**File naming convention**: `{doc_type}_{YYYYMMDD}.{ext}`

Example: `policy_statement_20211215.html`

**Source**: Document 01, Section 7.1 - Download script implementation

**REQ-DATA-005**: The system SHALL store extracted text in `/data/processed/` directory

**File naming convention**: `{doc_type}_{YYYYMMDD}.txt`

**REQ-DATA-006**: The system SHALL store corpus metadata in JSON format including:
```json
{
  "doc_type": "policy_statement",
  "date": "20211215",
  "url": "https://...",
  "download_status": "success",
  "extraction_status": "success",
  "word_count": 495,
  "detected_shifts": ["transitory_removal"]
}
```

**Source**: Document 01, Section 7.1 - Metadata format

**REQ-DATA-007**: The system SHALL store detection results in CSV format with columns:
- date
- doc_type
- word
- count
- shift_type
- alert_generated

**Source**: Document 03, Section 2.3 - Results storage format

### 4.3 Data Retention

**REQ-DATA-008**: The system SHALL retain all downloaded raw documents indefinitely

**Rationale**: Historical corpus for re-analysis with updated methods

**REQ-DATA-009**: The system SHALL retain extraction results for at least 2 years

**REQ-DATA-010**: The system SHALL archive detection logs for at least 1 year

### 4.4 Data Volume

**REQ-DATA-011**: The system SHALL support a corpus of at least 240 documents

**Calculation**: 8 FOMC meetings/year × 15 years (2008-2023) × 2 doc types (statements + minutes)

**Source**: Document 01, Section 5.4 - Full corpus estimates

**REQ-DATA-012**: Estimated storage requirements:

| Data Type | Volume per Document | Total (240 docs) |
|-----------|---------------------|------------------|
| Raw HTML | ~80-150 KB | ~25 MB |
| Extracted Text | ~5-10 KB | ~2 MB |
| Metadata | ~1 KB | ~0.3 MB |
| **Total** | | **~30 MB** |

**Source**: Document 01, Section 5.4 - File sizes observed during testing

---

## 5. Interface Requirements

### 5.1 Input Interfaces

**REQ-INT-001**: The system SHALL accept configuration via YAML file with the following structure:

```yaml
keywords:
  - word: "transitory"
    type: "deletion"
    context: "inflation narrative"
    shift_id: "SHIFT-2021-01"

  - word: "accommodative"
    type: "deletion"
    context: "policy stance"
    shift_id: "SHIFT-2018-01"

detection:
  sustained_removal_threshold: 3
  baseline_window_months: 6
  focus_document_type: "policy_statement"

corpus:
  start_date: "2008-01-01"
  data_dir: "data/"
  output_dir: "results/"

download:
  delay_seconds: 1
  retry_attempts: 3
  timeout_seconds: 30
```

**REQ-INT-002**: The system SHALL provide command-line interface accepting the following arguments:

```bash
fedspeak download --start-date YYYY-MM-DD --end-date YYYY-MM-DD
fedspeak extract [--doc-type TYPE]
fedspeak analyze [--config CONFIG_FILE]
fedspeak report [--format json|html|text]
```

**REQ-INT-003**: The system SHALL validate configuration file on startup and report errors with specific field names

### 5.2 Output Interfaces

**REQ-INT-004**: The system SHALL output alerts in JSON format:

```json
{
  "alert_id": "ALERT-20211215-001",
  "timestamp": "2021-12-15T14:30:00Z",
  "shift_type": "removal",
  "word": "transitory",
  "document": {
    "type": "policy_statement",
    "date": "2021-12-15",
    "url": "https://..."
  },
  "change": {
    "previous_count": 1,
    "current_count": 0,
    "baseline_avg": 1.0
  },
  "context": {
    "category": "inflation narrative",
    "shift_id": "SHIFT-2021-01",
    "significance": "Fed abandonment of 'transitory' framing..."
  },
  "confidence": "high"
}
```

**REQ-INT-005**: The system SHALL write log files in structured format with levels: DEBUG, INFO, WARNING, ERROR

**REQ-INT-006**: The system SHALL generate corpus summary reports including:
- Total documents processed
- Date range covered
- Number of shifts detected by type
- Alert history timeline

**Format options**: HTML dashboard, JSON data, CSV table

**REQ-INT-007**: The system SHALL generate timeline visualizations in PNG format showing:
- Word frequency over time
- Detected shift markers
- Baseline trends

**Source**: Document 03, Section 2.3 - Visualization outputs

---

## 6. Constraints

**REQ-CONST-001**: The system MUST use only publicly available data from federalreserve.gov

**Rationale**: No proprietary data sources, reproducible by any user

**REQ-CONST-002**: The system SHALL NOT require authentication, API keys, or special access

**REQ-CONST-003**: The system MUST respect `robots.txt` directives from federalreserve.gov

**REQ-CONST-004**: The system SHALL include a 1-second delay between download requests per REQ-DA-008

**Rationale**: Respectful server usage, avoid rate limiting

**REQ-CONST-005**: The system SHALL NOT scrape real-time or intra-meeting data

**Scope**: Post-meeting publications only (statements and minutes)

**Source**: `/planning/00-objective.md` - Non-goals

**REQ-CONST-006**: The system SHALL run in batch processing mode, not real-time streaming

**Rationale**: FOMC publishes documents 8 times per year on predictable schedule

**REQ-CONST-007**: The system MUST operate in Python 3.8+ environment

**REQ-CONST-008**: The system SHALL require no more than 2 GB RAM for normal operation

**REQ-CONST-009**: The system SHALL require no more than 100 MB disk space for code and dependencies (excluding corpus data)

---

## 7. Assumptions and Dependencies

### 7.1 Assumptions

**ASSUME-001**: The Federal Reserve will continue publishing FOMC statements and minutes in HTML format accessible at current URL patterns

**ASSUME-002**: Fed document structure (headers, sections, content organization) will remain reasonably stable or evolve gradually

**Mitigation**: Version-aware extraction per REQ-TP-004

**ASSUME-003**: Python 3.8+ runtime environment is available on deployment platform

**ASSUME-004**: Network connectivity to federalreserve.gov is available with reasonable reliability (>99% uptime)

**ASSUME-005**: Fed website will not implement aggressive anti-scraping measures (CAPTCHA, IP blocking) for reasonable request rates

**Rationale**: Current 1-second delay is respectful; Fed data is public

**ASSUME-006**: Disk space for corpus storage (~30 MB initially, growing ~2 MB/year) is available

**ASSUME-007**: Language shifts will continue to follow patterns documented in Document 02 (additions, deletions, substitutions)

**Risk**: If Fed adopts entirely new communication strategy, detection may require method updates

### 7.2 Dependencies

**DEP-001**: External Libraries

| Library | Purpose | Version | License |
|---------|---------|---------|---------|
| beautifulsoup4 | HTML parsing | >=4.12.0 | MIT |
| lxml | Parser backend | >=5.0.0 | BSD |
| pdfplumber | PDF extraction | >=0.10.0 | MIT |
| pandas | Data handling | >=2.1.0 | BSD |
| matplotlib | Visualization | >=3.8.0 | PSF |

**Source**: `/requirements.txt`, Document 01 Section 7.3

**DEP-002**: Python Standard Library Modules
- `re` - Regular expressions for word matching
- `json` - Configuration and output formatting
- `pathlib` - File path handling
- `datetime` - Date parsing and formatting
- `requests` - HTTP downloads

**DEP-003**: External Services
- federalreserve.gov website (HTTP/HTTPS access)
- DNS resolution for domain lookup
- Internet connectivity

**DEP-004**: System Requirements
- Python 3.8 or higher interpreter
- pip package manager
- 2 GB RAM minimum
- 100 MB disk space (code + deps)
- 50 MB disk space (corpus storage, grows over time)

---

## 8. Out of Scope

The following are explicitly **NOT** in scope for this system:

**OUT-001**: Real-time monitoring or intra-meeting analysis

**Rationale**: Fed publishes post-meeting; no real-time data available

**Source**: `/planning/00-objective.md` - Non-goals

**OUT-002**: Sentiment analysis or emotional tone detection

**Rationale**: Focus is on word/phrase changes, not sentiment shifts

**OUT-003**: Prediction of future policy actions or market reactions

**Rationale**: System detects language changes, does not predict outcomes

**OUT-004**: Analysis of non-Federal Reserve communications

**Scope**: Fed documents only, not ECB, BOE, BOJ, or other central banks

**Source**: `/planning/00-objective.md` - Project scope

**OUT-005**: Analysis of Fed speeches or testimonies (beyond FOMC statements/minutes)

**Rationale**: Document 01 focused corpus analysis on statements and minutes

**Note**: May be added in future enhancement

**OUT-006**: Natural language generation or automated commentary

**Rationale**: System provides alerts with context; humans interpret significance

**OUT-007**: Integration with trading systems or automated trading decisions

**Rationale**: Analytical tool for humans, not trading automation

**OUT-008**: Historical document OCR or scanned PDF processing

**Rationale**: Focus on digital-native documents from 2008+ with text layers

**OUT-009**: Multi-language support

**Rationale**: Fed documents are in English only

**OUT-010**: Advanced NLP methods (TF-IDF, embeddings, topic modeling)

**Rationale**: Document 03 testing showed simple keyword tracking sufficient

**Note**: May be reconsidered if keyword tracking proves inadequate in production

**Source**: Document 03, Section 5.3 - Rejected approaches

---

## 9. Success Criteria

The system SHALL be considered successfully implemented when:

### 9.1 Functional Success

**SUCCESS-001**: The system correctly detects **at least 10 of 11** documented shifts from Document 02 catalog when run on historical corpus (2008-2023)

**Target shifts** (Document 02, Section 1):
- ✓ SHIFT-2021-01: "Transitory" emergence and removal
- ✓ SHIFT-2020-01: "Full range of tools" addition
- ✓ SHIFT-2018-01: "Accommodative" removal
- ✓ SHIFT-2015-01: "Patient" removal
- ✓ SHIFT-2014-01: "Considerable time" → "Patient"
- ✓ SHIFT-2013-02: Taper decision language
- ✓ SHIFT-2013-01: Taper signal language
- ✓ SHIFT-2012-01: State-contingent guidance
- ✓ SHIFT-2010-01: QE2 language
- ✓ SHIFT-2008-01: ZIRP range language

**Acceptance**: 10/11 = 91% detection rate (target: 95% per REQ-ACC-001)

**SUCCESS-002**: False positive rate below 5% across full historical corpus

**Measurement**: (False alerts / Total alerts) < 0.05

**SUCCESS-003**: The system processes the full 2008-2023 corpus (240 documents) in under 20 minutes

**Target**: 15 minutes per REQ-PERF-002

**SUCCESS-004**: The system runs without manual intervention for:
- Downloading new documents when available
- Extracting text
- Detecting shifts
- Generating alerts

**Test**: Schedule automated run for 1 month, verify <5% failure rate

### 9.2 Accuracy Success

**SUCCESS-005**: Test cases from Document 03 are correctly detected:

| Test Case | Expected Detection | Lag Tolerance |
|-----------|-------------------|---------------|
| "Transitory" emergence (Apr 2021) | Detected in April 2021 statement | 0 days |
| "Transitory" removal (Dec 2021) | Detected in Dec 2021 statement | 0 days |
| "Accommodative" removal (Sep 2018) | Detected in Sep 2018 statement | 0 days |

**Acceptance**: 3/3 test cases = 100%

**Source**: Document 03, Section 1.3 - Ground truth verification

**SUCCESS-006**: Detection precision ≥ 95% and recall ≥ 95%

**Formulas**:
- Precision = True Positives / (True Positives + False Positives)
- Recall = True Positives / (True Positives + False Negatives)

**Source**: Document 03, Section 3.3 - Accuracy requirements

### 9.3 Usability Success

**SUCCESS-007**: Users can understand why alerts fired without consulting documentation

**Test**: Show alert to Fed watchers unfamiliar with system; ask them to explain what changed

**Acceptance**: 90% can correctly identify the shift

**SUCCESS-008**: Users can investigate alert history and view timeline visualizations

**Test**: User can answer "When did the Fed start using 'transitory'?" using system interface

**SUCCESS-009**: System generates actionable insights per original objective

**Test**: Users report alerts provide early warning of policy direction changes before consensus observations

**Source**: `/planning/00-objective.md` - Success criteria

### 9.4 Reliability Success

**SUCCESS-010**: System handles network failures gracefully

**Test**: Simulate network outage during download; verify system retries and continues

**SUCCESS-011**: System recovers from interrupted processing

**Test**: Kill process mid-extraction; verify restart continues from last checkpoint

**SUCCESS-012**: System validates extracted text for completeness

**Test**: Inject malformed HTML; verify system detects and reports extraction failure

---

## 10. Future Enhancements

The following features are **potential** but NOT required for initial release:

### 10.1 Planned Enhancements (High Priority)

**FUTURE-001**: Press conference transcript analysis

**Rationale**: Document 01 confirmed PDF transcripts are available and extractable

**Benefit**: Q&A provides unscripted elaboration on policy language

**FUTURE-002**: Beige Book analysis

**Rationale**: Document 01 identified Beige Books as available but lower signal

**Benefit**: Economic assessment shifts complement policy language shifts

**FUTURE-003**: Synonym and phrase expansion

**Implementation**: Track related terms ("transitory", "temporary", "transient")

**Rationale**: Document 03, Section 7.2 - Identified as refinement need

**FUTURE-004**: Adaptive baseline calculation

**Current**: Fixed 6-month window

**Enhancement**: Detect changes relative to historical average with statistical significance (>2 std dev)

**Rationale**: Document 03, Section 7.2 - Refinement suggestion

### 10.2 Research Enhancements (Medium Priority)

**FUTURE-005**: Hybrid detection approach

**Method**: Keyword tracking (99% of cases) + semantic similarity (outlier detection for novel shifts)

**Rationale**: Document 03, Section 7.5 - Hybrid approach consideration

**FUTURE-006**: TF-IDF discovery mode

**Use case**: Quarterly corpus scan to identify candidate shifts for manual review

**Rationale**: Document 03, Section 3.1 - TF-IDF for discovery (not monitoring)

**FUTURE-007**: N-gram phrase tracking

**Enhancement**: Extend keyword tracking to multi-word patterns

**Rationale**: Document 03, Section 5.2 - Backup recommendation

### 10.3 Integration Enhancements (Low Priority)

**FUTURE-008**: API endpoint for programmatic access

**Use case**: Third-party tools query FedSpeak for shift data

**FUTURE-009**: Web dashboard

**Current**: Command-line reports

**Enhancement**: Interactive web UI for exploring corpus and alerts

**FUTURE-010**: Email/Slack alert delivery

**Current**: JSON output and log files

**Enhancement**: Push notifications to users

**FUTURE-011**: Historical Fed transcript analysis

**Scope**: Minutes from 1990s-2000s if they become accessible

**Rationale**: Document 01 identified pre-2008 404 errors but noted potential archive sources (FRASER)

### 10.4 Analysis Enhancements (Low Priority)

**FUTURE-012**: Shift clustering analysis

**Method**: Identify periods of high shift activity (e.g., multiple shifts in 2013 taper era)

**Benefit**: Detect regime changes beyond single-word shifts

**FUTURE-013**: Speaker attribution in transcripts

**Method**: Track which Fed officials use specific language in Q&A

**Benefit**: Identify if language originates with Chair vs. distributed across speakers

**FUTURE-014**: Correlation with market reactions

**Method**: Link detected shifts to bond yield changes, equity moves

**Scope**: Analytical research, not real-time trading

---

## Appendix A: Traceability Matrix

| Requirement ID | Source Document | Section | Validated By |
|----------------|-----------------|---------|--------------|
| REQ-DA-001 to REQ-DA-010 | Document 01 | 2.1, 7.1 | Corpus download tested |
| REQ-TP-001 to REQ-TP-007 | Document 01 | 2.1, 4.1 | Extraction tested |
| REQ-SD-001 to REQ-SD-010 | Document 02, Document 03 | Various | Detection tested |
| REQ-AG-001 to REQ-AG-008 | Document 03 | 6.3 | Alert format defined |
| REQ-HA-001 to REQ-HA-005 | Document 01, Document 03 | Various | Historical analysis |
| REQ-PERF-001 to REQ-PERF-006 | Document 03 | 5.1, 8.1 | Performance tested |
| REQ-ACC-001 to REQ-ACC-006 | Document 03 | 2.4, 3.3 | Test cases validated |

---

## Appendix B: RFC 2119 Keywords

This specification uses RFC 2119 keywords with the following meanings:

- **MUST / SHALL**: Absolute requirement
- **MUST NOT / SHALL NOT**: Absolute prohibition
- **SHOULD**: Recommended but not absolute
- **SHOULD NOT**: Not recommended but not prohibited
- **MAY**: Optional, truly discretionary

---

## Appendix C: Document References

- `/planning/00-objective.md`: Original project objective and scope
- `/deliverables/01-corpus.md`: Corpus analysis - data availability and extraction methods
- `/deliverables/02-shifts.md`: Ground truth catalog - documented language shifts
- `/deliverables/03-methods.md`: Detection feasibility - tested approaches and recommendations
- `/requirements.txt`: Python dependencies
- `/scripts/download_fed_docs.py`: Document download implementation
- `/scripts/extract_and_analyze.py`: Text extraction implementation
- `/scripts/approach_1_keywords.py`: Keyword detection implementation

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-31 | FedSpeak Project | Initial requirements specification |

**Approval**

This requirements specification is ready for review and approval by project stakeholders.

**Next Steps**:
1. Review and approve requirements
2. Create architecture specification
3. Begin implementation planning
4. Set up development environment

---

*End of Requirements Specification*
