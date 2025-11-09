# Pre-Compaction Checklist (Phase Complete)

## Use This When

You've completed all tasks for a phase and are ready to compact BEFORE starting the next phase.

If you're compacting MID-PHASE (phase not complete), use `MID_PHASE_COMPACTION_GUIDE.md` instead.

---

## Verification Steps

### 1. Phase Completion Verification

```bash
# Verify all tasks for current phase are marked [x]
grep -A 50 "### Phase N:" IMPLEMENTATION_PLAN.md

# Should see ALL tasks with [x], NONE with [ ]
```

**Manual Check**:
- [ ] All Phase N tasks marked [x] in IMPLEMENTATION_PLAN.md
- [ ] No in-progress work left incomplete
- [ ] No uncommitted code changes (unless intentional)

### 2. Deliverables Verification

**For Phase N, verify all expected deliverables exist**:

```bash
# Check files mentioned in Phase N "Files to Modify" section exist
ls -la [files from Phase N]

# Verify tests pass (if applicable)
pytest tests/

# Quick functionality check
python -c "import [relevant module]; print('OK')"
```

**Manual Check**:
- [ ] All files mentioned in Phase N exist and are modified
- [ ] Tests pass (or are updated if test changes expected)
- [ ] Basic functionality verified
- [ ] No obvious errors in recent work

### 3. Documentation Created

**Create Phase Completion Report**:
- [ ] Created `docs/PHASE_N_COMPLETION.md` from PHASE_COMPLETION_TEMPLATE.md
- [ ] Executive Summary written
- [ ] All deliverables listed with descriptions
- [ ] Verification commands included
- [ ] Next steps/phase preview included
- [ ] Key decisions documented

### 4. Implementation Plan Updated

**Update IMPLEMENTATION_PLAN.md**:
- [ ] Phase N status changed to "✅ Complete"
- [ ] Dashboard shows Phase N complete
- [ ] Overall progress percentage updated
- [ ] "Last Updated" date is today
- [ ] Next phase (N+1) is clearly marked as next

```bash
# Verify dashboard updated
head -20 IMPLEMENTATION_PLAN.md

# Should show:
# - Current Phase: Phase N+1
# - Phase N listed under "Completed Work"
```

### 5. Ready to Compact

**Final verification**:
- [ ] Read PHASE_N_COMPLETION.md - does it make sense?
- [ ] User can use this document to understand what was accomplished
- [ ] Clear what Phase N+1 should do
- [ ] No confusion about current state

### 6. Inform User

Tell user:

```
Phase [N] complete and documented. Verification checklist passed.

Ready to compact.

After compaction, use the "Phase Start Prompt" from docs/COMPACTION_DECISION_TREE.md to begin Phase [N+1].
```

---

## If Checklist Fails

If any item above fails:
1. **Complete remaining work** before marking phase complete
2. **Create missing documentation**
3. **Fix failing tests** or document why they're expected to fail
4. **Update IMPLEMENTATION_PLAN.md** to reflect reality

If you realize the phase isn't actually complete:
- Use **MID_PHASE_COMPACTION_GUIDE.md** instead
- Create a checkpoint rather than completion report

---

*This document is STATIC - use it before every phase-complete compaction.*
