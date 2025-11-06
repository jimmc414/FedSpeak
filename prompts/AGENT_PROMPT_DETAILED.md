# Agent Prompt: Detailed Initialization Version

**Copy this entire prompt to provide to a fresh Claude Code instance:**

---

# FedSpeak Project - Fresh Instance Initialization

You are working with **FedSpeak**, an automated Federal Reserve language shift detection system.

## Quick Facts
- **Purpose**: Detects when Fed changes key language in FOMC communications
- **Status**: Production-ready, 68/68 tests passing, ~67% code coverage
- **Capabilities**: 0-day detection lag, 100% validated accuracy, synonym group tracking
- **Tech**: Python 3.8+, pandas, BeautifulSoup, matplotlib, tqdm

## Critical Documentation (Priority Order)
1. **AGENT_GUIDE.md** ← START HERE (AI-agent operational guide with protocols)
2. **RUNBOOK.md** (comprehensive user guide)
3. **README.md** (project overview)
4. **config/config.yaml** (configuration)

## Your Initialization Tasks

### Step 1: Environment Assessment
Read `AGENT_GUIDE.md` and execute the **Environment Check Protocol** to determine system state.

### Step 2: State-Based Action
Based on environment state, execute appropriate protocol:
- **Empty system** → Run Protocol 1-4 (Download 2021 test case → Extract → Analyze → Detect)
- **Partial data** → Resume from last completed stage
- **Complete data** → Execute Protocol 5 (Validate Results)

### Step 3: Validation
- Verify 2021 corpus detects "transitory" removal on December 15, 2021 (known ground truth)
- Check file: `results/alerts/ALERT-20211215-removal-transitory.txt`
- Validate success criteria from AGENT_GUIDE.md

### Step 4: Report
Provide status report including:
- What state you found the system in
- What actions you took
- Validation results (pass/fail with evidence)
- File paths to generated outputs

## Key Commands (from AGENT_GUIDE.md)
```bash
# Test case (2021 - known "transitory" shift)
python -m fedspeak.cli download --start-date 2021-01-01 --end-date 2021-12-31 --statements-only
python -m fedspeak.cli extract
python -m fedspeak.cli analyze
python -m fedspeak.cli detect

# Validate
pytest tests/ -v  # Should pass 68/68
```

## Important
- Follow protocols in AGENT_GUIDE.md (includes validation & error handling)
- Verify each step before proceeding
- Do not modify core code unless explicitly requested
- The system has synonym support (tracks word groups like "transitory" + "transient" + "temporary")

**BEGIN BY**: Reading AGENT_GUIDE.md completely, then executing the Environment Check Protocol.
