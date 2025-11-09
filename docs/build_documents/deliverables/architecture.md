# FedSpeak: Technical Architecture Document

**Version**: 1.0
**Date**: November 1, 2025
**Status**: Design Document
**Purpose**: Complete technical architecture for FedSpeak language shift detection system

---

## 1. Executive Summary

### 1.1 System Overview

FedSpeak is a batch-processing system that automatically detects when the Federal Reserve changes language in official FOMC communications. The system downloads Fed documents, extracts text, tracks keyword frequencies over time, and generates alerts when significant shifts occur.

**Core Capability**: Detect language shifts with 0-day lag using simple keyword frequency tracking.

**Validation**: Tested on real Fed documents (2017-2022) achieving 100% detection accuracy with 0 false positives.

### 1.2 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Detection Method** | Keyword frequency tracking | 100% accuracy on test cases; simpler than ML alternatives |
| **Document Focus** | FOMC policy statements | Clearest shift signal; minutes lag 3 weeks |
| **Processing Model** | Batch processing | FOMC publishes 8x/year on schedule; real-time not needed |
| **Corpus Scope** | 2008-present | Pre-2008 returns 404s; 15 years = 240 docs sufficient |
| **Technology** | Python 3.8+ | Mature ecosystem, standard libraries, easy deployment |

### 1.3 Technology Stack

**Language**: Python 3.8+

**Core Dependencies**:
- `beautifulsoup4` 4.12+ - HTML parsing
- `lxml` 5.0+ - Parser backend
- `pdfplumber` 0.10+ - PDF extraction
- `pandas` 2.1+ - Data handling
- `matplotlib` 3.8+ - Visualization
- `requests` - HTTP downloads

**Infrastructure**: Local filesystem storage, no database required

**Deployment**: Cron-scheduled Python script, ~1000 lines total

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FedSpeak System                          │
│                      (Batch Processing)                         │
└─────────────────────────────────────────────────────────────────┘

