# FedSpeak: Quickstart After Compaction

## 30-Second Emergency Recovery

If you need to resume IMMEDIATELY:

```bash
# 1. Check project status
ls docs/PHASE_*_COMPLETION.md docs/PHASE_*_CHECKPOINT_*.md 2>/dev/null | tail -1

# 2. Read the most recent file shown above
# 3. Resume from "Next Steps" or "Next Immediate Steps" section
```

## 5-Minute Full Recovery

### Step 1: Verify Environment (30 seconds)

```bash
# Verify you're in the FedSpeak project
pwd  # Should show FedSpeak directory
ls -la  # Should see main project files

# Quick status check
git status
python --version  # Verify Python environment
```

### Step 2: Identify Where You Left Off (2 minutes)

```bash
# Find the most recent completion or checkpoint document
ls -lt docs/PHASE_*.md | head -5

# Read the most recent one to understand current state
```

**Two scenarios**:

**A) Latest file is PHASE_N_COMPLETION.md**:
- Phase N is complete
- You need to START Phase N+1
- Go to Step 3A below

**B) Latest file is PHASE_N_CHECKPOINT_YYYY-MM-DD.md**:
- Phase N is IN PROGRESS (interrupted mid-phase)
- You need to RESUME Phase N from checkpoint
- Go to Step 3B below

### Step 3A: Starting New Phase (Phase Complete) (2 minutes)

```bash
# 1. Verify previous phase completion
cat docs/PHASE_N_COMPLETION.md  # Read executive summary

# 2. Review next phase in implementation plan
grep -A 20 "### Phase N+1:" IMPLEMENTATION_PLAN.md

# 3. Ready to start
# User will provide you with Phase N+1 start prompt
```

**Wait for user to provide the phase start prompt from COMPACTION_DECISION_TREE.md**

### Step 3B: Resuming Mid-Phase (Checkpoint Recovery) (2 minutes)

```bash
# 1. Read checkpoint file completely
cat docs/PHASE_N_CHECKPOINT_YYYY-MM-DD.md

# 2. Pay special attention to:
#    - "Current Task" section (what you were working on)
#    - "Files Modified" section (what's changed)
#    - "Next Immediate Steps" section (what to do next)

# 3. Review phase status in implementation plan
grep -A 30 "### Phase N:" IMPLEMENTATION_PLAN.md
```

**Resume from "Next Immediate Steps" in checkpoint**. Continue marking tasks complete in IMPLEMENTATION_PLAN.md as you work.

## Recovery Verification Checklist

Before proceeding with work, verify:

- [ ] You've read either the latest COMPLETION or CHECKPOINT document
- [ ] You understand what phase you're in
- [ ] You know the next 2-3 tasks to work on
- [ ] You've reviewed the relevant section of IMPLEMENTATION_PLAN.md
- [ ] Tests pass: `pytest tests/` (if applicable)

## Emergency Contacts

If you're confused or documents are missing:
1. Check IMPLEMENTATION_PLAN.md - it's the source of truth
2. Read COMPACTION_DECISION_TREE.md for guidance
3. Ask user for clarification

## Key Principles

- **Update IMPLEMENTATION_PLAN.md immediately** as you complete tasks
- **Use TodoWrite** to track tasks during your session
- **Mark ONE task as in_progress** at a time
- **Update completion status [x]** as soon as tasks finish
- **Don't wait** to batch updates - update continuously

---

*This document is STATIC - never update it. It remains the same for all phases.*
