# Agent Prompts Directory

This directory contains ready-to-use prompts for initializing fresh Claude Code instances with the FedSpeak project.

---

## Available Prompts

### 1. AGENT_PROMPT_COMPREHENSIVE.md
**Use when:** You want a balanced, complete initialization prompt.

**Best for:**
- First-time agent initialization
- General project work
- When you want the agent to be autonomous but thorough

**Contains:**
- Full project overview
- Documentation hierarchy
- Clear task priorities
- Important constraints

**Copy-paste ready:** Yes

---

### 2. AGENT_PROMPT_QUICK.md
**Use when:** You need a minimal, fast-start prompt.

**Best for:**
- Experienced agents familiar with the project structure
- Quick validation tasks
- When you trust the agent to explore on its own

**Contains:**
- Minimal context
- Direct pointer to AGENT_GUIDE.md
- Assumes agent will explore

**Copy-paste ready:** Yes

---

### 3. AGENT_PROMPT_TASK_SPECIFIC.md
**Use when:** You have a specific task for the agent to complete.

**Best for:**
- Directed work (not exploration)
- Specific feature additions
- Targeted analysis tasks
- When you want focused execution

**Contains:**
- Template with [TASK DESCRIPTION] placeholder
- Four pre-written example tasks
- Task-specific procedure outlines

**Copy-paste ready:** Requires customization (replace [TASK DESCRIPTION])

**Example tasks included:**
1. Validate system with 2021 test case
2. Monitor recent Fed communications (3 months)
3. Add custom keyword and analyze
4. Generate full historical report

---

### 4. AGENT_PROMPT_DETAILED.md
**Use when:** You want maximum guidance and step-by-step initialization.

**Best for:**
- Complex projects where mistakes are costly
- Training new agents on the system
- Documentation/audit requirements
- When you want explicit validation at each step

**Contains:**
- Comprehensive project facts
- Numbered step-by-step initialization
- Validation criteria
- Expected outputs and file paths
- Key commands reference

**Copy-paste ready:** Yes

---

## Quick Selection Guide

```
┌─ What's your goal?
│
├─ Agent should explore and learn
│  └─ Use: AGENT_PROMPT_COMPREHENSIVE.md
│
├─ Quick test/validation
│  └─ Use: AGENT_PROMPT_QUICK.md
│
├─ Specific task to complete
│  └─ Use: AGENT_PROMPT_TASK_SPECIFIC.md (customize first)
│
└─ Detailed guided execution
   └─ Use: AGENT_PROMPT_DETAILED.md
```

---

## How to Use These Prompts

### Method 1: Direct Copy-Paste
1. Open the appropriate prompt file
2. Copy the entire contents (skip the header "Agent Prompt: ...")
3. Paste into a fresh Claude Code instance
4. The agent will begin execution

### Method 2: Customized Task
1. Open AGENT_PROMPT_TASK_SPECIFIC.md
2. Replace [TASK DESCRIPTION] with your specific goal
3. Optionally customize the PROCEDURE section
4. Copy and paste to Claude Code instance

### Method 3: Hybrid Approach
1. Start with AGENT_PROMPT_COMPREHENSIVE.md
2. Add specific task requirements at the end
3. Paste to Claude Code instance

---

## All Prompts Reference AGENT_GUIDE.md

Every prompt directs the agent to **AGENT_GUIDE.md** as the primary operational reference. This guide contains:

- Environment Check Protocol
- State Detection Protocol
- 7 operational protocols (Download, Extract, Analyze, Detect, Validate, View, Update)
- Decision trees
- Success criteria
- Error handling procedures
- Validation protocols

**Why this matters:** The prompts are intentionally brief because AGENT_GUIDE.md contains all the detailed procedures. This keeps prompts concise while ensuring agents have complete operational knowledge.

---

## Testing Your Prompt

After providing a prompt to a fresh Claude Code instance, verify it's working correctly:

1. **Agent should immediately:**
   - Read AGENT_GUIDE.md
   - Execute Environment Check Protocol
   - Report current system state

2. **Agent should NOT:**
   - Start coding without reading documentation
   - Make assumptions about project structure
   - Skip validation steps

3. **Expected first actions:**
   ```bash
   # Check environment
   python --version
   ls -la | grep -E "fedspeak|config"
   python -c "import pandas, beautifulsoup4"
   ```

4. **Expected output pattern:**
   ```
   === CURRENT STATE ===
   Downloaded documents: X
   Extracted texts: Y
   Metrics: YES/NO
   Alerts: Z
   ====================
   ```

If the agent doesn't follow this pattern, the prompt may need adjustment.

---

## Updating These Prompts

When you update the project, remember to update these prompts if:

- Project structure changes significantly
- Key documentation files are renamed/moved
- Primary workflows change
- Test expectations change (e.g., different number of passing tests)

**Current assumptions in prompts:**
- 68 tests pass (if this changes, update all prompts)
- AGENT_GUIDE.md is the primary operational reference
- 2021 "transitory" removal is the primary test case
- Python 3.8+ requirement
- Project is in production-ready state

---

## Examples of Using These Prompts

### Example 1: New Contributor Validation
```
Scenario: New developer wants to validate the project works
Prompt: AGENT_PROMPT_COMPREHENSIVE.md
Expected result: Agent runs 2021 test case, reports "transitory" detection on Dec 15, 2021
```

### Example 2: Daily Monitoring
```
Scenario: Check for new Fed language shifts in past week
Prompt: AGENT_PROMPT_TASK_SPECIFIC.md
Customization: Change task to "Download last 7 days and detect shifts"
Expected result: Agent downloads recent docs, reports any new shifts
```

### Example 3: Research Task
```
Scenario: Analyze when Fed started using "soft landing" terminology
Prompt: AGENT_PROMPT_TASK_SPECIFIC.md
Customization: Add "soft landing" keyword task
Expected result: Agent adds keyword, analyzes corpus, reports usage timeline
```

### Example 4: Quick Health Check
```
Scenario: Verify project still works after system update
Prompt: AGENT_PROMPT_QUICK.md
Expected result: Agent quickly validates environment, runs tests, confirms 68/68 pass
```

---

## Troubleshooting

### Problem: Agent seems confused or stuck
**Solution:** Use AGENT_PROMPT_DETAILED.md for more explicit guidance

### Problem: Agent skips validation steps
**Solution:** Verify prompt includes "Follow protocols in AGENT_GUIDE.md"

### Problem: Agent modifies code unexpectedly
**Solution:** Add "Do not modify core code without explicit instruction" to prompt

### Problem: Agent doesn't find documentation
**Solution:** Ensure agent has access to repository files, verify paths in prompt

### Problem: Agent asks too many questions
**Solution:** Use AGENT_PROMPT_COMPREHENSIVE.md or add more context to task-specific prompt

---

## Contributing

When creating new prompt variants:

1. Follow the naming convention: `AGENT_PROMPT_[TYPE].md`
2. Include "Copy this entire prompt" instruction at top
3. Reference AGENT_GUIDE.md as primary operational source
4. Add entry to this README.md
5. Test with a fresh Claude Code instance
6. Document expected behavior

---

**Last Updated:** 2025-01-06
**Maintained by:** FedSpeak Project
**Related Documentation:** AGENT_GUIDE.md, RUNBOOK.md