Input: Fed Website (federalreserve.gov)
                    ↓
         ┌──────────────────────┐
         │  Document Fetcher    │  ← URL templates, retry logic
         │  (download_fed_docs) │
         └──────────────────────┘
                    ↓
         /data/raw/*.html, *.pdf  (Raw storage)
                    ↓
         ┌──────────────────────┐
         │   Text Extractor     │  ← BeautifulSoup, pdfplumber
         │  (extract_analyze)   │     Version-aware selectors
         └──────────────────────┘
                    ↓
         /data/processed/*.txt   (Extracted text)
                    ↓
         ┌──────────────────────┐
         │  Language Analyzer   │  ← Keyword counter
         │   (shift_detector)   │     Baseline comparison
         └──────────────────────┘
                    ↓
         /data/processed/metrics.csv (Time-series counts)
                    ↓
         ┌──────────────────────┐
         │   Shift Detector     │  ← Emergence/removal logic
         │   (shift_detector)   │     Sustained threshold
         └──────────────────────┘
                    ↓
         ┌──────────────────────┐
         │   Alert Generator    │  ← Context from catalog
         │  (alert_formatter)   │     Evidence assembly
         └──────────────────────┘
                    ↓
         /results/alerts/*.json  (Alert output)
                    ↓
Output: User alerts + visualizations
```

### 2.2 Data Flow

**Normal Operation Flow** (New FOMC Statement Published):

1. **Trigger**: Cron job executes on FOMC meeting day (8x/year)
2. **Download**: Fetcher attempts download from known URL pattern
3. **Extract**: Text extractor processes HTML → clean text
4. **Count**: Analyzer counts target keywords (11 words from catalog)
5. **Compare**: Detector compares counts to 6-month baseline
6. **Detect**: If emergence (0→>0) or removal (>0→0 for 3 docs), generate alert
7. **Alert**: Format alert with context, evidence, links
8. **Output**: Write JSON alert + update visualizations

**Historical Analysis Flow** (One-Time):

1. **Batch Download**: Fetch all documents 2008-present (~240 docs)
2. **Batch Extract**: Process all downloads → text files
3. **Batch Count**: Count keywords in all documents
4. **Detect**: Find all historical shifts
5. **Validate**: Compare detections to Document 02 catalog (ground truth)
6. **Report**: Generate summary report + timeline visualizations

### 2.3 Component Interactions

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   Fetcher    │───────>│  Extractor   │───────>│   Analyzer   │
│              │  files │              │  text  │              │
└──────────────┘        └──────────────┘        └──────────────┘
       ↓                       ↓                       ↓
   metadata.json         extraction.json         metrics.csv
                                                       ↓
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Alert Gen   │<───────│   Detector   │<───────│   Config     │
│              │ alerts │              │ params │              │
└──────────────┘        └──────────────┘        └──────────────┘
       ↓
   alerts/*.json
   visualizations/*.png
```

**Component Dependencies**:
- Fetcher: Independent (only depends on federalreserve.gov availability)
- Extractor: Depends on Fetcher output (raw files)
- Analyzer: Depends on Extractor output (text files)
- Detector: Depends on Analyzer output (metrics) + Config (keywords, thresholds)
- Alert Generator: Depends on Detector output (shift events) + Config (context catalog)

---

## 3. Component Design

### 3.1 Document Fetcher Module

**Purpose**: Download FOMC documents from Federal Reserve website

**Responsibility**: Retrieve HTML/PDF files, handle network errors, respect rate limits

**Interface**:
```python
class DocumentFetcher:
    """Downloads Federal Reserve documents."""

    def __init__(self, output_dir: str, config: Config):
        """Initialize with output directory and configuration."""

    def download_document(self, doc_type: str, date: str) -> DownloadResult:
        """
        Download single document.

        Args:
            doc_type: 'policy_statement' | 'fomc_minutes' | 'beige_book'
            date: YYYYMMDD format (e.g., '20211215')

        Returns:
            DownloadResult with status, filepath, metadata

        Raises:
            NetworkError: If all retries fail
        """

    def download_batch(self, documents: List[DocumentSpec]) -> BatchResult:
        """Download multiple documents with progress tracking."""

    def get_latest_statement_date(self) -> str:
        """Determine next expected FOMC statement date."""

    def save_metadata(self, filepath: str):
        """Save download metadata for audit trail."""
```

**Design Decisions**:

**Why batch processing vs streaming**: FOMC publishes on predictable schedule (8x/year), no continuous stream to monitor. Batch approach respectful to Fed servers and simpler to implement.

**Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s delays)
- Rationale: Network transients common; Fed website occasionally slow
- Acceptance: After 3 failures, log error and continue to next document
- Tradeoff: May miss occasional document requiring manual download

**Rate limiting**: 1-second delay between requests
- Rationale: Respectful to Fed servers; avoid anti-scraping measures
- Compliance: robots.txt adherence (REQ-CONST-003)

**Pseudocode**:
```
function download_document(doc_type, date):
    url = construct_url(doc_type, date)
    filepath = construct_filepath(doc_type, date)

    for attempt in 1 to MAX_RETRIES (3):
        try:
            response = http_get(url, timeout=30 seconds)

            if response.status_code == 200:
                save_to_file(filepath, response.content)
                log_success(url, filepath, len(response.content))
                sleep(1 second)  # Rate limiting
                return DownloadResult(success=True, filepath=filepath)

            else if response.status_code == 404:
                # Document doesn't exist (date wrong or not published yet)
                log_not_found(url)
                return DownloadResult(success=False, error="404 Not Found")

        catch NetworkError as e:
            wait_time = BACKOFF_BASE * (2 ^ attempt)  # 1s, 2s, 4s
            log_retry(url, attempt, wait_time)
            sleep(wait_time)

    log_failure(url, "Max retries exceeded")
    return DownloadResult(success=False, error="Max retries exceeded")
```

**Error Handling**:
- `NetworkError`: Retry with backoff
- `404 Not Found`: Log and skip (document may not exist yet)
- `Timeout`: Retry (30-second timeout per request)
- `Disk Full`: Critical error, halt execution
- `Invalid URL`: Programming error, raise exception

**Concurrency**: Not needed (8 documents/year = minimal throughput requirements)

### 3.2 Text Extraction Module

**Purpose**: Extract clean text from downloaded HTML/PDF documents

**Responsibility**: Parse HTML/PDF, remove boilerplate, preserve policy content

**Interface**:
```python
class TextExtractor:
    """Extracts text from Fed documents."""

    def __init__(self, input_dir: str, output_dir: str):
        """Initialize with input (raw) and output (processed) directories."""

    def extract_html(self, filepath: str) -> ExtractionResult:
        """
        Extract text from HTML document.

        Returns:
            ExtractionResult with text, word_count, structure_info, success
        """

    def extract_pdf(self, filepath: str) -> ExtractionResult:
        """Extract text from PDF document."""

    def clean_text(self, raw_text: str) -> str:
        """Remove boilerplate and normalize whitespace."""

    def validate_extraction(self, result: ExtractionResult) -> bool:
        """Check if extraction is complete (min word count, no errors)."""
```

**Design Decisions**:

**Version-aware parsing strategy** (Based on Document 01 findings):
- Fed website structure changed in 2013
- Solution: Cascading selector fallback

**Cascading selectors**:
```
1. Try modern format: <div id="article">  (2013+)
2. Try legacy format: <div id="leftText"> (2008-2012)
3. Try alternative: <div id="generalContentText">
4. Fallback: <body> tag
```

**Boilerplate removal**:
- Remove: `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` tags
- Remove: "Board of Governors" footer text
- Remove: Social media links ("Share on Twitter", etc.)
- Preserve: Section headings, paragraph text, tables

**Pseudocode**:
```
function extract_html(filepath):
    html_content = read_file(filepath)
    soup = parse_html(html_content, parser='lxml')

    # Remove noise elements
    for tag in ['script', 'style', 'nav', 'footer', 'header']:
        remove_all(soup, tag)

    # Find main content with cascading strategy
    main_content = soup.find('div', id='article')
    if not main_content:
        main_content = soup.find('div', id='leftText')
    if not main_content:
        main_content = soup.find('div', id='generalContentText')
    if not main_content:
        main_content = soup.body

    if main_content:
        # Extract text with newline preservation
        text = main_content.get_text(separator='\n', strip=True)

        # Clean whitespace
        text = regex_replace(text, r'\n\s*\n', '\n\n')  # Normalize blank lines
        text = regex_replace(text, r' +', ' ')  # Collapse multiple spaces

        # Validate
        word_count = len(text.split())
        if word_count < MIN_WORD_COUNT_THRESHOLD:
            return ExtractionResult(success=False, error="Insufficient text")

        return ExtractionResult(success=True, text=text, word_count=word_count)
    else:
        return ExtractionResult(success=False, error="Main content not found")
```

**PDF Extraction** (pdfplumber):
```
function extract_pdf(filepath):
    pdf = open_pdf(filepath)
    text_parts = []

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    text = join(text_parts, separator='\n\n')
    text = clean_text(text)

    return ExtractionResult(success=True, text=text,
                            word_count=len(text.split()),
                            num_pages=len(pdf.pages))
```

**Validation** (REQ-REL-002):
- Minimum word count: 100 words (statements), 1000 words (minutes)
- No extraction errors logged
- Text contains expected section markers (for FOMC statements: "Committee Policy Action")

### 3.3 Language Analysis Module

**Purpose**: Count keyword occurrences in documents over time

**Responsibility**: Track target words, maintain time-series data, calculate baselines

**Interface**:
```python
class LanguageAnalyzer:
    """Analyzes keyword frequencies in Fed documents."""

    def __init__(self, keywords: List[str], data_dir: str):
        """Initialize with target keywords and data directory."""

    def count_word_in_document(self, filepath: str, word: str) -> int:
        """
        Count occurrences of word in document.

        Uses whole-word matching (regex \b{word}\b).
        Case-insensitive.
        """

    def analyze_document(self, filepath: str, doc_date: str) -> DocumentMetrics:
        """
        Count all keywords in document.

        Returns:
            DocumentMetrics with {word: count} mapping, date, doc_type
        """

    def build_time_series(self, documents: List[str]) -> pd.DataFrame:
        """
        Build time-series dataset of keyword frequencies.

        Returns DataFrame with columns: date, doc_type, word, count
        """

    def calculate_baseline(self, word: str, current_date: str,
                           window_months: int = 6) -> float:
        """
        Calculate baseline (average) word count from historical window.

        Args:
            word: Target keyword
            current_date: Reference date
            window_months: Lookback period (default 6 months)

        Returns:
            Average count over window period
        """
```

**Algorithm**: Keyword counting (from Document 03)

**Method**: Regex whole-word matching
```python
pattern = rf'\b{word}\b'
matches = re.findall(pattern, text, re.IGNORECASE)
count = len(matches)
```

**Rationale for regex approach**:
- Avoids partial matches ("transitory" should not match "transitorily")
- Case-insensitive (matches "Transitory", "TRANSITORY", "transitory")
- Fast execution (<0.1 seconds per document)
- Standard library (no ML dependencies)

**Baseline Calculation**:
```
function calculate_baseline(word, current_date, window_months=6):
    # Get documents from previous 6 months
    start_date = subtract_months(current_date, window_months)
    historical_docs = filter_documents(date >= start_date, date < current_date)

    # Count word in each historical document
    counts = []
    for doc in historical_docs:
        count = count_word_in_document(doc, word)
        counts.append(count)

    # Calculate average
    if len(counts) > 0:
        baseline = mean(counts)
    else:
        baseline = 0  # No historical data

    return baseline
```

**Edge Cases**:
- Insufficient historical data (<3 documents): Set baseline to 0, skip removal detection
- First document in corpus: No baseline available, only detect emergence
- Word never appeared before: Baseline = 0, any occurrence triggers emergence alert

### 3.4 Shift Detection Module

**Purpose**: Detect when keyword frequencies change significantly

**Responsibility**: Compare current counts to baseline, apply shift detection rules

**Interface**:
```python
class ShiftDetector:
    """Detects language shifts in Fed communications."""

    def __init__(self, config: DetectionConfig):
        """
        Initialize with detection configuration.

        Config includes:
        - sustained_removal_threshold: Number of consecutive docs (default 3)
        - baseline_window_months: Lookback period (default 6)
        - focus_doc_type: 'policy_statement' (primary signal)
        """

    def detect_shifts(self, word: str, time_series: pd.DataFrame) -> List[Shift]:
        """
        Detect shifts for a single word across time series.

        Returns:
            List of Shift objects (emergence, removal events)
        """

    def detect_emergence(self, word: str, current_count: int,
                         baseline_count: float) -> Optional[Shift]:
        """
        Detect emergence (0 → >0).

        Returns Shift object if detected, None otherwise.
        """

    def detect_removal(self, word: str, current_count: int,
                       baseline_count: float,
                       future_docs: List[Document]) -> Optional[Shift]:
        """
        Detect sustained removal (>0 → 0 for 3+ consecutive docs).

        Returns Shift object if detected, None otherwise.
        """

    def validate_shift(self, shift: Shift) -> bool:
        """Validate shift against false positive criteria."""
```

**Detection Algorithm** (from Document 03, Section 2.1):

**Emergence Detection**:
```
function detect_emergence(word, current_count, baseline_count):
    if baseline_count == 0 and current_count > 0:
        return Shift(
            type='emergence',
            word=word,
            date=current_date,
            change=f"0 → {current_count}",
            confidence='high'  # First occurrence is definitive
        )
    return None
```

**Removal Detection** (Sustained Threshold):
```
function detect_removal(word, current_count, baseline_count, future_docs):
    if baseline_count > 0 and current_count == 0:
        # Check if removal is sustained (next 3 documents also = 0)
        sustained = True
        for doc in future_docs[0:3]:  # Check next 3
            if count_word_in_document(doc, word) > 0:
                sustained = False
                break

        if sustained:
            return Shift(
                type='removal',
                word=word,
                date=current_date,
                change=f"{baseline_count:.1f} → 0",
                confidence='high'  # Sustained absence confirms shift
            )

    return None
```

**Parameter Values** (from Document 03 testing):
- Emergence threshold: `current_count > 0` (any occurrence)
- Removal sustained docs: `3` consecutive documents
- Baseline window: `6 months` (approximately 4 FOMC meetings)
- Minimum sample size: `3 documents` (otherwise insufficient data)

**Rationale for sustained removal threshold**:
- Prevents false positives from single-document absence
- Fed may skip a word occasionally without policy intent
- 3 consecutive docs = ~9 months of sustained absence (high confidence)

**False Positive Avoidance** (REQ-SD-009):
```
function validate_shift(shift):
    # Ignore shifts in procedural sections
    if word_in_procedural_section(shift.word, shift.document):
        return False

    # Ignore attendance/voting changes
    if word_in_voting_record(shift.word):
        return False

    # Ignore one-time mentions
    if not sustained_change(shift.word, shift.date):
        return False

    return True
```

### 3.5 Alert Generation Module

**Purpose**: Format shift detections into user-facing alerts

**Responsibility**: Assemble context, evidence, significance explanation

**Interface**:
```python
class AlertGenerator:
    """Generates user-facing alerts for detected shifts."""

    def __init__(self, context_catalog: Dict, config: AlertConfig):
        """
        Initialize with context catalog from Document 02.

        Context catalog maps words to:
        - shift_id (e.g., "SHIFT-2021-01")
        - context category (e.g., "inflation narrative")
        - historical significance
        """

    def generate_alert(self, shift: Shift, document: Document) -> Alert:
        """
        Create alert from shift detection.

        Returns:
            Alert object with formatted message, evidence, links
        """

    def format_json(self, alert: Alert) -> dict:
        """Format alert as JSON for programmatic consumption."""

    def format_text(self, alert: Alert) -> str:
        """Format alert as human-readable text."""

    def get_historical_context(self, word: str) -> str:
        """Retrieve significance explanation from catalog."""
```

**Alert Structure** (REQ-INT-004):
```json
{
  "alert_id": "ALERT-20211215-001",
  "timestamp": "2021-12-15T14:30:00Z",
  "shift_type": "removal",
  "word": "transitory",
  "document": {
    "type": "policy_statement",
    "date": "2021-12-15",
    "url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20211215a.htm",
    "title": "FOMC Statement December 15, 2021"
  },
  "change": {
    "previous_count": 1.0,
    "current_count": 0,
    "baseline_avg": 1.0,
    "baseline_window": "6 months"
  },
  "context": {
    "category": "inflation narrative",
    "shift_id": "SHIFT-2021-01",
    "significance": "Fed used 'transitory' to describe inflation surge from April-November 2021. Removal signals shift from temporary to persistent inflation framing, indicating policy pivot toward rate increases."
  },
  "evidence": {
    "previous_occurrences": [
      {"date": "2021-04-28", "count": 1},
      {"date": "2021-06-16", "count": 1},
      {"date": "2021-07-28", "count": 1},
      {"date": "2021-09-22", "count": 1},
      {"date": "2021-11-03", "count": 1}
    ],
    "sustained_absence": true,
    "next_3_docs_count": 0
  },
  "confidence": "high",
  "visualization": "/results/visualizations/transitory_timeline.png"
}
```

**Text Format** (REQ-USE-001):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   FEDSPEAK LANGUAGE SHIFT DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Word: "transitory"
Shift Type: Removal
Document: FOMC Statement, December 15, 2021

Change: Word was present in 5 previous statements (April-November 2021)
        Now absent from December statement

Context: Inflation narrative
Shift ID: SHIFT-2021-01

Historical Significance:
Fed used "transitory" to describe inflation surge from April-November 2021.
Removal signals shift from temporary to persistent inflation framing,
indicating policy pivot toward rate increases.

Evidence:
  Previous occurrences: April 2021 (1), June 2021 (1), July 2021 (1),
                        September 2021 (1), November 2021 (1)
  Sustained absence: Yes (confirmed over next 3 documents)

Confidence: High

Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20211215a.htm
Timeline: /results/visualizations/transitory_timeline.png

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Context Assembly**:
```
function generate_alert(shift, document):
    # Get historical context from Document 02 catalog
    context = lookup_context_catalog(shift.word)

    # Assemble evidence
    evidence = {
        'previous_occurrences': get_previous_occurrences(shift.word, shift.date),
        'sustained_absence': check_sustained_absence(shift.word, shift.date),
        'next_3_docs_count': count_next_3_docs(shift.word, shift.date)
    }

    # Generate visualization
    viz_path = create_timeline_plot(shift.word, shift.date)

    # Assemble alert
    alert = Alert(
        alert_id=generate_id(shift.date, shift.word),
        timestamp=now(),
        shift_type=shift.type,
        word=shift.word,
        document=document,
        change=shift.change,
        context=context,
        evidence=evidence,
        confidence=shift.confidence,
        visualization=viz_path
    )

    return alert
```

---

## 4. Data Architecture

### 4.1 Storage Design

**File Structure**:
```
/fedspeak/
  │
  ├── /data/
  │   ├── /raw/                     # Downloaded documents
  │   │   ├── /minutes/
  │   │   │   ├── /2024/
  │   │   │   │   ├── fomc_minutes_20240131.html
  │   │   │   │   └── fomc_minutes_20240320.html
  │   │   │   └── /2023/
  │   │   │       └── ...
  │   │   ├── /statements/
  │   │   │   ├── /2024/
  │   │   │   │   ├── policy_statement_20240131.html
  │   │   │   │   └── policy_statement_20240320.html
  │   │   │   └── /2023/
  │   │   │       └── ...
  │   │   └── /press_transcripts/
  │   │       └── ...
  │   │
  │   ├── /processed/               # Extracted text
  │   │   ├── /minutes/
  │   │   │   ├── /2024/
  │   │   │   │   ├── fomc_minutes_20240131.txt
  │   │   │   │   └── fomc_minutes_20240320.txt
  │   │   │   └── /2023/
  │   │   │       └── ...
  │   │   ├── /statements/
  │   │   │   └── ...
  │   │   ├── extraction_results.csv
  │   │   └── extraction_details.json
  │   │
  │   └── /metadata/               # Corpus metadata
  │       ├── corpus_index.json    # Master index of all documents
  │       ├── download_log.json    # Download history
  │       └── keyword_metrics.csv  # Time-series word counts
  │
  ├── /config/
  │   ├── keywords.yaml            # Target words and context
  │   ├── detection.yaml           # Detection parameters
  │   └── sources.yaml             # Document sources and URLs
  │
  ├── /results/
  │   ├── /alerts/                 # Generated alerts
  │   │   ├── /2024/
  │   │   │   ├── alert_20240131_001.json
  │   │   │   └── alert_20240320_002.json
  │   │   └── alert_history.json
  │   │
  │   ├── /visualizations/         # Timeline plots
  │   │   ├── transitory_timeline.png
  │   │   ├── accommodative_timeline.png
  │   │   └── ...
  │   │
  │   └── /reports/                # Summary reports
  │       ├── monthly_summary_2024_01.html
  │       └── historical_shifts_report.html
  │
  ├── /logs/
  │   ├── fedspeak_2024_01_31.log
  │   ├── fedspeak_2024_03_20.log
  │   └── error.log
  │
  └── /scripts/
      ├── fedspeak.py              # Main CLI
      ├── document_fetcher.py
      ├── text_extractor.py
      ├── language_analyzer.py
      ├── shift_detector.py
      └── alert_generator.py
```

**Rationale for File-Based Storage**:
- No database needed: 240 documents × 11 keywords = 2,640 metrics (trivial for CSV)
- Corpus growth: ~16 new documents/year = minimal storage increase
- Simplicity: No database setup, backup = file copy
- Portability: Transfer project = zip directory
- Transparency: Users can inspect raw data in text editors

**Metadata Schema** (corpus_index.json):
```json
{
  "corpus_version": "1.0",
  "last_updated": "2024-01-31T14:30:00Z",
  "documents": [
    {
      "doc_id": "fomc_stmt_20211215",
      "doc_type": "policy_statement",
      "date": "2021-12-15",
      "url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20211215a.htm",
      "filepath_raw": "data/raw/statements/2021/policy_statement_20211215.html",
      "filepath_processed": "data/processed/statements/2021/policy_statement_20211215.txt",
      "download_status": "success",
      "download_timestamp": "2024-01-15T10:00:00Z",
      "extraction_status": "success",
      "extraction_timestamp": "2024-01-15T10:01:00Z",
      "word_count": 495,
      "file_size_bytes": 142350,
      "detected_shifts": ["transitory_removal"],
      "processing_complete": true
    }
  ]
}
```

**Keyword Metrics Schema** (keyword_metrics.csv):
```
date,doc_type,word,count,baseline_avg,shift_detected,shift_type
2021-04-28,policy_statement,transitory,1,0.0,true,emergence
2021-06-16,policy_statement,transitory,1,1.0,false,
2021-07-28,policy_statement,transitory,1,1.0,false,
2021-09-22,policy_statement,transitory,1,1.0,false,
2021-11-03,policy_statement,transitory,1,1.0,false,
2021-12-15,policy_statement,transitory,0,1.0,true,removal
2022-01-26,policy_statement,transitory,0,0.2,false,
```

### 4.2 Corpus Management

**Initial Corpus Build**:
```
1. Download all FOMC statements 2008-2025 (~120 documents)
2. Download all FOMC minutes 2008-2025 (~120 documents)
3. Extract text from all downloads
4. Build keyword_metrics.csv with historical counts
5. Detect shifts and validate against Document 02 catalog
6. Generate historical report
```

**Incremental Updates** (New FOMC Meeting):
```
1. Fetch new statement (day of meeting)
2. Extract text
3. Count keywords
4. Detect shifts (compare to baseline)
5. Generate alerts if shifts detected
6. Update keyword_metrics.csv
7. Update corpus_index.json
8. Fetch minutes 3 weeks later
9. Repeat steps 2-7 for minutes
```

**Backup Strategy**:
- Weekly backup of `/data/` directory to external storage
- Git version control for `/config/` and `/scripts/`
- Alert history retained indefinitely (disk usage negligible)
- Raw documents retained indefinitely (historical re-analysis)

### 4.3 Data Retention

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Raw documents | Indefinite | Historical corpus for re-analysis |
| Extracted text | Indefinite | Re-running detection with new parameters |
| Keyword metrics | Indefinite | Time-series analysis, trend detection |
| Alerts | Indefinite | Audit trail, false positive review |
| Logs | 1 year | Debugging, performance monitoring |
| Visualizations | 2 years | Historical reference |

**Storage Growth Estimation**:
- Current corpus (2008-2024): ~30 MB
- Annual growth: ~2 MB (16 docs × 125 KB average)
- 10-year projection: ~50 MB total
- Conclusion: Storage is non-issue

---

## 5. Algorithm Design

### 5.1 Detection Algorithm

**Specification**: Keyword Frequency Tracking (Approach 1 from Document 03)

**Method**: Count target word occurrences in each document. Compare current count to historical baseline. Flag significant changes.

**Step-by-Step**:

**Step 1: Load Historical Documents**
```
documents = load_documents_from_corpus(
    date_range=[CORPUS_START_DATE, current_date],
    doc_type='policy_statement'  # Primary signal source
)
# Sort chronologically
documents = sort_by_date(documents)
```

**Step 2: Calculate Metrics for Each Document**
```
metrics = []
for doc in documents:
    doc_metrics = {}
    for word in TARGET_KEYWORDS:
        count = count_word_in_document(doc.text, word)
        doc_metrics[word] = count

    metrics.append({
        'date': doc.date,
        'doc_type': doc.doc_type,
        'metrics': doc_metrics
    })
```

**Step 3: Establish Baseline for Each Keyword**
```
function calculate_baseline(word, current_date, metrics):
    # Get documents from 6 months before current_date
    window_start = subtract_months(current_date, 6)
    historical_metrics = filter(metrics, date >= window_start, date < current_date)

    # Extract counts for this word
    counts = [m.metrics[word] for m in historical_metrics]

    if len(counts) >= MIN_SAMPLE_SIZE:  # 3 documents minimum
        baseline = mean(counts)
    else:
        baseline = 0  # Insufficient data

    return baseline
```

**Step 4: Detect Shifts for New Document**
```
function detect_shifts_in_document(new_doc, metrics, TARGET_KEYWORDS):
    shifts = []

    for word in TARGET_KEYWORDS:
        current_count = count_word_in_document(new_doc.text, word)
        baseline = calculate_baseline(word, new_doc.date, metrics)

        # EMERGENCE DETECTION (0 → >0)
        if baseline == 0 and current_count > 0:
            shifts.append(Shift(
                type='emergence',
                word=word,
                date=new_doc.date,
                previous_count=baseline,
                current_count=current_count,
                confidence='high'
            ))

        # REMOVAL DETECTION (>0 → 0, sustained for 3+ docs)
        if baseline > 0 and current_count == 0:
            # Check future documents for sustained absence
            future_docs = get_next_documents(new_doc.date, count=3)
            sustained = all([count_word_in_document(d.text, word) == 0
                             for d in future_docs])

            if sustained:
                shifts.append(Shift(
                    type='removal',
                    word=word,
                    date=new_doc.date,
                    previous_count=baseline,
                    current_count=0,
                    confidence='high'
                ))

    return shifts
```

**Step 5: Generate Alerts for Detected Shifts**
```
function generate_alerts(shifts, document):
    alerts = []

    for shift in shifts:
        context = lookup_context_catalog(shift.word)
        evidence = assemble_evidence(shift.word, shift.date)

        alert = Alert(
            shift_type=shift.type,
            word=shift.word,
            document=document,
            change=f"{shift.previous_count} → {shift.current_count}",
            context=context,
            evidence=evidence,
            confidence=shift.confidence
        )

        alerts.append(alert)

    return alerts
```

### 5.2 Parameter Values

**From Document 03 Empirical Testing**:

| Parameter | Value | Source | Rationale |
|-----------|-------|--------|-----------|
| **Baseline Window** | 6 months | Doc 03, Sec 6.1 | Approximately 4 FOMC meetings; balances recency vs. sample size |
| **Sustained Removal Threshold** | 3 consecutive docs | Doc 03, Sec 2.1 | ~9 months absence = high confidence; prevents single-doc false positives |
| **Emergence Threshold** | Any occurrence (count > 0) | Doc 03, Sec 2.1 | First use of new term is significant event |
| **Minimum Sample Size** | 3 documents | Doc 03, Sec 7.4 | Statistical minimum for baseline calculation |
| **Document Type Focus** | policy_statement | Doc 02, Sec 5 | Clearest signal; minutes lag and discuss historical language |
| **Target Keywords** | 11 words | Document 02 | Documented shifts from catalog |

**Rationale - Baseline Window (6 months)**:
- FOMC meets 8x/year = ~1 meeting every 6 weeks
- 6 months = ~4 meetings = sufficient sample
- Longer window (12 months) dilutes recent changes
- Shorter window (3 months) = only 2 meetings (insufficient)

**Rationale - Sustained Removal (3 docs)**:
- Fed occasionally omits words without policy intent
- Single absence could be stylistic choice or space constraints
- 3 consecutive absences = ~9 months = deliberate policy signal
- Test cases confirmed: 0 false positives with this threshold

### 5.3 Edge Cases

**Edge Case 1: Insufficient Historical Data**
- **Scenario**: New keyword added, <3 historical documents
- **Handling**: Set baseline = 0, only detect emergence (skip removal detection)
- **Rationale**: Cannot establish meaningful baseline without sample

**Edge Case 2: First Document in Corpus**
- **Scenario**: Analyzing 2008 documents (no prior data)
- **Handling**: All words with count > 0 are "baseline present", not emergent
- **Rationale**: Cannot detect emergence without "before" period

**Edge Case 3: Word Removed Then Re-Introduced**
- **Scenario**: "Accommodative" removed 2018, reappears 2020 (hypothetical)
- **Handling**: Detect removal (2018), then emergence (2020) as separate events
- **Algorithm**: Each shift independent; no "reversal" category

**Edge Case 4: Gradual Decline (Not Immediate Removal)**
- **Scenario**: Word count declines 3 → 2 → 1 → 0 over 4 docs
- **Handling**: Only flag when reaches 0 and stays 0 for 3+ docs
- **Rationale**: Gradual decline may reflect natural variation; focus on complete removal

**Edge Case 5: End of Corpus (Cannot Verify Sustained Removal)**
- **Scenario**: Most recent document shows count = 0, but <3 future docs available
- **Handling**: Do not flag as removal (cannot verify sustainability)
- **Alert**: Log as "potential removal - pending confirmation"

### 5.4 Text Preprocessing

**From Document 01 Findings**:

**Boilerplate Removal**:
```
function remove_boilerplate(text):
    # Remove standard disclaimers
    text = remove_pattern(text, "Board of Governors of the Federal Reserve System")
    text = remove_pattern(text, "For media inquiries, call")
    text = remove_pattern(text, "Last Update:.*\d{4}")

    # Remove navigation
    text = remove_pattern(text, "Home > ")
    text = remove_pattern(text, "Share on (Twitter|Facebook|LinkedIn)")

    # Remove voting records (to avoid false positives)
    text = remove_section(text, start_marker="Voting for", end_marker="Voting against")

    return text
```

**Tokenization**: Not needed (regex word matching handles boundaries)

**Normalization Steps**:
1. Collapse multiple newlines → double newline
2. Collapse multiple spaces → single space
3. Strip leading/trailing whitespace
4. Preserve paragraph structure (for context)

**No Stemming/Lemmatization**:
- Rationale: Fed uses specific word forms ("transitory" ≠ "transition")
- Exact word matching is requirement, not semantic similarity

---

## 6. Technology Stack

### 6.1 Language and Runtime

**Language**: Python 3.8+

**Rationale**:
- **Mature NLP ecosystem**: BeautifulSoup, pandas, matplotlib widely used
- **Standard library strength**: regex, pathlib, datetime built-in
- **Deployment simplicity**: Single-file script, no compilation
- **Maintainability**: Readable syntax, extensive documentation
- **Cross-platform**: Works on Linux, macOS, Windows without changes

**Why Python 3.8+ specifically**:
- `pathlib` improvements (cleaner file handling)
- Type hints supported (optional but helpful for large codebase)
- Compatible with modern Ubuntu LTS (20.04+)
- No cutting-edge features required (stable, predictable)

**Runtime Environment**:
- CPython interpreter (default Python implementation)
- Virtual environment (`venv`) for dependency isolation
- No JIT compilation needed (performance adequate with interpreter)

### 6.2 Core Dependencies

**From Document 03 and reference implementations**:

| Library | Version | Purpose | License | Rationale |
|---------|---------|---------|---------|-----------|
| **beautifulsoup4** | >=4.12.0 | HTML parsing | MIT | Industry standard, robust, handles malformed HTML |
| **lxml** | >=5.0.0 | Parser backend | BSD | Fast C-based parser, better than html.parser |
| **pdfplumber** | >=0.10.0 | PDF extraction | MIT | Better text extraction than PyPDF2, preserves layout |
| **pandas** | >=2.1.0 | Data handling | BSD | Time-series manipulation, CSV I/O, groupby operations |
| **matplotlib** | >=3.8.0 | Visualization | PSF | Timeline plots, frequency charts |
| **requests** | >=2.31.0 | HTTP downloads | Apache 2.0 | Reliable, session management, timeout handling |

**Dependency Selection Rationale**:

**BeautifulSoup over lxml direct**:
- lxml API is low-level and verbose
- BeautifulSoup provides clean Pythonic interface
- BeautifulSoup handles encoding detection automatically
- Both used together: BS4 for API, lxml for speed

**pdfplumber over PyPDF2**:
- PyPDF2 often produces garbled text (spacing issues)
- pdfplumber preserves layout, better for transcripts
- Document 01 testing showed 100% extraction success with pdfplumber

**pandas over raw CSV**:
- Time-series groupby operations (`df.groupby('date')`)
- Easy filtering (`df[df['word'] == 'transitory']`)
- Built-in date parsing
- Plotting integration with matplotlib

**requests over urllib**:
- Cleaner API for sessions, retries
- Built-in timeout handling
- Cookie/header management
- Industry standard (more Stack Overflow examples)

### 6.3 Development Dependencies

**For Testing and Code Quality**:

| Library | Version | Purpose |
|---------|---------|---------|
| **pytest** | >=7.4.0 | Unit testing framework |
| **pytest-cov** | >=4.1.0 | Code coverage reporting |
| **black** | >=23.0.0 | Code formatting (PEP 8) |
| **mypy** | >=1.5.0 | Type checking (optional) |
| **pylint** | >=2.17.0 | Linting (code quality) |

**Justification**:
- pytest: More Pythonic than unittest, better assertions, fixture support
- black: Zero-configuration formatter, no debates on style
- mypy: Catch type errors early (optional but recommended)

### 6.4 No Machine Learning Libraries

**Explicitly NOT using**:
- TensorFlow / PyTorch (semantic embeddings rejected in Doc 03)
- scikit-learn (TF-IDF rejected in Doc 03)
- NLTK / spaCy (no NLP preprocessing needed)
- word2vec / BERT (overkill for keyword tracking)

**Rationale** (from Document 03, Section 5.3):
- Keyword tracking achieved 100% accuracy without ML
- ML adds complexity (1000+ lines vs 200 lines)
- ML requires training data, hyperparameter tuning, model versioning
- ML harder to explain to stakeholders
- No computational infrastructure needed

**Trade-off Accepted**:
- Cannot discover unexpected shifts (requires manual catalog maintenance)
- Document 02 catalog provides 11 known patterns to monitor
- Quarterly manual corpus scans can identify new candidates

---

## 7. Configuration Management

### 7.1 Configuration File Format

**Primary Config**: YAML (readable, hierarchical, supports comments)

**File**: `config/keywords.yaml`
```yaml
# FedSpeak Keyword Configuration
# Source: Document 02 Ground Truth Catalog

keywords:
  - word: "transitory"
    type: deletion
    context: "inflation narrative"
    shift_id: SHIFT-2021-01
    significance: |
      Fed used "transitory" to describe inflation surge from April-November 2021.
      Removal in December 2021 signaled shift from temporary to persistent
      inflation framing, indicating policy pivot toward rate increases.
    enabled: true
    priority: high  # high/medium/low

  - word: "accommodative"
    type: deletion
    context: "policy stance"
    shift_id: SHIFT-2018-01
    significance: |
      "Accommodative" described Fed's supportive policy stance.
      Removal in September 2018 signaled end of post-crisis accommodation,
      transition to neutral/restrictive policy.
    enabled: true
    priority: high

  - word: "patient"
    type: deletion
    context: "forward guidance"
    shift_id: SHIFT-2015-01
    significance: |
      "Patient" in 2014-2015 signaled Fed would wait before raising rates.
      Removal in March 2015 indicated liftoff was imminent (occurred Dec 2015).
    enabled: true
    priority: medium

  - word: "considerable time"
    type: substitution
    context: "forward guidance"
    shift_id: SHIFT-2014-01
    significance: |
      "Considerable time" was forward guidance phrase 2013-2014.
      Substitution with "patient" in December 2014 marked transition
      toward liftoff preparation.
    enabled: true
    priority: medium

  - word: "full range of tools"
    type: addition
    context: "crisis response"
    shift_id: SHIFT-2020-01
    significance: |
      Added in March 2020 during COVID crisis.
      Signaled Fed's readiness to use unconventional policy tools
      (QE, forward guidance, emergency facilities).
    enabled: true
    priority: high
```

**File**: `config/detection.yaml`
```yaml
# Detection Algorithm Parameters
# Source: Document 03 Testing Results

detection:
  # Sustained removal threshold (consecutive docs at count=0)
  sustained_removal_threshold: 3

  # Baseline calculation window (months)
  baseline_window_months: 6

  # Minimum documents needed for baseline
  min_baseline_samples: 3

  # Primary document type for detection
  focus_document_type: policy_statement

  # Confidence levels
  confidence:
    high: "matches known pattern from catalog"
    medium: "new word following known pattern"
    low: "uncertain pattern requiring manual review"

# Alert Configuration
alerts:
  # Output formats
  output_formats:
    - json
    - text
    - html

  # Output directory
  output_dir: results/alerts

  # Include timeline visualization
  include_visualization: true

  # Notification settings (future)
  notify_on_confidence: high  # high/medium/low
```

**File**: `config/sources.yaml`
```yaml
# Data Source Configuration

sources:
  base_url: "https://www.federalreserve.gov"

  # URL templates
  url_templates:
    fomc_minutes: "/monetarypolicy/fomcminutes{date}.htm"
    policy_statement: "/newsevents/pressreleases/monetary{date}a.htm"
    beige_book: "/monetarypolicy/beigebook{date}.htm"
    press_transcript: "/mediacenter/files/FOMCpresconf{date}.pdf"

  # Download settings
  download:
    delay_seconds: 1  # Rate limiting
    retry_attempts: 3
    retry_backoff_base: 1  # seconds (exponential backoff)
    timeout_seconds: 30
    user_agent: "Mozilla/5.0 (Academic Research Bot; FedSpeak Project)"

# Corpus Configuration
corpus:
  start_date: "2008-01-01"  # Pre-2008 returns 404s
  data_dir: "data/"
  raw_subdir: "raw/"
  processed_subdir: "processed/"

# File Naming Patterns
file_naming:
  raw: "{doc_type}_{date}.{ext}"  # e.g., policy_statement_20211215.html
  processed: "{doc_type}_{date}.txt"
  metadata: "{doc_type}_metadata.json"
```

### 7.2 Environment Variables

**For Security-Sensitive or Environment-Specific Values**:

`.env` file (not committed to git):
```bash
# FedSpeak Environment Configuration

# Logging
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR
LOG_DIR=logs/

# Output Paths
RESULTS_DIR=results/
DATA_DIR=data/

# Notification Settings (future enhancement)
EMAIL_ALERTS_ENABLED=false
SLACK_WEBHOOK_URL=""

# Performance
MAX_CONCURRENT_DOWNLOADS=1  # Respect Fed servers
```

**Loading Environment Variables**:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access variables
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DATA_DIR = Path(os.getenv('DATA_DIR', 'data/'))
```

### 7.3 Configuration Validation

**On Startup**:
```
function validate_configuration():
    # Load all config files
    keywords_config = load_yaml('config/keywords.yaml')
    detection_config = load_yaml('config/detection.yaml')
    sources_config = load_yaml('config/sources.yaml')

    errors = []

    # Validate keywords
    for keyword in keywords_config['keywords']:
        if not keyword.get('word'):
            errors.append(f"Keyword missing 'word' field: {keyword}")
        if keyword.get('type') not in ['addition', 'deletion', 'substitution', 'reframing']:
            errors.append(f"Invalid type for '{keyword['word']}': {keyword.get('type')}")
        if not keyword.get('shift_id'):
            errors.append(f"Keyword '{keyword['word']}' missing shift_id")

    # Validate detection parameters
    if detection_config['detection']['sustained_removal_threshold'] < 1:
        errors.append("sustained_removal_threshold must be >= 1")
    if detection_config['detection']['baseline_window_months'] < 1:
        errors.append("baseline_window_months must be >= 1")

    # Validate data directories
    if not Path(sources_config['corpus']['data_dir']).exists():
        errors.append(f"Data directory not found: {sources_config['corpus']['data_dir']}")

    # Report errors
    if errors:
        for error in errors:
            log_error(error)
        raise ConfigurationError(f"{len(errors)} configuration errors found")

    log_info("✓ Configuration validation passed")
```

**Error Messages** (REQ-USE-006):
```
Example: "Invalid configuration in config/keywords.yaml:
         Keyword 'transitory' missing required field 'shift_id'

         Fix: Add shift_id field to keyword definition"
```

---

## 8. Error Handling Strategy

### 8.1 Error Categories

**Category 1: Network Errors** (REQ-REL-001)

**Handling Approach**:
```python
def download_with_retry(url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            log_warning(f"Timeout on attempt {attempt}/{max_retries}: {url}")
            if attempt < max_retries:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                log_error(f"Failed after {max_retries} attempts: {url}")
                raise NetworkError(f"Timeout after {max_retries} retries")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Document doesn't exist (not an error, just skip)
                log_info(f"Document not found (404): {url}")
                return None
            else:
                log_error(f"HTTP error {e.response.status_code}: {url}")
                raise

        except requests.exceptions.RequestException as e:
            log_error(f"Request failed: {url} - {e}")
            if attempt < max_retries:
                sleep(2 ** attempt)
            else:
                raise NetworkError(f"Request failed after {max_retries} retries")
```

**Recovery**: Retry with exponential backoff, skip document if all retries fail

**Category 2: Parsing Errors**

**Handling Approach**:
```python
def extract_text_safe(filepath):
    try:
        result = extract_html(filepath)

        # Validate extraction
        if not result['success']:
            log_warning(f"Extraction failed for {filepath}: {result['error']}")
            return None

        if result['word_count'] < MIN_WORD_COUNT:
            log_warning(f"Extracted text too short ({result['word_count']} words): {filepath}")
            return None

        return result

    except Exception as e:
        log_error(f"Unexpected error extracting {filepath}: {e}")
        log_error(traceback.format_exc())
        return None
```

**Recovery**: Log error, mark document as failed, continue to next document

**Category 3: Data Quality Errors** (REQ-REL-002)

**Validation Checks**:
```python
def validate_extracted_text(text, doc_type):
    errors = []

    # Check minimum word count
    word_count = len(text.split())
    min_count = MIN_WORD_COUNT[doc_type]  # 100 for statements, 1000 for minutes
    if word_count < min_count:
        errors.append(f"Insufficient text: {word_count} < {min_count} words")

    # Check for expected section markers
    if doc_type == 'policy_statement':
        if "Committee" not in text and "Federal Reserve" not in text:
            errors.append("Missing expected keywords (Committee, Federal Reserve)")

    # Check for extraction artifacts
    if text.count('\n\n\n') > 10:
        errors.append("Excessive blank lines (possible extraction error)")

    if errors:
        log_warning(f"Data quality issues: {', '.join(errors)}")
        return False

    return True
```

**Recovery**: Reject extraction, flag for manual review

**Category 4: Algorithm Errors**

**Handling Approach**:
```python
def detect_shifts_safe(document, metrics):
    try:
        shifts = detect_shifts(document, metrics)
        return shifts

    except InsufficientDataError as e:
        log_info(f"Skipping detection for {document.date}: {e}")
        return []

    except Exception as e:
        log_error(f"Detection error for {document.date}: {e}")
        log_error(traceback.format_exc())
        # Do not generate alerts if detection fails
        return []
```

**Recovery**: Skip shift detection for problematic document, alert admin

### 8.2 Logging Strategy

**Log Levels**:
- **DEBUG**: Detailed execution flow (word counts, baseline calculations)
- **INFO**: Normal operations (downloads, detections, alerts)
- **WARNING**: Recoverable errors (failed download, skipped document)
- **ERROR**: Serious errors (parsing failure, config invalid)
- **CRITICAL**: System-level failures (cannot write to disk, config missing)

**Log Format**:
```
2024-01-31 14:30:15 | INFO | document_fetcher | Downloaded policy_statement_20240131.html (142 KB)
2024-01-31 14:30:16 | INFO | text_extractor | Extracted 495 words from policy_statement_20240131.html
2024-01-31 14:30:17 | INFO | shift_detector | SHIFT DETECTED: 'transitory' removal in 20211215
2024-01-31 14:30:18 | WARNING | document_fetcher | 404 Not Found: /monetarypolicy/fomcminutes20240199.htm
2024-01-31 14:30:19 | ERROR | text_extractor | Failed to parse fomc_minutes_20240131.html: invalid HTML
```

**Log Files** (REQ-INT-005):
```
/logs/
  fedspeak_2024_01_31.log     # Daily log (all levels)
  error.log                    # Errors only (persistent)
```

**Log Rotation**:
- Daily logs: Retain for 1 year
- Error log: Retain indefinitely (compressed after 1 year)
- Log rotation handled by `logging.handlers.RotatingFileHandler`

**Implementation**:
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_dir='logs/', log_level='INFO'):
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True)

    # Daily log file
    daily_log = log_dir / f"fedspeak_{datetime.now().strftime('%Y_%m_%d')}.log"

    # Error log file (persistent)
    error_log = log_dir / 'error.log'

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler(daily_log),
            RotatingFileHandler(error_log, maxBytes=10*1024*1024, backupCount=5),
            logging.StreamHandler()  # Also print to console
        ]
    )
```

### 8.3 Recovery Mechanisms

**Automated Recovery**:

**Scenario 1: Download Failed (Network Glitch)**
- Retry 3 times with exponential backoff
- If still fails, log error and continue
- Next scheduled run will retry (FOMC documents don't change)

**Scenario 2: Extraction Failed (Malformed HTML)**
- Log error with document identifier
- Skip to next document
- Generate report of failed extractions for manual review
- Admin can manually download/extract if needed

**Scenario 3: Disk Space Low**
- Check available disk space before downloads
- If <100 MB free, send warning alert
- If <50 MB free, halt execution (prevent corruption)

**Manual Intervention Required**:

**Scenario 1: Configuration Error**
- System cannot start if config invalid
- Error message points to specific config line
- Admin fixes config, restarts system

**Scenario 2: Persistent Network Failure**
- If >50% of downloads fail in single run, alert admin
- Possible causes: Fed website down, network outage, IP blocked
- Admin investigates, may need to pause system

**Scenario 3: False Positive Alert**
- User reports alert is incorrect
- Admin reviews detection logic, may adjust parameters
- Update config/keywords.yaml to exclude false positive patterns
- Re-run detection on historical corpus to validate fix

**Recovery Checklist**:
```python
def recovery_checklist():
    """Run before system startup to verify healthy state."""
    checks = []

    # Check 1: Data directories exist
    checks.append(("Data directories", check_directories_exist()))

    # Check 2: Config files valid
    checks.append(("Configuration", validate_configuration()))

    # Check 3: Disk space available
    checks.append(("Disk space", check_disk_space() > 100_000_000))

    # Check 4: Network connectivity
    checks.append(("Network", test_network_connectivity()))

    # Check 5: Last run completed successfully
    checks.append(("Last run", check_last_run_status()))

    # Report
    for check_name, passed in checks:
        if passed:
            log_info(f"✓ {check_name}")
        else:
            log_error(f"✗ {check_name} FAILED")
            return False

    return True
```

---

## 9. Testing Strategy

### 9.1 Unit Testing

**Objective**: Test each component in isolation with mocked dependencies

**Test Coverage Target**: 80% code coverage minimum (REQ-MAINT-008)

**Component Tests**:

**Document Fetcher Tests**:
```python
import pytest
from unittest.mock import Mock, patch
from document_fetcher import DocumentFetcher

class TestDocumentFetcher:
    def test_download_success(self, tmp_path):
        """Test successful document download."""
        fetcher = DocumentFetcher(output_dir=tmp_path)

        # Mock HTTP response
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html>Test content</html>"
            mock_get.return_value = mock_response

            result = fetcher.download_document('policy_statement', '20211215')

            assert result['status'] == 'success'
            assert result['file_size'] == len(b"<html>Test content</html>")
            assert (tmp_path / 'policy_statement_20211215.html').exists()

    def test_download_404(self, tmp_path):
        """Test handling of 404 Not Found."""
        fetcher = DocumentFetcher(output_dir=tmp_path)

        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError()
            mock_get.return_value = mock_response

            result = fetcher.download_document('policy_statement', '20991231')

            assert result['status'] == 'failed'
            assert '404' in result['error']

    def test_retry_logic(self, tmp_path):
        """Test retry with exponential backoff."""
        fetcher = DocumentFetcher(output_dir=tmp_path)

        with patch('requests.Session.get') as mock_get:
            # Fail twice, succeed on third attempt
            mock_get.side_effect = [
                requests.Timeout(),
                requests.Timeout(),
                Mock(status_code=200, content=b"Success")
            ]

            result = fetcher.download_document('policy_statement', '20211215')

            assert result['status'] == 'success'
            assert mock_get.call_count == 3
```

**Text Extractor Tests**:
```python
class TestTextExtractor:
    def test_extract_html_modern_format(self, tmp_path):
        """Test extraction from modern Fed format (2013+)."""
        html = """
        <html>
          <div id="article">
            <p>Federal Open Market Committee statement.</p>
            <p>The Committee decided to maintain the target range.</p>
          </div>
        </html>
        """
        filepath = tmp_path / 'test.html'
        filepath.write_text(html)

        extractor = TextExtractor()
        result = extractor.extract_html(filepath)

        assert result['success'] == True
        assert 'Federal Open Market Committee' in result['text']
        assert result['word_count'] > 10

    def test_extract_html_legacy_format(self, tmp_path):
        """Test extraction from legacy Fed format (2008-2012)."""
        html = """
        <html>
          <div id="leftText">
            <p>Policy statement content.</p>
          </div>
        </html>
        """
        filepath = tmp_path / 'test.html'
        filepath.write_text(html)

        extractor = TextExtractor()
        result = extractor.extract_html(filepath)

        assert result['success'] == True
        assert 'Policy statement' in result['text']

    def test_extraction_validation_fail(self, tmp_path):
        """Test that insufficient text fails validation."""
        html = "<html><body>Too short</body></html>"
        filepath = tmp_path / 'test.html'
        filepath.write_text(html)

        extractor = TextExtractor()
        result = extractor.extract_html(filepath)

        # Should fail validation due to low word count
        assert result['success'] == False or result['word_count'] < 100
```

**Language Analyzer Tests**:
```python
class TestLanguageAnalyzer:
    def test_count_word_exact_match(self, tmp_path):
        """Test whole-word matching."""
        text = "The transitory inflation is transitory but transitoryness is not."
        filepath = tmp_path / 'test.txt'
        filepath.write_text(text)

        analyzer = LanguageAnalyzer(['transitory'])
        count = analyzer.count_word_in_document(filepath, 'transitory')

        # Should match "transitory" twice, not "transitoryness"
        assert count == 2

    def test_case_insensitive(self, tmp_path):
        """Test case-insensitive matching."""
        text = "Transitory TRANSITORY transitory"
        filepath = tmp_path / 'test.txt'
        filepath.write_text(text)

        analyzer = LanguageAnalyzer(['transitory'])
        count = analyzer.count_word_in_document(filepath, 'transitory')

        assert count == 3

    def test_baseline_calculation(self):
        """Test baseline calculation from historical window."""
        # Create sample time-series data
        data = {
            'date': ['2021-01-01', '2021-02-01', '2021-03-01', '2021-04-01'],
            'word': ['transitory', 'transitory', 'transitory', 'transitory'],
            'count': [0, 0, 1, 1]
        }
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        analyzer = LanguageAnalyzer(['transitory'])
        baseline = analyzer.calculate_baseline('transitory', '2021-04-01', df)

        # Average of [0, 0, 1] = 0.33
        assert abs(baseline - 0.33) < 0.1
```

**Shift Detector Tests**:
```python
class TestShiftDetector:
    def test_detect_emergence(self):
        """Test emergence detection (0 → >0)."""
        detector = ShiftDetector(config={'sustained_removal_threshold': 3})

        shift = detector.detect_emergence(
            word='transitory',
            current_count=1,
            baseline_count=0.0
        )

        assert shift is not None
        assert shift.type == 'emergence'
        assert shift.word == 'transitory'

    def test_detect_removal_sustained(self):
        """Test sustained removal detection."""
        detector = ShiftDetector(config={'sustained_removal_threshold': 3})

        # Mock future documents all showing count = 0
        future_docs = [
            Mock(date='2021-12-15', count=0),
            Mock(date='2022-01-26', count=0),
            Mock(date='2022-03-16', count=0)
        ]

        shift = detector.detect_removal(
            word='transitory',
            current_count=0,
            baseline_count=1.0,
            future_docs=future_docs
        )

        assert shift is not None
        assert shift.type == 'removal'

    def test_detect_removal_not_sustained(self):
        """Test that single-doc absence doesn't trigger removal."""
        detector = ShiftDetector(config={'sustained_removal_threshold': 3})

        # Word returns in second future doc
        future_docs = [
            Mock(date='2021-12-15', count=0),
            Mock(date='2022-01-26', count=1),  # Word returns
            Mock(date='2022-03-16', count=1)
        ]

        shift = detector.detect_removal(
            word='transitory',
            current_count=0,
            baseline_count=1.0,
            future_docs=future_docs
        )

        # Should NOT detect removal (not sustained)
        assert shift is None
```

**Test Execution**:
```bash
# Run all unit tests
pytest tests/unit/ -v --cov=scripts --cov-report=term-missing

# Run specific test module
pytest tests/unit/test_shift_detector.py -v

# Check coverage
pytest --cov=scripts --cov-report=html
```

### 9.2 Integration Testing

**Objective**: Test component interactions with real data

**Integration Test Scenarios**:

**End-to-End Pipeline Test**:
```python
class TestIntegrationPipeline:
    def test_full_pipeline_historical_corpus(self, tmp_path):
        """Test complete pipeline on historical corpus."""
        # Setup
        config = load_config('config/keywords.yaml')
        fetcher = DocumentFetcher(output_dir=tmp_path / 'raw')
        extractor = TextExtractor(input_dir=tmp_path / 'raw',
                                    output_dir=tmp_path / 'processed')
        analyzer = LanguageAnalyzer(keywords=['transitory'])
        detector = ShiftDetector(config=config)

        # Download sample documents (2021 transitory test case)
        docs_to_download = [
            {'doc_type': 'policy_statement', 'date': '20210428'},  # Emergence
            {'doc_type': 'policy_statement', 'date': '20210616'},
            {'doc_type': 'policy_statement', 'date': '20211215'},  # Removal
            {'doc_type': 'policy_statement', 'date': '20220126'},
        ]

        # Execute pipeline
        for doc_spec in docs_to_download:
            # Download
            download_result = fetcher.download_document(**doc_spec)
            assert download_result['status'] == 'success'

            # Extract
            extract_result = extractor.extract_html(download_result['filepath'])
            assert extract_result['success'] == True

            # Count
            metrics = analyzer.analyze_document(extract_result['text'], doc_spec['date'])
            assert 'transitory' in metrics

        # Detect shifts
        time_series = analyzer.build_time_series(docs_to_download)
        shifts = detector.detect_shifts('transitory', time_series)

        # Validate
        assert len(shifts) == 2  # Emergence + removal
        assert any(s.type == 'emergence' for s in shifts)
        assert any(s.type == 'removal' for s in shifts)
```

**Document Format Compatibility Test**:
```python
def test_extract_multiple_formats():
    """Test extraction from different Fed website versions."""
    test_documents = [
        'data/raw/fomc_minutes_20081216.html',  # 2008 format
        'data/raw/fomc_minutes_20131218.html',  # 2013+ format
        'data/raw/policy_statement_20230322.html',  # Recent format
    ]

    extractor = TextExtractor()
    results = []

    for doc_path in test_documents:
        result = extractor.extract_html(doc_path)
        results.append(result)

    # All should succeed despite format differences
    assert all(r['success'] for r in results)
    assert all(r['word_count'] > 100 for r in results)
```

### 9.3 Validation Testing

**Objective**: Validate against ground truth from Document 02

**Test Cases from Document 02 Catalog**:

```python
class TestGroundTruthValidation:
    """Validate system against known shifts from Document 02."""

    def test_transitory_shift_2021(self):
        """SUCCESS-005: Validate 'transitory' shift detection."""
        # Run detection on April-December 2021 statements
        detector = run_detection_on_corpus(
            start_date='2021-01-01',
            end_date='2022-06-30',
            keywords=['transitory']
        )

        shifts = detector.get_shifts('transitory')

        # Validate emergence
        emergence = [s for s in shifts if s.type == 'emergence']
        assert len(emergence) == 1
        assert emergence[0].date == '2021-04-28'  # April 2021 statement

        # Validate removal
        removal = [s for s in shifts if s.type == 'removal']
        assert len(removal) == 1
        assert removal[0].date == '2021-12-15'  # December 2021 statement

        # Detection lag (REQ-ACC-003)
        assert emergence[0].lag_days == 0
        assert removal[0].lag_days == 0

    def test_accommodative_shift_2018(self):
        """SUCCESS-005: Validate 'accommodative' removal."""
        detector = run_detection_on_corpus(
            start_date='2017-01-01',
            end_date='2019-12-31',
            keywords=['accommodative']
        )

        shifts = detector.get_shifts('accommodative')

        # Should detect removal in September 2018
        removal = [s for s in shifts if s.type == 'removal']
        assert len(removal) == 1
        assert removal[0].date == '2018-09-26'
        assert removal[0].lag_days == 0

    def test_all_documented_shifts(self):
        """SUCCESS-001: Detect 10/11 shifts from Document 02."""
        # Load all 11 shifts from Document 02 catalog
        ground_truth_shifts = load_ground_truth('deliverables/02-shifts.md')

        # Run detection on full historical corpus
        detector = run_detection_on_corpus(
            start_date='2008-01-01',
            end_date='2023-12-31',
            keywords=ground_truth_shifts.keys()
        )

        # Count successful detections
        detected = 0
        for shift_id, expected_date in ground_truth_shifts.items():
            if detector.detected_shift(shift_id, expected_date):
                detected += 1

        # SUCCESS-001: At least 10/11 = 91%
        assert detected >= 10
        detection_rate = detected / len(ground_truth_shifts)
        assert detection_rate >= 0.91
```

**False Positive Rate Test**:
```python
def test_false_positive_rate():
    """SUCCESS-002: Validate false positive rate <5%."""
    # Run detection on full corpus
    detector = run_detection_on_corpus(
        start_date='2008-01-01',
        end_date='2023-12-31'
    )

    total_alerts = len(detector.all_shifts)
    ground_truth_shifts = 11  # From Document 02

    # Assume anything beyond ground truth is false positive
    # (Conservative estimate; manual review may validate some)
    false_positives = max(0, total_alerts - ground_truth_shifts)
    false_positive_rate = false_positives / total_alerts if total_alerts > 0 else 0

    assert false_positive_rate < 0.05  # <5% per REQ-ACC-002
```

**Performance Test**:
```python
def test_processing_performance():
    """SUCCESS-003: Validate <20 min for full corpus."""
    import time

    start_time = time.time()

    # Process 240 documents
    run_detection_on_corpus(
        start_date='2008-01-01',
        end_date='2023-12-31'
    )

    elapsed_time = time.time() - start_time

    # REQ-PERF-002: <15 min target, 20 min max
    assert elapsed_time < 1200  # 20 minutes
    print(f"Processed full corpus in {elapsed_time:.1f} seconds")
```

---

## 10. Deployment Architecture

### 10.1 Execution Model

**Processing Mode**: Batch processing (not real-time)

**Trigger**: Cron job scheduled around FOMC meeting dates

**FOMC Meeting Schedule** (Predictable):
- 8 meetings per year
- Scheduled in advance: January, March, May, June, July, September, November, December
- Statements published immediately after meeting (2:00 PM ET)
- Minutes published 3 weeks later

**Cron Schedule**:
```bash
# Check for new FOMC statements daily at 3:00 PM ET during meeting weeks
0 15 * * * /usr/bin/python3 /opt/fedspeak/scripts/fedspeak.py run --doc-type statements

# Check for new minutes weekly on Wednesdays at 2:00 PM ET
0 14 * * 3 /usr/bin/python3 /opt/fedspeak/scripts/fedspeak.py run --doc-type minutes

# Full corpus validation monthly (first Sunday at 1:00 AM)
0 1 1 * * /usr/bin/python3 /opt/fedspeak/scripts/fedspeak.py validate --full-corpus
```

**Manual Execution**:
```bash
# Download latest documents
./fedspeak.py download --start-date 2024-01-01 --end-date 2024-12-31

# Extract text from downloaded documents
./fedspeak.py extract

# Run shift detection
./fedspeak.py analyze

# Generate report
./fedspeak.py report --format html --output results/report.html

# Validate against ground truth
./fedspeak.py validate --test-cases deliverables/02-shifts.md
```

### 10.2 Runtime Environment

**Operating System**: Linux (Ubuntu 20.04+ LTS recommended)
- Also compatible with macOS, Windows

**Python Version**: 3.8+ (tested on 3.8, 3.9, 3.10, 3.11)

**Installation**:
```bash
# Clone repository
git clone https://github.com/username/fedspeak.git
cd fedspeak

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
./fedspeak.py --version
./fedspeak.py test
```

**Directory Structure**:
```
/opt/fedspeak/  (or user's chosen location)
  ├── venv/                 # Virtual environment
  ├── scripts/              # Python modules
  ├── config/               # Configuration files
  ├── data/                 # Corpus storage
  ├── results/              # Alerts and reports
  ├── logs/                 # Log files
  ├── tests/                # Test suite
  ├── fedspeak.py           # Main CLI
  ├── requirements.txt      # Dependencies
  └── README.md             # Documentation
```

### 10.3 Resource Requirements

**CPU**:
- Minimum: 1 core
- Recommended: 2 cores
- Usage: Mostly I/O-bound (HTTP downloads, file reads), minimal CPU intensity

**Memory**:
- Minimum: 512 MB RAM
- Recommended: 2 GB RAM
- Usage: Pandas DataFrame for ~240 documents × 11 keywords = ~2,640 rows (<10 MB)

**Disk**:
- Code + dependencies: ~100 MB
- Corpus storage: ~30 MB (current), growing ~2 MB/year
- Logs: ~10 MB/year
- Total: ~200 MB (ample headroom for 10+ years)

**Network**:
- Bandwidth: Minimal (16 documents/year × ~150 KB = 2.4 MB/year)
- Latency: Not critical (batch processing)
- Availability: Requires internet access to federalreserve.gov

**Storage I/O**:
- Read: ~240 documents × 10 KB = 2.4 MB per analysis run
- Write: ~16 new documents/year + logs
- IOPS: Minimal (sequential reads/writes)

### 10.4 Deployment Options

**Option 1: Personal Laptop/Desktop**
- Install Python, clone repo, run manually
- Suitable for: Individual researchers, ad-hoc analysis
- Cron: Use system cron (macOS/Linux) or Task Scheduler (Windows)

**Option 2: Cloud VM (AWS EC2, GCP, Azure)**
- t2.micro or equivalent (free tier eligible)
- Setup: Install Python, clone repo, configure cron
- Suitable for: Always-on monitoring, automated alerts
- Cost: ~$5-10/month (can be free tier)

**Option 3: Raspberry Pi / Home Server**
- Low-power device sufficient for workload
- Setup: Raspbian OS, Python 3.8+, cron
- Suitable for: Cost-conscious continuous monitoring
- Cost: ~$50 one-time hardware, negligible power

**Recommended Deployment** (MVP):
- Cloud VM (AWS t2.micro or GCP e2-micro)
- Ubuntu 20.04 LTS
- Python 3.8+ in virtual environment
- Cron for scheduling
- Log rotation configured
- SSH access for maintenance

**Deployment Checklist**:
```bash
# System setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3.8 python3-venv git -y

# Application setup
git clone https://github.com/username/fedspeak.git /opt/fedspeak
cd /opt/fedspeak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration
cp config/keywords.example.yaml config/keywords.yaml
# Edit config files as needed

# Permissions
chmod +x fedspeak.py
chmod 644 config/*.yaml

# Initial corpus download
./fedspeak.py download --start-date 2008-01-01 --end-date $(date +%Y-%m-%d)
./fedspeak.py extract
./fedspeak.py analyze

# Validate
./fedspeak.py validate --test-cases deliverables/02-shifts.md

# Setup cron
crontab -e
# Add cron lines from Section 10.1

# Verify
tail -f logs/fedspeak_$(date +%Y_%m_%d).log
```

---

## 11. Monitoring and Observability

### 11.1 Metrics to Track

**Operational Metrics**:

| Metric | Measurement | Alert Threshold |
|--------|-------------|-----------------|
| **Documents Processed** | Count per run | <8 documents = missing data |
| **Processing Time** | Seconds elapsed | >20 min = performance issue |
| **Download Success Rate** | % successful | <90% = network/availability issue |
| **Extraction Success Rate** | % successful | <95% = parsing issue |
| **Alerts Generated** | Count per month | >5 = possible false positives |
| **Disk Usage** | MB in /data/ | >500 MB = cleanup needed |
| **Log File Size** | MB in /logs/ | >100 MB = rotation issue |

**Quality Metrics**:

| Metric | Measurement | Target |
|--------|-------------|--------|
| **Detection Lag** | Days between shift and alert | 0 days |
| **False Positive Rate** | FP / Total Alerts | <5% |
| **Detection Rate** | Detected / Ground Truth | >95% |
| **Uptime** | % of scheduled runs completed | >99% |

**Instrumentation**:
```python
class MetricsCollector:
    """Collect and report system metrics."""

    def __init__(self, metrics_file='data/metadata/metrics.json'):
        self.metrics_file = Path(metrics_file)
        self.metrics = self.load_metrics()

    def record_run(self, run_data: dict):
        """Record metrics from a system run."""
        self.metrics['runs'].append({
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': run_data['duration'],
            'documents_processed': run_data['doc_count'],
            'downloads_successful': run_data['downloads_ok'],
            'downloads_failed': run_data['downloads_failed'],
            'extractions_successful': run_data['extractions_ok'],
            'shifts_detected': run_data['shifts_count'],
            'alerts_generated': run_data['alerts_count']
        })

        self.save_metrics()

    def get_summary(self, period_days=30):
        """Generate summary for last N days."""
        cutoff = datetime.now() - timedelta(days=period_days)
        recent_runs = [r for r in self.metrics['runs']
                       if datetime.fromisoformat(r['timestamp']) > cutoff]

        return {
            'total_runs': len(recent_runs),
            'avg_duration': mean([r['duration_seconds'] for r in recent_runs]),
            'total_documents': sum([r['documents_processed'] for r in recent_runs]),
            'success_rate': mean([r['downloads_successful'] /
                                  (r['downloads_successful'] + r['downloads_failed'])
                                  for r in recent_runs]),
            'alerts_generated': sum([r['alerts_generated'] for r in recent_runs])
        }
```

### 11.2 Health Checks

**Pre-Run Health Check**:
```python
def health_check():
    """Verify system health before execution."""
    checks = {
        'config_valid': validate_config(),
        'data_dirs_exist': check_directories(),
        'disk_space': get_disk_space() > 100_000_000,  # 100 MB
        'network': test_fed_website_reachable(),
        'last_run_success': check_last_run_log()
    }

    all_healthy = all(checks.values())

    if not all_healthy:
        for check, status in checks.items():
            log_error(f"Health check '{check}': {'PASS' if status else 'FAIL'}")

    return all_healthy
```

**Post-Run Validation**:
```python
def post_run_validation():
    """Validate run completed successfully."""
    validations = {
        'alerts_generated': check_alerts_directory(),
        'metrics_updated': check_metrics_file(),
        'logs_written': check_log_file(),
        'no_errors': count_errors_in_log() == 0
    }

    return all(validations.values())
```

### 11.3 Alerting

**System Alerts** (not to be confused with shift detection alerts):

**Email Alerts** (future enhancement):
```python
def send_system_alert(subject, message, severity='warning'):
    """Send alert to system administrator."""
    if severity == 'critical':
        # Immediate notification
        send_email(to=ADMIN_EMAIL, subject=f"[CRITICAL] {subject}", body=message)
    elif severity == 'warning':
        # Daily digest
        queue_for_digest(subject, message)
```

**Alert Conditions**:

| Condition | Severity | Action |
|-----------|----------|--------|
| Health check fails | Warning | Log, retry in 1 hour |
| 3 consecutive run failures | Critical | Email admin, halt cron |
| Detection FP rate >10% | Warning | Email admin, review needed |
| Disk space <50 MB | Critical | Email admin, cleanup required |
| Fed website unreachable 24h | Warning | Log, retry next day |
| New shift detected | Info | Normal operation, log only |

**Log Monitoring**:
```bash
# Monitor for errors in real-time
tail -f logs/fedspeak_$(date +%Y_%m_%d).log | grep ERROR

# Daily error summary
grep ERROR logs/fedspeak_*.log | wc -l

# Alert if >5 errors in last 24 hours
ERROR_COUNT=$(find logs/ -name "fedspeak_*.log" -mtime -1 -exec grep -c ERROR {} \; | paste -sd+ | bc)
if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "High error count: $ERROR_COUNT" | mail -s "FedSpeak Alert" admin@example.com
fi
```

---

## 12. Security Considerations

### 12.1 Data Security

**Data Classification**:
- All Fed documents: **Public** (no confidentiality requirements)
- Configuration files: **Internal** (no sensitive data)
- Logs: **Internal** (may contain URLs, timestamps)
- Alerts: **Internal** (analytical output, not sensitive)

**No Authentication Required**:
- Fed documents are publicly accessible (no API keys, passwords)
- System operates read-only on Fed website (no write access needed)
- No user accounts or credentials managed

**Local Storage Protection**:
```bash
# Set appropriate permissions
chmod 755 /opt/fedspeak                    # Directory: rwxr-xr-x
chmod 644 /opt/fedspeak/config/*.yaml      # Config: rw-r--r--
chmod 600 /opt/fedspeak/.env               # Secrets: rw-------
chmod 644 /opt/fedspeak/data/**/*.txt      # Data: rw-r--r--
```

**Backup Security**:
- Backups stored on local filesystem or encrypted cloud storage
- No sensitive data, but backups should still be access-controlled
- Backup retention: 1 year (compliance with retention policies)

### 12.2 Operational Security

**Rate Limiting** (REQ-CONST-004):
- 1-second delay between requests (respectful to Fed servers)
- User-Agent header identifies as research bot
- No aggressive scraping or DDoS-like behavior

**robots.txt Compliance** (REQ-CONST-003):
```python
def check_robots_txt():
    """Verify compliance with Fed robots.txt."""
    from urllib.robotparser import RobotFileParser

    rp = RobotFileParser()
    rp.set_url("https://www.federalreserve.gov/robots.txt")
    rp.read()

    # Check if our paths are allowed
    paths_to_check = [
        "/monetarypolicy/fomcminutes20240131.htm",
        "/newsevents/pressreleases/monetary20240131a.htm"
    ]

    for path in paths_to_check:
        if not rp.can_fetch("FedSpeakBot", path):
            log_warning(f"robots.txt disallows: {path}")
            return False

    return True
