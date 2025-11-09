# Phase [N] Checkpoint: [YYYY-MM-DD]

**Phase**: [N] - [Phase Name]
**Checkpoint Date**: [YYYY-MM-DD]
**Phase Status**: 🔄 In Progress ([X]% complete)

---

## Current State Summary

[1-2 sentences describing where you are in this phase]

---

## Current Task

**Task**: [The specific task from IMPLEMENTATION_PLAN.md you're working on NOW]

**Status**: [One of: Starting | Partially Complete | Debugging | Almost Done]

**What's Done**:
- [Specific accomplishment 1]
- [Specific accomplishment 2]

**What's Remaining**:
- [ ] [Next immediate step 1]
- [ ] [Next immediate step 2]
- [ ] [Next immediate step 3]

---

## Files Modified

### `path/to/file1.py`
**Status**: [Modified | New | In Progress]
**Changes**:
- [Specific change 1]
- [Specific change 2]

**Current State**:
```python
# Key code snippet showing current state
[Relevant code that shows what's been done]
```

### `path/to/file2.py`
**Status**: [Modified | New | In Progress]
**Changes**:
- [Specific change 1]

[Repeat for all modified files]

---

## Completed Tasks (This Session)

From IMPLEMENTATION_PLAN.md Phase [N]:
- [x] Task N.1: [Description]
- [x] Task N.2: [Description]
- [x] Task N.3: [Description]

**Progress**: [X] of [Y] Phase [N] tasks complete ([Z]%)

---

## Remaining Tasks (Phase [N])

From IMPLEMENTATION_PLAN.md Phase [N]:
- [ ] Task N.4: [Description] ← **CURRENT TASK**
- [ ] Task N.5: [Description]
- [ ] Task N.6: [Description]

---

## Next Immediate Steps

When resuming, do these steps IN ORDER:

1. **[Immediate Step 1]**
   - [Specific action]
   - Files: `[files to modify]`
   - Expected outcome: [what should happen]

2. **[Immediate Step 2]**
   - [Specific action]
   - Files: `[files to modify]`
   - Expected outcome: [what should happen]

3. **[Immediate Step 3]**
   - [Specific action]
   - Files: `[files to modify]`

4. Continue with remaining Phase [N] tasks in IMPLEMENTATION_PLAN.md

---

## Open Questions / Blockers

**Question 1**: [What needs clarification]
- **Context**: [Why this matters]
- **Options**: [Possible approaches]

**Blocker 1**: [What's blocking progress]
- **Impact**: [What can't proceed]
- **Needs**: [What's required to unblock]

[Delete this section if no questions/blockers]

---

## Verification Commands

To verify current state after resuming:

```bash
# Verify files exist
ls -la [modified files]

# Check git status
git status

# Run tests (may have failures - that's expected mid-phase)
pytest tests/[relevant tests]

# Verify partial functionality
python -c "[basic check that current code runs]"
```

**Expected State**:
- Files [list] should exist and be modified
- Git should show [expected changes]
- Tests: [X passing, Y expected failures (being worked on)]

---

## Context Notes

[Any important context about decisions made, approaches tried, things to remember]

- **Note 1**: [Important context]
- **Note 2**: [Important context]

---

## TodoWrite Snapshot

[Copy your current TodoWrite list here for reference]

```
- [x] completed task 1
- [x] completed task 2
- [ ] in_progress task 3 ← CURRENT
- [ ] pending task 4
- [ ] pending task 5
```

---

## Recovery Instructions

After compaction, use the "Mid-Phase Resume Prompt" from `COMPACTION_DECISION_TREE.md`.

1. Read this checkpoint file completely
2. Review Phase [N] in IMPLEMENTATION_PLAN.md
3. Start from "Next Immediate Steps" above
4. Continue Phase [N] until complete

---

*This is a mid-phase checkpoint. When Phase [N] is complete, create PHASE_[N]_COMPLETION.md and archive this checkpoint.*
