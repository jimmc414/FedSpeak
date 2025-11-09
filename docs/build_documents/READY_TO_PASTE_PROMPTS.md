# FedSpeak: Ready-to-Paste Phase Prompts

This document contains ready-to-paste prompts for starting each phase of the FedSpeak implementation.

---

## How to Use These Prompts

**Simple 3-Step Process:**

1. **Scroll** to the phase you're starting
2. **Copy** the entire prompt block (everything in the code fence)
3. **Paste** into Claude Code to begin the phase

That's it! The prompt includes all necessary context and instructions.

---

## Phase 1: Pre-Implementation Setup & Environment

```
Please implement Phase 1 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_0_COMPLETION.md (Research & Analysis phase - verify COMPREHENSIVE_ANALYSIS_REPORT.md exists and prototypes are validated)
3. Review @IMPLEMENTATION_PLAN.md Phase 1 section:
   - Environment Setup (Development & Production)
   - Data Access Verification
   - Code Review (prototypes/improved_detection.py)
   - Stakeholder Alignment
   - Documentation Review

Planning:
4. Create comprehensive TodoWrite list for all Phase 1 tasks
5. Present execution plan for approval including:
   - High-level approach for environment setup
   - Key deliverables (configured environments, verified data access, approvals obtained)
   - Potential challenges (server access, stakeholder availability)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Verify each environment component as configured
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_1_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - All environments accessible
    - All prerequisite documents read
    - Stakeholder approvals obtained
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 1 status as "✅ Complete"
    - Update "Overall Progress" to "2/9 phases complete (22%)"
    - Update "Current Phase" to "Phase 1 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 2 (Core Code Migration & Hardening)
```

---

## Phase 2: Core Code Migration & Hardening

```
Please implement Phase 2 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_1_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 2 section:
   - Code Migration (prototype → production structure)
   - Error Handling (try/except blocks, custom exceptions)
   - Logging Implementation (structured JSON logging)
   - Configuration Management (YAML config, secrets management)
   - Code Quality (pylint, type hints)

Planning:
4. Create comprehensive TodoWrite list for all Phase 2 tasks
5. Present execution plan for approval including:
   - High-level approach for code refactoring
   - Key deliverables (src/core/detector.py, config files, logging setup)
   - Potential challenges (maintaining performance while adding error handling)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Test code quality after each major refactor
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_2_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - Code passes linting (>8.0 score)
    - All error paths covered
    - Logging outputs parseable JSON
    - Configuration loads from YAML
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 2 status as "✅ Complete"
    - Update "Overall Progress" to "3/9 phases complete (33%)"
    - Update "Current Phase" to "Phase 2 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 3 (Testing & Production Deployment)
```

---

## Phase 3: Testing & Production Deployment

```
Please implement Phase 3 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_2_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 3 section:
   - Unit Tests (test_detector.py, 2021 critical cases)
   - Integration Tests (full pipeline testing)
   - Regression Tests (130 ground truth shifts)
   - Production Deployment (server setup, directory structure)
   - Systemd Service Setup (service file, monitoring)
   - Monitoring Infrastructure (Prometheus metrics)

Planning:
4. Create comprehensive TodoWrite list for all Phase 3 tasks
5. Present execution plan for approval including:
   - High-level approach for test suite development
   - Key deliverables (tests/, systemd service, production deployment)
   - Potential challenges (production server access, achieving >80% coverage)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_3_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - All tests passing (pytest)
    - Code coverage >80%
    - Prospective test replicated: 100% on 2021
    - Service runs on production server
    - Monitoring metrics accessible
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 3 status as "✅ Complete"
    - Update "Overall Progress" to "4/9 phases complete (44%)"
    - Update "Current Phase" to "Phase 3 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 4 (Real-Time Monitoring & Alert Distribution)
```

---

## Phase 4: Real-Time Monitoring & Alert Distribution

