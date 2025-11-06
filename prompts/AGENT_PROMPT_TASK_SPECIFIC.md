# Agent Prompt: Task-Specific Template

**Instructions: Replace [TASK DESCRIPTION] with your specific goal, then copy to Claude Code instance**

---

You are working with FedSpeak, a Federal Reserve language shift detector.

READ FIRST: AGENT_GUIDE.md (complete operational guide for AI agents)

YOUR SPECIFIC TASK:
[TASK DESCRIPTION - Replace with one of these or your own:]
- "Validate the system works by running the 2021 test case"
- "Download the last 3 months of Fed documents and detect any new shifts"
- "Add a new keyword 'soft landing' and analyze the 2023-2024 corpus"
- "Generate a report of all detected shifts in the full historical corpus"

PROCEDURE:
1. Read AGENT_GUIDE.md Section: [relevant section]
2. Execute Environment Check Protocol
3. Follow the appropriate Protocol from the guide
4. Validate results and provide detailed report with file paths

The system is production-ready. Follow validation protocols to ensure success.

---

## Example Tasks for Reference

### Task 1: Validate System
```
YOUR SPECIFIC TASK:
Validate the system works by running the 2021 test case. Expected result: Detection of "transitory" removal on December 15, 2021.

PROCEDURE:
1. Read AGENT_GUIDE.md Protocol 1-4
2. Execute complete pipeline for 2021
3. Validate alert exists at results/alerts/ALERT-20211215-removal-transitory.txt
4. Run pytest tests/ to verify 68/68 passing
```

### Task 2: Recent Monitoring
```
YOUR SPECIFIC TASK:
Download the last 3 months of Fed documents and detect any new language shifts.

PROCEDURE:
1. Read AGENT_GUIDE.md Protocol 7 (Update Detection)
2. Calculate 90-day date range
3. Execute download, extract, analyze, detect
4. Report any new shifts found with alert file paths
```

### Task 3: Add Custom Keyword
```
YOUR SPECIFIC TASK:
Add a new keyword "soft landing" with synonyms ["smooth transition", "gradual adjustment"] and analyze the 2023-2024 corpus.

PROCEDURE:
1. Read AGENT_GUIDE.md Configuration Adjustments section
2. Add keyword to config/config.yaml
3. Download 2023-2024 corpus
4. Execute extract, analyze, detect
5. Report on "soft landing" usage patterns
```

### Task 4: Full Historical Report
```
YOUR SPECIFIC TASK:
Generate a comprehensive report of all detected shifts in the complete historical corpus (2008-present).

PROCEDURE:
1. Read AGENT_GUIDE.md Protocol 1-4
2. Download full corpus (2008-present, ~60 min)
3. Execute extract, analyze, detect
4. Compile summary of all detected shifts with dates, keywords, and significance
5. Create CSV export of all shifts
```