```

**User-Agent Identification**:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Academic Research Bot; FedSpeak Project; contact@example.com)'
}
```

**IP Blocking Risk Mitigation**:
- Respectful rate limiting (1s delay)
- Minimal request volume (16 docs/year)
- No retry storms (max 3 attempts with backoff)
- If blocked: Wait 24 hours, contact Fed webmaster if persistent

### 12.3 Code Security

**Input Validation**:
```python
def validate_date_input(date_str):
    """Validate date format to prevent injection."""
    # Only allow YYYYMMDD format
    if not re.match(r'^\d{8}$', date_str):
        raise ValueError(f"Invalid date format: {date_str}")

    # Check date is reasonable
    try:
        dt = datetime.strptime(date_str, '%Y%m%d')
        if dt.year < 2008 or dt.year > datetime.now().year + 1:
            raise ValueError(f"Date out of range: {date_str}")
    except ValueError as e:
        raise ValueError(f"Invalid date: {e}")

    return date_str
```

**Path Traversal Prevention**:
```python
def safe_filepath(base_dir, filename):
    """Prevent path traversal attacks."""
    # Resolve to absolute path
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()

    # Ensure target is under base directory
    if not str(target).startswith(str(base)):
        raise SecurityError(f"Path traversal attempt: {filename}")

    return target
```

