# Agent Prompt: Comprehensive Version

**Copy this entire prompt to provide to a fresh Claude Code instance:**

---

You are working with FedSpeak, an automated system that detects Federal Reserve language shifts in FOMC policy communications.

PROJECT OVERVIEW:
- Detects when the Fed changes key language (e.g., December 2021 "transitory" removal)
- Uses 4-stage pipeline: Download → Extract → Analyze → Detect
- Tracks 5 keywords + synonyms with 0-day detection lag and 100% validated accuracy
- Language: Python 3.8+
- Status: Production-ready, all 68 tests passing

KEY DOCUMENTATION FILES (read these first):
1. AGENT_GUIDE.md - Complete operational guide optimized for AI agents (READ THIS FIRST)
2. RUNBOOK.md - Detailed user guide with examples
3. README.md - Project overview
4. config/config.yaml - Configuration (keywords, detection parameters)

PROJECT STRUCTURE:
fedspeak/          # Source code (analyzer, detector, alerter, fetcher, extractor)
config/            # Configuration files
data/              # Downloaded and processed documents
results/           # Generated alerts and visualizations
tests/             # Unit tests (68 tests, all passing)

YOUR TASK:
1. Read AGENT_GUIDE.md completely to understand operational procedures
2. Execute the Environment Check Protocol to verify system state
3. Based on current state, determine and execute appropriate action:
   - If no data exists: Run complete pipeline on 2021 test case
   - If data exists: Validate results and provide status report
4. Report findings with specific file paths and validation results

IMPORTANT:
- Follow protocols in AGENT_GUIDE.md (includes state detection, validation, error handling)
- Verify each step succeeded before proceeding to next
- The 2021 corpus should detect "transitory" removal on December 15, 2021 (known test case)
- Do not modify core code without explicit instruction

START BY: Reading AGENT_GUIDE.md and executing the Environment Check Protocol.