```
Please implement Phase 4 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_3_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 4 section:
   - FOMC Statement Fetcher (RSS feed monitoring)
   - Automated Detection Trigger (monitoring loop)
   - Alert Data Structure (Alert dataclass)
   - Alert Routing Logic (high/medium/low confidence)
   - Email Alerts (SMTP configuration, templates)
   - Dashboard (Flask/FastAPI web interface)
   - Alert Deduplication

Planning:
4. Create comprehensive TodoWrite list for all Phase 4 tasks
5. Present execution plan for approval including:
   - High-level approach for real-time monitoring
   - Key deliverables (src/fetcher/, src/monitor.py, src/alerter/, dashboard)
   - Potential challenges (RSS feed parsing, email delivery testing)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_4_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - RSS feed monitored successfully
    - New statements downloaded automatically
    - Detection runs on new statements
    - High-confidence alerts sent via email within 5 minutes
    - Dashboard shows recent alerts
    - No duplicate alerts sent
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 4 status as "✅ Complete"
    - Update "Overall Progress" to "5/9 phases complete (56%)"
    - Update "Current Phase" to "Phase 4 Complete ✅ - Tier 1 COMPLETE"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 5 (Market Data Integration) OR Phase 9 (Documentation) if stopping at Tier 1
```

---

## Phase 5: Market Data Integration

```
Please implement Phase 5 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_4_COMPLETION.md to confirm previous phase complete (Tier 1 operational)
3. Review @IMPLEMENTATION_PLAN.md Phase 5 section:
   - API Provider Selection (FRED, Alpha Vantage, IEX Cloud)
   - API Integration (MarketDataFetcher class)
   - Historical Data Download (2008-2025 Treasury yields, VIX, S&P 500)
   - API Error Handling (rate limits, downtime, caching)
   - Market Validation Logic (significance scoring 0-1)
   - Backtesting (validate on 130 ground truth shifts)

Planning:
4. Create comprehensive TodoWrite list for all Phase 5 tasks
5. Present execution plan for approval including:
   - High-level approach for market data integration
   - Key deliverables (src/external/market_data.py, src/validation/market_validator.py, data/market/)
   - Potential challenges (API rate limits, data quality)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_5_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - API integration functional
    - Historical data downloaded and validated
    - Market reaction score calculated
    - Backtesting shows +5-10% precision improvement
    - False positive rate reduced
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 5 status as "✅ Complete"
    - Update "Overall Progress" to "6/9 phases complete (67%)"
    - Update "Current Phase" to "Phase 5 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 6 (Media Coverage & Multi-Signal Validation)
```

---

## Phase 6: Media Coverage & Multi-Signal Validation

```
Please implement Phase 6 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_5_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 6 section:
   - Media API Provider Selection (GDELT, NewsAPI, Bing News)
   - Media API Integration (MediaCoverageFetcher class)
   - Sentiment Analysis (FinBERT or API-provided)
   - Media Validation Logic (significance scoring)
   - Multi-Signal Validation (detection 0.5 + market 0.3 + media 0.2)
   - Integration Testing (full pipeline end-to-end)
   - Threshold Tuning (optimize for 65-70% precision)
   - Documentation (threshold rationale, tuning guide)

Planning:
4. Create comprehensive TodoWrite list for all Phase 6 tasks
5. Present execution plan for approval including:
   - High-level approach for media coverage analysis
   - Key deliverables (src/external/media_coverage.py, src/validation/media_validator.py, updated alerter)
   - Potential challenges (API costs, sentiment analysis accuracy)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_6_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - Media API functional
    - Multi-signal validation working
    - Precision increased to 65-70% (from 55%)
    - Recall maintained at ~16%
    - Full pipeline completes in <10 seconds
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 6 status as "✅ Complete"
    - Update "Overall Progress" to "7/9 phases complete (78%)"
    - Update "Current Phase" to "Phase 6 Complete ✅ - Tier 2 COMPLETE"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 7 (Word2Vec Dashboard) OR Phase 9 (Documentation) if stopping at Tier 2
```

---

## Phase 7: Word2Vec Exploration Dashboard

```
Please implement Phase 7 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_4_COMPLETION.md (Tier 1) OR @docs/PHASE_6_COMPLETION.md (Tier 2 recommended) to confirm prerequisites
3. Review @IMPLEMENTATION_PLAN.md Phase 7 section:
   - Word2Vec Model Integration (from prototypes/fed_word2vec.model)
   - REST API (FastAPI/Flask endpoints for similarity queries)
   - Frontend Dashboard (search, results table, visualizations)
   - Deployment (hosting, access control)

Planning:
4. Create comprehensive TodoWrite list for all Phase 7 tasks
5. Present execution plan for approval including:
   - High-level approach for dashboard development
   - Key deliverables (src/exploration/word2vec_service.py, API, frontend dashboard)
   - Potential challenges (frontend framework choice, API performance)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_7_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - API endpoints functional
    - Queries return results in <500ms
    - Dashboard accessible via browser
    - All features functional
    - Responsive design
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 7 status as "✅ Complete"
    - Update "Overall Progress" to "8/9 phases complete (89%)"
    - Update "Current Phase" to "Phase 7 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 8 (MILA Framework & Visualizations)
```