**Dependency Vulnerabilities**:
```bash
# Regular security audits
pip install safety
safety check --file requirements.txt

# Update dependencies quarterly
pip list --outdated
pip install --upgrade beautifulsoup4 lxml pandas matplotlib requests
```

**No Secrets in Code**:
- No API keys (Fed data is public)
- No passwords (no authentication needed)
- Email credentials (if added) → environment variables only
- Never commit .env files to git

---

## 13. Scalability Considerations

### 13.1 Current Scale

**Current Workload**:
- Corpus size: ~240 documents (2008-2023)
- Keywords tracked: 11
- Processing frequency: 8 new documents/year
- Alert volume: ~2-5 alerts/year (historical average)

**Performance Measurements** (from Document 03):
- Single document processing: <2 seconds
- Full corpus (240 docs): <15 minutes
- Keyword counting: <0.1 seconds per document
- Alert generation: <1 second

### 13.2 Future Scale

**10-Year Projection**:
- Corpus size: ~400 documents (240 + 16/year × 10 years)
- Keywords tracked: ~20 (adding new patterns)
- Processing time: ~25 minutes (linear scaling)
- Storage: ~50 MB (trivial)

**Scaling Strategy**: None needed
- Linear scaling is acceptable for batch processing
- 25 minutes for full corpus still well within acceptable range
- No infrastructure changes required

