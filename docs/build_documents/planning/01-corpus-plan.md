# Document 01: Corpus Analysis Plan

## Purpose

Understand the raw material we're working with - what's available, how it's structured, and what extraction challenges exist before attempting any analysis.

## Questions to Answer

1. What document types exist and how far back does each go?
2. How consistent is formatting within/across document types?
3. What's the text volume per document (affects processing approach)?
4. Are there format changes that break naive scraping (HTML structure shifts, PDF layout variations)?
5. What non-content elements pollute the text (headers, footers, tables, legal boilerplate)?
6. Which document types are worth focusing on first?

## Data Collection

Download a representative sample of Federal Reserve communications:

### FOMC Minutes
- 3 documents per decade: 1990s, 2000s, 2010s, 2020s
- Total: 12 documents
- URL structure: https://www.federalreserve.gov/monetarypolicy/fomcminutes[YYYYMMDD].htm

### Policy Statements
- 6 documents spanning 2000-2025
- Distributed across different policy regimes (pre-crisis, QE era, normalization, COVID response)
- URL structure: https://www.federalreserve.gov/newsevents/pressreleases/monetary[YYYYMMDD]a.htm

### Press Conference Transcripts
- 4 documents from 2011-2025 (when they started regular press conferences)
- Note: Format may differ significantly from other documents

### Beige Book Reports
- 3 documents from different eras (2005, 2015, 2025)
- URL structure: https://www.federalreserve.gov/monetarypolicy/beigebook[YYYYMM].htm

**Total sample size:** ~25 documents covering format evolution over 30+ years

## Analysis Tasks

### 1. Document Metadata Collection

For each document, record:
- Publication date
- Document type
- Format (HTML, PDF, or both)
- URL structure pattern
- File size (if PDF)
- Availability (is it accessible, or are there gaps?)

Create a table with this information.

### 2. Text Extraction Testing

Test extraction on each format:
- **HTML documents:** Use BeautifulSoup or similar parser
- **PDF documents:** Use pdfplumber, PyPDF2, or pdfminer.six
- **Document success/failure:** Note which documents extract cleanly vs. which have issues
- **Code snippets:** Save working extraction code for each format type

Document specific challenges:
- Malformed HTML
- Scanned PDFs (image-based, no text layer)
- Tables that break text flow
- Multi-column layouts
- Embedded charts/graphs

### 3. Word Count Distribution

For successfully extracted documents:
- Count total words per document
- Calculate statistics: min, max, median, mean per document type
- Identify outliers (unusually short/long documents may indicate extraction problems)

This informs processing approach - very long documents may need chunking or section-based analysis.

### 4. Structure Analysis

Examine document structure elements:
- **Headers/footers:** Board of Governors branding, page numbers, publication dates
- **Section markers:** "Committee Policy Action", "Participants' Views", etc.
- **Speaker labels:** In transcripts, how are speakers identified?
- **Boilerplate text:** Legal disclaimers, standard disclaimers that appear in every document
- **Tables and lists:** How are voting records, economic projections formatted?

Create annotated examples showing:
- Text that should be stripped (non-content)
- Text that should be preserved (actual policy language)
- Structural markers that could be useful for section-based analysis

### 5. Content Categorization

Within each document type, identify:
- **Policy language sections:** Where actual forward guidance and policy decisions are described
- **Economic assessment sections:** Discussion of current conditions
- **Procedural text:** Voting records, meeting logistics, administrative details

Determine which sections contain the signal we care about vs. noise.

### 6. Format Evolution Analysis

Compare documents from different eras:
- Has HTML structure changed (different tags, classes, IDs)?
- Have PDF layouts changed (fonts, spacing, multi-column shifts)?
- Are older documents harder to extract?

This identifies whether we need multiple extraction strategies for different time periods.

## Deliverable Format

Create `01-corpus.md` with the following sections:

### 1. Executive Summary
2-3 paragraphs answering:
- What Fed documents are available and in what formats?
- Can we reliably extract text from them?
- What's the recommended starting point?

### 2. Document Inventory
Table with columns:
- Document Type
- Date Range Available
- Format(s)
- Sample URL
- Extraction Status (Easy/Medium/Hard)

### 3. Extraction Results
For each format type (HTML/PDF):
- Code snippet that worked
- Success rate across sample
- Common failure modes
- Recommended Python libraries

### 4. Text Statistics
Table with columns:
- Document Type
- Word Count (Min/Max/Median)
- Sample Size
- Notes

### 5. Structural Analysis
Annotated examples (2-3 documents) showing:
- Original text with highlighting
- What to strip (boilerplate, headers)
- What to keep (policy language)
- Section boundaries

### 6. Challenges & Recommendations

Document specific issues discovered:
- Extraction failures and workarounds
- Format inconsistencies
- Data quality concerns
- Processing bottlenecks

### 7. Decision & Next Steps

**Based on this analysis, recommend:**
- Which document type to start with and why
- Which time period has the best data quality
- What extraction approach to use
- What preprocessing steps are necessary

**What Document 02 should focus on:**
- If certain document types are unusable, scope ground truth search accordingly
- If extraction is difficult, may need to focus on more recent documents only

## Time Estimate

4-6 hours:
- 1-2 hours: Document collection and downloading
- 2-3 hours: Extraction testing and debugging
- 1 hour: Analysis and documentation

## Tools Needed

- Python 3.x
- Libraries: `beautifulsoup4`, `requests`, `pdfplumber` or `PyPDF2`
- Text editor for annotation
- Spreadsheet or markdown tables for data tracking

## Success Criteria

Document 01 is complete when you can answer:
1. "Which Fed documents should we use?" (with data-backed reasoning)
2. "How do we extract text from them?" (with working code)
3. "What preprocessing is required?" (with specific steps)

---

*This plan may be adjusted based on what's discovered during execution.*
