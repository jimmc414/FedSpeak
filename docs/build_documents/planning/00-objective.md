# FedSpeak: Project Objective

## Primary Objective

Build a system that automatically detects when the Federal Reserve changes how it describes economic conditions, policy actions, or forward guidance in its official communications. The tool identifies semantic shifts, euphemism adoption, topic emergence/suppression, and narrative pivots before they're widely recognized, providing early signals of policy direction changes.

## Success Criteria

- Detects known historical language shifts (2008 QE euphemism adoption, 2021 "transitory" inflation narrative, 2006 M3 discontinuation language)
- Flags new semantic patterns within 1-2 meetings of their emergence
- Low false positive rate (doesn't alert on trivial word substitutions)
- Generates actionable signals for someone tracking Fed policy credibility and narrative management

## Non-Goals

- Sentiment analysis or predicting market reactions
- Real-time intra-meeting analysis (post-meeting publication is sufficient)
- Analyzing non-Fed central bank communications

## Target User

Financial analysts, Austrian economists, and institutional skeptics who track Federal Reserve narrative management and policy credibility. Users who need early warning of Fed communication shifts before they become consensus observations.

## Project Scope

FedSpeak focuses exclusively on Federal Reserve communications:
- FOMC minutes and statements
- Press conference transcripts
- Beige Book reports
- Board speeches (if relevant)

The system will analyze historical documents back to the 1990s (where available) and monitor new publications going forward.

## Expected Deliverable

A tool that:
1. Maintains a corpus of Fed communications
2. Applies NLP techniques to detect language pattern changes
3. Generates alerts when significant shifts occur
4. Provides context and historical comparison for detected shifts

## Project Status

**Phase:** Exploratory analysis (Documents 01-03)

This objective statement represents the initial project scope and may be refined based on findings from:
- Document 01: Corpus analysis (data availability and structure)
- Document 02: Ground truth catalog (what shifts actually matter)
- Document 03: Detection feasibility (what's technically achievable)

---

*Version 0.1 - October 30, 2025*