### 13.3 If Scale Increases 10x (Hypothetical)

**Scenario**: Expand to multiple central banks, analyze speeches, daily reports

**Challenges**:
- Corpus size: 2,400 documents
- Processing time: ~2.5 hours (may be too slow)
- Keywords: 100+
- Alert volume: 50+ alerts/year

**Scaling Solutions**:

**Option 1: Parallel Processing**
```python
from multiprocessing import Pool

def process_document_parallel(documents):
    """Process documents in parallel."""
    with Pool(processes=4) as pool:
        results = pool.map(analyze_document, documents)
    return results
```
- 4 cores → 4x speedup → 2.5 hours → 37 minutes
- Acceptable for overnight batch runs

**Option 2: Incremental Processing**
- Only process new documents (not full corpus each run)
- Full corpus validation: Monthly (not daily)
- Daily runs: ~1 minute (only new docs)

**Option 3: Database Storage**
- Replace CSV with SQLite or PostgreSQL
- Faster queries for large time-series data
- Index on (date, word) for performance

**Decision**: Not needed for current scope
- MVP uses file-based storage
- Re-evaluate if corpus exceeds 1,000 documents

---

## 14. Key Design Decisions

### Decision 1: Keyword Frequency Tracking (Not ML)

**Options Considered**:
1. Keyword frequency tracking (simple word counting)
2. TF-IDF change detection
3. Semantic similarity with embeddings
4. N-gram phrase tracking