---

## Phase 8: MILA Framework & Visualizations

```
Please implement Phase 8 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @docs/PHASE_7_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 8 section:
   - LLM Provider Selection (Claude 3.5 Sonnet recommended)
   - LLM API Integration (MILAAnalyzer for stance analysis)
   - Caching & Cost Control (budget limits, rate limiting)
   - Explainability Dashboard (stance visualization, key phrases)
   - Visualization Suite (term timelines, shift history, diff view)
   - Testing (LLM accuracy validation, dashboard performance)
   - User Training (1-hour session, feedback collection)

Planning:
4. Create comprehensive TodoWrite list for all Phase 8 tasks
5. Present execution plan for approval including:
   - High-level approach for LLM integration and visualizations
   - Key deliverables (src/explainability/mila_analyzer.py, dashboards, viz suite)
   - Potential challenges (LLM prompt engineering, cost control)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_8_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - LLM integration functional
    - Stance analysis accurate (validated by analysts)
    - Cost under control (<$500/month)
    - All dashboards and visualizations functional
    - Analyst adoption >80%
    - User feedback ≥4/5
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 8 status as "✅ Complete"
    - Update "Overall Progress" to "9/9 phases complete (100%)"
    - Update "Current Phase" to "Phase 8 Complete ✅ - Tier 3 COMPLETE"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 9 (Documentation & Production Handoff)
```

---

## Phase 9: Documentation & Production Handoff

```
Please implement Phase 9 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @docs/QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from the most recent tier completion:
   - @docs/PHASE_4_COMPLETION.md (if Tier 1 only)
   - @docs/PHASE_6_COMPLETION.md (if Tier 1+2)
   - @docs/PHASE_8_COMPLETION.md (if all tiers)
3. Review @IMPLEMENTATION_PLAN.md Phase 9 section:
   - Production Runbook (deployment, service management, troubleshooting)
   - User Guide (for analysts - alert interpretation, dashboard usage)
   - API Documentation (if applicable)
   - Training (1-hour session, demos, Q&A)
   - Final Testing (unit, integration, prospective validation, UAT)
   - Sign-Off (developer, QA, ops, product owner)

Planning:
4. Create comprehensive TodoWrite list for all Phase 9 tasks
5. Present execution plan for approval including:
   - High-level approach for documentation and handoff
   - Key deliverables (docs/PRODUCTION_RUNBOOK.md, docs/USER_GUIDE.md, training materials)
   - Potential challenges (scheduling training, obtaining all sign-offs)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Ensure all documentation is comprehensive and tested
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_9_COMPLETION.md from @docs/PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist:
    - All documentation complete and reviewed
    - Training conducted, positive feedback
    - All tests passing
    - All sign-offs obtained
    - System operational and monitored
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 9 status as "✅ Complete"
    - Update "Overall Progress" to "10/10 phases complete (100%)" (includes Phase 0)
    - Update "Current Phase" to "PROJECT COMPLETE ✅"
12. Clear TodoWrite list
13. Summarize entire project accomplishments:
    - Total investment and ROI
    - Key metrics achieved (precision, recall, latency)
    - All deliverables produced
    - Production system operational
    - Next steps for ongoing monitoring and maintenance
```

---

## Notes

### Phase Dependencies

- **Phase 1-4**: Sequential (Tier 1)
- **Phase 5-6**: Require Phase 4 complete (Tier 2)
- **Phase 7-8**: Require Phase 4 complete, Phase 6 recommended (Tier 3)
- **Phase 9**: Requires at least one complete tier

### Mid-Phase Compaction

If you need to compact **before** completing a phase:

1. Use `@docs/MID_PHASE_COMPACTION_GUIDE.md` to create a checkpoint
2. Use the **Mid-Phase Resume Prompt** from `@docs/COMPACTION_DECISION_TREE.md`
3. Do NOT use these ready-to-paste prompts (they're for starting fresh phases)

### Customization

Feel free to modify these prompts based on:
- Your specific development environment
- Available resources
- Timeline adjustments
- Tier selection (1, 1+2, or all 3)

---

*Generated for FedSpeak Phase-Based Workflow System v2.0*
