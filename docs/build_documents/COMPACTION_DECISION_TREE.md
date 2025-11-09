# Compaction Decision Tree & Resume Prompts

## 10-Second Decision: Which Process?

```
Need to compact?
       |
       v
   Is current phase COMPLETE?
   (All tasks marked [x])
       |
       +-- YES --> PHASE COMPLETE COMPACTION
       |           (Create completion report)
       |
       +-- NO ---> MID-PHASE COMPACTION
                   (Create checkpoint document)
```

## Quick Reference Table

| Situation | Before Compaction | Document Created | After Compaction |
|-----------|------------------|------------------|------------------|
| **Phase Complete** | All Phase N tasks done [x] | PHASE_N_COMPLETION.md | Start Phase N+1 |
| **Mid-Phase** | Some Phase N tasks still [ ] | PHASE_N_CHECKPOINT_YYYY-MM-DD.md | Resume Phase N |

---

## PHASE COMPLETE COMPACTION

### Before You Compact

**1. Verify phase is complete:**
```bash
# Check all Phase N tasks are marked [x]
grep -A 50 "### Phase N:" IMPLEMENTATION_PLAN.md | grep "\[ \]"
# Should return ZERO results (no unchecked tasks)
```

**2. Create Phase Completion Report:**

Use `docs/PHASE_COMPLETION_TEMPLATE.md` to create `docs/PHASE_N_COMPLETION.md` (replace N with your phase number).

**3. Update IMPLEMENTATION_PLAN.md:**
- Mark Phase N as "✅ Complete"
- Update dashboard progress percentage
- Update "Last Updated" date

**4. Verify using checklist:**

Read and complete `docs/PRE_COMPACTION_CHECKLIST.md`

**5. Ready to compact:**

Tell user: "Phase N complete. Ready to compact. After compaction, use Phase N+1 Start Prompt from COMPACTION_DECISION_TREE.md"

---

### After Compaction: Phase Start Prompt

**User: Copy and paste this prompt after compaction when starting a new phase:**

```
I'm resuming the FedSpeak project after a compaction. The previous phase is complete.

Please do the following:

1. Read docs/QUICKSTART_AFTER_COMPACTION.md to orient yourself

2. Verify the previous phase completion:
   - Read docs/PHASE_[N]_COMPLETION.md (replace [N] with the last completed phase number)
   - Confirm all deliverables are present

3. Review the next phase in IMPLEMENTATION_PLAN.md:
   - Read the full "Phase [N+1]" section
   - Understand objectives, tasks, and success criteria

4. Create a TodoWrite list for Phase [N+1] based on the tasks

5. Begin implementation:
   - Mark the first task as in_progress
   - Start working through the tasks systematically
   - Update IMPLEMENTATION_PLAN.md as you complete each task (mark [x])
   - Keep TodoWrite list updated throughout

6. Continue until phase complete or context requires compaction

Remember:
- Update IMPLEMENTATION_PLAN.md continuously (not at end)
- Only ONE task in_progress at a time in TodoWrite
- Mark tasks complete immediately when done
- Use COMPACTION_DECISION_TREE.md when ready to compact again
```

---

## MID-PHASE COMPACTION

### Before You Compact

**1. Verify this is mid-phase:**
```bash
# Check Phase N still has unchecked tasks
grep -A 50 "### Phase N:" IMPLEMENTATION_PLAN.md | grep "\[ \]"
# Should return REMAINING tasks (unchecked [ ])
```

**2. Create Checkpoint Document:**

Use `docs/MID_PHASE_COMPACTION_GUIDE.md` to create `docs/PHASE_N_CHECKPOINT_YYYY-MM-DD.md` (replace N with phase number and YYYY-MM-DD with today's date).

Include:
- Which task you're currently working on
- Files you've modified (with brief status)
- Code snippets showing partial work
- Exact next 3-5 steps
- Any open questions or blockers

**3. Update IMPLEMENTATION_PLAN.md:**
- Mark completed tasks as [x]
- Keep remaining tasks as [ ]
- Add comment to Phase N: `<!-- See PHASE_N_CHECKPOINT_YYYY-MM-DD.md -->`
- Update dashboard to show "Phase N In Progress (X%)"
- Update "Last Updated" date

**4. Ready to compact:**

Tell user: "Phase N checkpoint created. Ready to compact mid-phase. After compaction, use Mid-Phase Resume Prompt from COMPACTION_DECISION_TREE.md"

---

### After Compaction: Mid-Phase Resume Prompt

**User: Copy and paste this prompt after mid-phase compaction:**

```
I'm resuming the FedSpeak project after a mid-phase compaction.

Please do the following:

1. Read docs/QUICKSTART_AFTER_COMPACTION.md to orient yourself

2. Read the checkpoint document:
   - Find and read docs/PHASE_[N]_CHECKPOINT_YYYY-MM-DD.md (most recent)
   - Pay close attention to:
     * Current Task section
     * Files Modified section
     * Next Immediate Steps section

3. Review the current phase in IMPLEMENTATION_PLAN.md:
   - Read the full "Phase [N]" section
   - Note which tasks are [x] complete vs [ ] remaining

4. Create a TodoWrite list for the REMAINING Phase [N] tasks

5. Resume work:
   - Start from "Next Immediate Steps" in the checkpoint
   - Continue marking tasks [x] in IMPLEMENTATION_PLAN.md as you complete them
   - Keep TodoWrite updated throughout

6. Continue Phase [N] until complete, then use PHASE COMPLETE process

Remember:
- This is continuing Phase [N], NOT starting a new phase
- Update IMPLEMENTATION_PLAN.md continuously
- When Phase [N] is fully complete, use PHASE COMPLETE COMPACTION process
```

---

## Which Prompt to Use?

After any compaction, check the most recent document in `docs/`:

```bash
ls -lt docs/PHASE_*.md | head -1
```

- If filename is **PHASE_N_COMPLETION.md** → Use "Phase Start Prompt"
- If filename is **PHASE_N_CHECKPOINT_YYYY-MM-DD.md** → Use "Mid-Phase Resume Prompt"

---

*This document is STATIC - never update it. These prompts work for all phases.*