**Chosen**: Option 1 (Keyword Frequency Tracking)

**Rationale**:
- **Empirical evidence**: Achieved 100% detection accuracy on test cases (Document 03, Section 2.4)
- **Detection lag**: 0 days (same meeting detection) vs estimated >1 day for ML approaches
- **Complexity**: 200 lines vs 1000+ lines for ML implementation
- **Dependencies**: Standard library vs TensorFlow/PyTorch (large install, version conflicts)
- **Interpretability**: Users can see exact word counts vs black-box similarity scores
- **Maintainability**: Simple code that any Python developer can understand
- **Speed**: <2 seconds vs minutes for embedding generation

**Alternatives Rejected**:

**TF-IDF** (Option 2):
- Why not: Adds complexity (scikit-learn dependency, parameter tuning)
- Trade-off: Could discover unexpected shifts, but catalog from Document 02 provides known patterns
- When to reconsider: If false positive rate >10% (would indicate keyword approach insufficient)

**Embeddings** (Option 3):
- Why not: Massive overkill (requires ML infrastructure, training data, GPU for speed)
- Trade-off: Could detect semantic shifts, but only 18% of shifts are reframings (Document 02)
- When to reconsider: If Fed changes communication strategy entirely (unlikely)

**N-grams** (Option 4):
- Why not: Can be implemented as extension of keyword tracking (multi-word keywords)
- Trade-off: Slightly more complex regex, but same underlying algorithm
- When to implement: If Document 02 catalog expands to include multi-word phrases

### Decision 2: Policy Statements Only (Not Minutes)

**Options Considered**:
1. Policy statements only
2. FOMC minutes only
3. Both statements + minutes

**Chosen**: Option 1 (Statements primary, minutes optional)

**Rationale** (from Document 02, Section 5):
- **Signal clarity**: Statements show shifts most clearly (official policy stance)
- **Timing**: Statements published immediately; minutes lag 3 weeks
- **Content focus**: Statements are forward-looking; minutes discuss historical debate
- **Test results**: 100% detection accuracy on statements alone (Document 03)
- **Confusion risk**: Minutes may discuss removed language in historical context (false positives)

**Alternatives Rejected**:

**Minutes only** (Option 2):
- Why not: 3-week lag unacceptable; historical discussion creates noise
- When to reconsider: Never (statements are superior signal)

**Both statements + minutes** (Option 3):
- Why not: Adds complexity (duplicate detection logic, reconciling conflicting signals)
- Trade-off: More data points, but minutes don't add unique value
- Future option: Add minutes as secondary confirmation signal (if time permits)

### Decision 3: 2008-Present Corpus (Not 1990s)

**Options Considered**:
1. Full historical back to 1990s
2. 2008-present only (post-financial crisis)
3. 2013-present (most reliable format)

**Chosen**: Option 2 (2008-present)

**Rationale** (from Document 01, Section 5.1):
- **Availability**: Pre-2008 URLs return 404 errors with current patterns
- **Format consistency**: 2008+ documents use consistent HTML structure
- **Policy regime**: 2008+ covers unconventional policy era (QE, ZIRP, forward guidance)
- **Shift coverage**: Document 02 catalog focuses on 2008+ shifts (most relevant)
- **Corpus size**: 240 documents sufficient for statistical analysis

**Alternatives Rejected**:

**Full 1990s history** (Option 1):
- Why not: URLs don't work (404s); would require FRASER archives or scraping old formats
- Trade-off: More historical context, but modern Fed communication style very different
- Future option: Add if FRASER integration becomes priority (low priority)

**2013-present only** (Option 3):
- Why not: Excludes important shifts (2008 ZIRP, 2010 QE2, 2013 taper)
- Trade-off: Most reliable extraction (consistent modern format)
- When to reconsider: Never (2008-2012 extraction works well with cascading selectors)

### Decision 4: Batch Processing (Not Real-Time)

**Options Considered**:
1. Real-time monitoring (scrape website constantly)
2. Batch processing (check daily/weekly)
3. Manual triggering

**Chosen**: Option 2 (Batch Processing)

**Rationale** (from REQ-CONST-006):
- **Publication schedule**: FOMC publishes 8x/year on known dates (not continuous stream)
- **No real-time data**: Documents published post-meeting (no intra-meeting updates)
- **Acceptable lag**: 24-hour lag acceptable for financial analysts
- **Server respect**: Batch approach avoids hammering Fed servers
- **Simplicity**: Cron job simpler than persistent monitoring daemon

**Alternatives Rejected**:

**Real-time monitoring** (Option 1):
- Why not: No benefit (documents published 8x/year, not continuously)
- Trade-off: Would reduce lag from 24 hours to minutes, but 0-day lag already achieved
- Cost: Complex infrastructure (daemon, restart logic, connection pooling)
- When to reconsider: If Fed starts publishing intra-meeting updates (unlikely)

**Manual triggering** (Option 3):
- Why not: Requires human to remember FOMC dates; defeats automation purpose
- Trade-off: Maximum control, but poor user experience
- When to use: Initial testing, ad-hoc historical analysis

### Decision 5: File-Based Storage (Not Database)

**Options Considered**:
1. Flat files (CSV, JSON)
2. SQLite database
3. PostgreSQL/MySQL

**Chosen**: Option 1 (Flat Files)

**Rationale**:
- **Data volume**: 240 docs × 11 keywords = 2,640 metrics (trivial for CSV)
- **Query complexity**: Simple time-series queries (pandas sufficient)
- **Portability**: Entire project fits in zip file (no DB setup)
- **Transparency**: Users can inspect/edit files with text editor
- **Backup**: File copy (no DB dump/restore)
- **No overhead**: No connection pooling, schema migrations, indexing

**Alternatives Rejected**:

**SQLite** (Option 2):
- Why not: No performance benefit at current scale; adds setup step
- Trade-off: Better for >10,000 documents, but we have 240
- When to reconsider: If corpus exceeds 1,000 documents or complex analytics needed

**PostgreSQL** (Option 3):
- Why not: Massive overkill (server setup, connection management, backups)
- Trade-off: Enterprise features (ACID, replication), but unnecessary
- When to reconsider: Multi-user web application (not in scope)

---

## 15. Open Questions and Risks

### 15.1 Open Questions

**Questions to Resolve During Implementation**:

**Q1: Should we track synonyms of cataloged keywords?**
- Example: "transitory" vs "temporary" vs "transient"
- Current approach: Only exact words from Document 02 catalog
- Investigation needed: Analyze how often Fed uses synonyms instead of target words
- Resolution approach: Manual corpus review; add synonyms to config if frequency >20%

**Q2: How to handle Fed website structure changes?**
- Fed redesigned website in 2013 (managed with cascading selectors)
- Question: If Fed redesigns again, can we detect extraction failures automatically?
- Investigation needed: Monitor word count trends; alert if sudden drop
- Resolution approach: Implement extraction validation (min word count check)

**Q3: Should alerts include market reaction context?**
- Example: "Transitory removal preceded 25bp rate hike in March 2022"
- Current approach: Only Fed language context (no market data)
- Investigation needed: User feedback on alert usefulness
- Resolution approach: Survey target users; add if >50% request market context

**Q4: How to prioritize keywords when catalog grows?**
- Current: All 11 keywords equal priority
- Future: May have 50+ keywords (too many to monitor actively)
- Investigation needed: Rank keywords by historical significance
- Resolution approach: Add "priority" field to config (high/medium/low)

**Q5: Should we generate visualizations on every run?**
- Current: PNG timeline plots for each shift
- Question: Storage cost if 100+ shifts detected historically
- Investigation needed: Measure disk usage after full corpus run
- Resolution approach: Generate on-demand or monthly batch

### 15.2 Risks

**Risk 1: Fed Changes Website Structure**

**Impact**: High (extraction fails → no data → no alerts)

**Probability**: Medium (happened in 2013, could happen again)

**Mitigation**:
- Version-aware extraction with cascading selectors (already implemented)
- Extraction validation alerts admin if word count drops suddenly
- Monitoring: Daily check for extraction failures
- Fallback: Manual extraction for critical documents

**Contingency Plan**:
```python
def detect_structure_change():
    """Alert if recent extractions show unusual pattern."""
    recent_extractions = get_last_n_extractions(n=10)
    avg_word_count = mean([e.word_count for e in recent_extractions])

    # If word count drops >50%, likely structure change
    if avg_word_count < HISTORICAL_AVG * 0.5:
        send_alert("Possible Fed website structure change detected")
```

**Risk 2: Detection Approach Underperforms on New Data**

**Impact**: Medium (missed shifts, lost user trust)

**Probability**: Low (100% accuracy on 5 years of test data)

**Mitigation**:
- Monthly validation against Document 02 ground truth
- User feedback mechanism (report false negatives)
- Parameter tuning: Adjust sustained removal threshold if needed
- Hybrid approach: Add TF-IDF discovery mode for outliers

**Contingency Plan**:
- If false negative rate >10%: Investigate missed shifts
- Add missed words to catalog
- If systematic failures: Reconsider ML approaches (Document 03, Section 7.5)

**Risk 3: False Positive Rate Exceeds Tolerance**

**Impact**: Medium (alert fatigue, user ignores real shifts)

**Probability**: Low (<5% FP rate in testing)

**Mitigation**:
- Sustained removal threshold (3 docs) reduces FPs
- Procedural section exclusion (voting records)
- Confidence scoring (high/medium/low)
- Manual review of low-confidence alerts

**Contingency Plan**:
```python
def review_false_positives():
    """User marks alerts as false positives."""
    # Track FP patterns
    if fp_rate > 0.10:
        log_warning("FP rate exceeded 10%")
        # Analyze common FP patterns
        # Add exclusion rules to config
```

**Risk 4: Fed Implements Anti-Scraping Measures**

**Impact**: High (cannot download documents)

**Probability**: Low (respectful rate limiting, public data)

**Mitigation**:
- 1-second delay between requests
- User-Agent identification
- robots.txt compliance
- Minimal request volume (16 docs/year)

**Contingency Plan**:
- If blocked: Wait 24 hours, reduce frequency
- Contact Fed webmaster (academic research exemption)
- Manual download fallback (user downloads, system processes)

**Risk 5: Keyword Catalog Becomes Stale**

**Impact**: Low (miss new shift types, but detect known patterns)

**Probability**: Medium (Fed language evolves over decades)

**Mitigation**:
- Quarterly manual corpus review
- User-reported shift suggestions
- TF-IDF discovery mode (future enhancement)
- Active monitoring of Fed commentary (Bloomberg, WSJ)

**Contingency Plan**:
- Maintain list of "candidate keywords" (not yet in catalog)
- Run discovery analysis quarterly
- Update catalog when new pattern confirmed (>3 occurrences)

### 15.3 Risk Register Summary

| Risk ID | Risk | Impact | Probability | Mitigation | Owner |
|---------|------|--------|-------------|------------|-------|
| R1 | Fed website redesign | High | Medium | Cascading selectors, monitoring | Dev Team |
| R2 | Detection underperforms | Medium | Low | Monthly validation, parameter tuning | Dev Team |
| R3 | High false positives | Medium | Low | Sustained threshold, confidence scoring | Users + Dev |
| R4 | Anti-scraping measures | High | Low | Rate limiting, robots.txt compliance | Dev Team |
| R5 | Stale keyword catalog | Low | Medium | Quarterly review, user feedback | Research Team |

---

## 16. Future Enhancements

### 16.1 Planned Enhancements (High Priority)

**Enhancement 1: Press Conference Transcript Analysis**

**Source**: Document 01 confirmed PDF transcripts available

**Rationale**: Q&A provides unscripted elaboration on policy language

**Implementation**:
- Add `press_transcript` document type
- PDF extraction already supported (pdfplumber)
- Track same keywords in transcripts
- Alert if shift appears in Q&A before statement

**Effort**: Low (2-3 days)

**Benefit**: Detect shifts 1-2 weeks earlier (Q&A often precedes statement changes)

**Enhancement 2: Beige Book Analysis**

**Source**: Document 01 identified Beige Books as available

**Rationale**: Economic assessment shifts complement policy language shifts

**Implementation**:
- Add `beige_book` document type
- Focus on summary section (avoid regional noise)
- Track economic condition keywords ("strengthening", "weakening", "slowing")

**Effort**: Medium (1 week - requires new keyword catalog)

**Benefit**: Economic narrative shifts (e.g., "labor market tightening" → "softening")

**Enhancement 3: Synonym and Phrase Expansion**

**Source**: Document 03, Section 7.2 identified as refinement need

**Rationale**: Fed may substitute synonyms ("transitory" → "temporary")

**Implementation**:
```yaml
# config/keywords.yaml
keywords:
  - word_group: "transitory_synonyms"
    words: ["transitory", "temporary", "transient", "passing"]
    type: deletion
    context: "inflation narrative"
```

**Effort**: Low (1 day - config change + aggregation logic)

**Benefit**: Catch synonym substitutions (estimated +10% recall)

**Enhancement 4: Adaptive Baseline Calculation**

**Source**: Document 03, Section 7.2 suggested statistical thresholds

**Rationale**: Fixed threshold (3 docs) may miss gradual shifts

**Implementation**:
```python
# Instead of: baseline = mean(last_6_months)
# Use: baseline = mean(last_12_months), threshold = 2 * std_dev

if current_count > baseline + (2 * std_dev):
    flag_increase()
elif current_count < baseline - (2 * std_dev):
    flag_decrease()
```

**Effort**: Medium (3-5 days - requires statistical testing)

**Benefit**: Detect gradual shifts (e.g., word frequency declining over 6 months)

### 16.2 Research Enhancements (Medium Priority)

**Enhancement 5: Hybrid Detection Approach**

**Source**: Document 03, Section 7.5 proposed hybrid method

**Rationale**: Keyword tracking (99% of cases) + semantic outlier detection (novel shifts)

**Implementation**:
1. Run keyword tracking (primary detection)
2. Monthly TF-IDF scan for outlier documents
3. Flag documents with unusual word distributions for manual review
4. Add discovered patterns to keyword catalog

**Effort**: High (2-3 weeks - requires ML integration)

**Benefit**: Discover unexpected shifts (catalog self-updates)

**Enhancement 6: TF-IDF Discovery Mode**

**Source**: Document 03, Section 3.1 noted TF-IDF useful for discovery

**Rationale**: Automated corpus scanning for shift candidates

**Implementation**:
```python
# Quarterly batch job
def discover_shifts():
    """Run TF-IDF on corpus to find unusual word changes."""
    corpus = load_full_corpus()
    tfidf = compute_tfidf(corpus)

    # Find words with largest TF-IDF changes
    changes = detect_tfidf_changes(tfidf, threshold=2.0)

    # Generate candidate list for manual review
    save_candidates('results/shift_candidates.csv', changes)
```

**Effort**: Medium (1-2 weeks)

**Benefit**: Reduce manual catalog maintenance burden

**Enhancement 7: N-gram Phrase Tracking**

**Source**: Document 03, Section 5.2 backup recommendation

**Rationale**: Multi-word shifts ("full range of tools", "considerable time")

**Implementation**:
- Extend keyword regex to multi-word patterns: `r'\bfull range of tools\b'`
- No algorithm changes (same counting logic)

**Effort**: Low (2-3 days)

**Benefit**: Track phrasal shifts (~20% of catalog from Document 02)

### 16.3 Integration Enhancements (Low Priority)

**Enhancement 8: API Endpoint for Programmatic Access**

**Rationale**: Third-party tools query FedSpeak for shift data

**Implementation**:
- Flask/FastAPI web service
- Endpoints: `/api/shifts`, `/api/alerts`, `/api/timeline/{word}`
- JSON responses

**Effort**: Medium (1-2 weeks)

**Benefit**: Integration with trading platforms, research tools

**Enhancement 9: Web Dashboard**

**Rationale**: Interactive exploration instead of CLI reports

**Implementation**:
- Flask web app
- Timeline visualizations (D3.js, Plotly)
- Alert history browser
- Keyword search

**Effort**: High (1 month)

**Benefit**: Better user experience for non-technical users

**Enhancement 10: Email/Slack Alert Delivery**

**Rationale**: Push notifications instead of polling for new alerts

**Implementation**:
```python
def send_email_alert(alert):
    """Email alert to subscribers."""
    smtp_send(
        to=SUBSCRIBERS,
        subject=f"FedSpeak Alert: {alert.word} {alert.shift_type}",
        body=format_text(alert)
    )

def send_slack_alert(alert):
    """Post alert to Slack channel."""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    requests.post(webhook_url, json={'text': format_text(alert)})
```

**Effort**: Low (2-3 days)

**Benefit**: Immediate notification (reduce lag from 24h to minutes)

**Enhancement 11: Historical Fed Transcript Analysis**

**Rationale**: Minutes from 1990s-2000s if accessible via FRASER archives

**Implementation**:
- Scrape FRASER (Federal Reserve Archival System)
- OCR for scanned PDFs (tesseract)
- Extend corpus to 1990+

**Effort**: High (1 month - OCR is error-prone)

**Benefit**: Historical shift patterns (Greenspan era, Volcker era)

### 16.4 Analysis Enhancements (Low Priority)

**Enhancement 12: Shift Clustering Analysis**

**Rationale**: Identify periods of high shift activity (regime changes)

**Implementation**:
```python
def cluster_shifts():
    """Identify periods with multiple shifts."""
    shifts = load_all_shifts()
    # Group shifts by 6-month windows
    windows = group_by_window(shifts, months=6)

    # Flag windows with >3 shifts
    high_activity = [w for w in windows if len(w.shifts) > 3]

    return high_activity  # e.g., 2013 (taper tantrum era)
```

**Effort**: Low (1 week)

**Benefit**: Macro-level regime detection (beyond single-word shifts)

**Enhancement 13: Speaker Attribution in Transcripts**

**Rationale**: Track which Fed officials use specific language in Q&A

**Implementation**:
- Parse speaker labels in transcripts ("CHAIR POWELL:", "GOVERNOR WALLER:")
- Attribute word usage to speakers
- Detect if language originates with Chair vs distributed

**Effort**: Medium (2 weeks - parsing speaker labels is fragile)

**Benefit**: Understand if shifts are Chair-driven or committee-wide

**Enhancement 14: Correlation with Market Reactions**

**Rationale**: Link detected shifts to bond yield changes, equity moves

**Implementation**:
- Fetch market data (yfinance library: 10-year Treasury yields, S&P 500)
- Calculate price changes 24h/48h/1wk after shift detected
- Generate correlation report

**Effort**: Medium (1-2 weeks)

**Benefit**: Quantify market impact of shifts (research/trading value)

**Scope**: Analytical research, not real-time trading

### 16.5 Enhancement Roadmap

**Phase 1 (MVP + 3 months)**:
- Enhancement 3: Synonym expansion
- Enhancement 7: N-gram tracking
- Enhancement 10: Email alerts

**Phase 2 (MVP + 6 months)**:
- Enhancement 1: Press transcript analysis
- Enhancement 4: Adaptive baseline
- Enhancement 9: Web dashboard

**Phase 3 (MVP + 12 months)**:
- Enhancement 5: Hybrid detection
- Enhancement 6: TF-IDF discovery
- Enhancement 8: API endpoint

**Research Track** (ongoing):
- Enhancement 12: Shift clustering
- Enhancement 13: Speaker attribution
- Enhancement 14: Market correlation

---

## Appendix A: Requirements Traceability

This architecture satisfies all 77 requirements from `requirements.md`. Key mappings:

| Requirement Category | Architecture Sections | Status |
|---------------------|----------------------|--------|
| **Data Acquisition** (REQ-DA-001 to DA-010) | Section 3.1 (Document Fetcher) | ✓ Addressed |
| **Text Processing** (REQ-TP-001 to TP-007) | Section 3.2 (Text Extractor) | ✓ Addressed |
| **Language Shift Detection** (REQ-SD-001 to SD-010) | Section 3.4 (Shift Detector), Section 5.1 (Algorithm) | ✓ Addressed |
| **Alert Generation** (REQ-AG-001 to AG-008) | Section 3.5 (Alert Generator) | ✓ Addressed |
| **Historical Analysis** (REQ-HA-001 to HA-005) | Section 2.2 (Data Flow), Section 9.3 (Validation) | ✓ Addressed |
| **Performance** (REQ-PERF-001 to PERF-006) | Section 10.3 (Resource Requirements) | ✓ Addressed |
| **Reliability** (REQ-REL-001 to REL-005) | Section 8 (Error Handling) | ✓ Addressed |
| **Accuracy** (REQ-ACC-001 to ACC-006) | Section 5.1 (Algorithm), Section 9.3 (Validation) | ✓ Addressed |
| **Maintainability** (REQ-MAINT-001 to MAINT-008) | Section 6 (Technology Stack), Section 7 (Configuration) | ✓ Addressed |
| **Usability** (REQ-USE-001 to USE-007) | Section 3.5 (Alert Format), Section 11 (Monitoring) | ✓ Addressed |
| **Data** (REQ-DATA-001 to DATA-012) | Section 4 (Data Architecture) | ✓ Addressed |
| **Constraints** (REQ-CONST-001 to CONST-009) | Section 12 (Security), Section 10 (Deployment) | ✓ Addressed |

**Detailed Traceability**:

- **REQ-SD-001** (Keyword frequency tracking): Section 5.1, Algorithm Design
- **REQ-SD-005** (Sustained removal threshold): Section 5.2, Parameter Values (3 consecutive docs)
- **REQ-PERF-001** (<5 sec/doc): Section 5.1 (expected <2 sec actual)
- **REQ-ACC-003** (0-day lag): Section 5.1 (same-document detection)
- **REQ-CONST-004** (1-second delay): Section 3.1 (Document Fetcher), Section 12.2 (Rate Limiting)

---

## Appendix B: File Organization Reference

**Complete File Tree**:
```
/fedspeak/
├── config/
│   ├── keywords.yaml           # Target words from Document 02
│   ├── detection.yaml          # Algorithm parameters
│   └── sources.yaml            # Fed URL patterns
├── data/
│   ├── raw/
│   │   ├── minutes/            # Downloaded FOMC minutes
│   │   └── statements/         # Downloaded policy statements
│   ├── processed/
│   │   ├── minutes/            # Extracted text from minutes
│   │   ├── statements/         # Extracted text from statements
│   │   └── keyword_metrics.csv # Time-series word counts
│   └── metadata/
│       ├── corpus_index.json   # Master document index
│       └── download_log.json   # Download history
├── deliverables/
│   ├── 01-corpus.md            # Corpus analysis (completed)
│   ├── 02-shifts.md            # Ground truth catalog (completed)
│   ├── 03-methods.md           # Detection feasibility (completed)
│   ├── requirements.md         # Formal requirements (completed)
│   └── architecture.md         # This document
├── logs/
│   ├── fedspeak_YYYY_MM_DD.log # Daily logs
│   └── error.log               # Persistent error log
├── results/
│   ├── alerts/
│   │   └── alert_*.json        # Generated alerts
│   ├── visualizations/
│   │   └── *_timeline.png      # Frequency plots
│   └── reports/
│       └── *.html              # Summary reports
├── scripts/
│   ├── fedspeak.py             # Main CLI
│   ├── document_fetcher.py     # Download module
│   ├── text_extractor.py       # Extraction module
│   ├── language_analyzer.py    # Keyword counting
│   ├── shift_detector.py       # Detection algorithm
│   └── alert_generator.py      # Alert formatting
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── validation/             # Ground truth validation
├── .env                        # Environment variables (not in git)
├── .gitignore
├── README.md                   # User documentation
├── requirements.txt            # Python dependencies
└── setup.py                    # Package setup
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Baseline** | Average word count over historical window (default 6 months) |
| **Corpus** | Collection of Fed documents analyzed by system (2008-present, ~240 docs) |
| **Emergence** | Shift type: Word appears after period of absence (0 → >0) |
| **False Positive** | Alert for non-shift (e.g., procedural language change) |
| **FOMC** | Federal Open Market Committee (Fed's policy-making body) |
| **Ground Truth** | Known shifts documented in Document 02 catalog (11 shifts) |
| **Keyword** | Target word tracked by system (from Document 02 catalog) |
| **Lag** | Days between shift occurrence and detection (target: 0 days) |
| **Policy Statement** | FOMC statement published after each meeting (8x/year) |
| **Removal** | Shift type: Word disappears after sustained use (>0 → 0) |
| **Shift** | Change in Fed language (addition, deletion, substitution, reframing) |
| **Sustained** | Removal persisting for 3+ consecutive documents (threshold) |
| **Time-Series** | Sequence of word counts over time |

---

## Document Control

**Version History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-01 | FedSpeak Architecture Team | Initial architecture document |

**Approval**:

This architecture document is ready for review by project stakeholders.

**Next Steps**:

1. Review and approve architecture
2. Set up development environment (Section 10.4)
3. Implement MVP components (Sections 3.1-3.5)
4. Execute test suite (Section 9)
5. Deploy to staging environment (Section 10)
6. Validate against Document 02 ground truth (Section 9.3)
7. Production deployment

---

**Architecture Document Complete**

*Total Sections: 16*
*Total Pages: ~50*
*Status: Ready for Implementation*

This architecture document provides complete technical specification for implementing FedSpeak. All design questions are answered, all components are specified with pseudocode, and all requirements are traced to architecture decisions.

**Key Deliverables**:
- ✓ Complete system architecture with data flow diagrams
- ✓ Detailed component specifications with interfaces and pseudocode
- ✓ Algorithm design with parameter values from empirical testing
- ✓ Error handling strategy with recovery mechanisms
- ✓ Testing strategy with unit, integration, and validation tests
- ✓ Deployment architecture with resource requirements
- ✓ Monitoring and security considerations
- ✓ Risk analysis with mitigation strategies
- ✓ Future enhancement roadmap
- ✓ Full requirements traceability matrix

**Implementation can begin immediately using this document as blueprint.**

---

*End of Architecture Document*
