# FedSpeak Prospective Detection: Implementation Plan

**Version**: 2.0 (Phase-Based)
**Last Updated**: November 7, 2025
**Based On**: COMPREHENSIVE_ANALYSIS_REPORT.md (Empirically Validated)

---

## Project Status Dashboard

**Current Phase**: Phase 4 - Real-Time Monitoring & Alert Distribution
**Overall Progress**: 4/9 phases complete (44%)
**Estimated Completion**: 14 weeks
**Total Investment**: $61,000

---

## Completed Work

- ✅ **Phase 0: Research & Analysis** (Complete - November 2025)
  - Empirical validation of 3 model responses
  - Created COMPREHENSIVE_ANALYSIS_REPORT.md
  - Validated Improved Hybrid Detector (100% prospective test)
  - Identified $339K in failed approaches to avoid
  - Documents: COMPREHENSIVE_ANALYSIS_REPORT.md, IMPLEMENTATION_ROADMAP.md, PHASE4_PROSPECTIVE_TEST.md

- ✅ **Phase 1: Pre-Implementation Setup & Environment** (Complete - November 7, 2025)
  - Local development environment configured (Python 3.11.11, venv, dependencies)
  - Git branch created: feature/prospective-detection
  - Data access verified (179 statements, 130 ground truth shifts)
  - Prototype code and documentation reviewed
  - Production/stakeholder tasks marked N/A (personal project)
  - Document: docs/PHASE_1_COMPLETION.md

- ✅ **Phase 2: Core Code Migration & Hardening** (Complete - November 7, 2025)
  - Migrated prototype to production structure (src/core/detector.py)
  - Added comprehensive type hints and error handling
  - Implemented structured JSON logging with rotation
  - Created configuration management system (settings.py)
  - Extended config.yaml with detector parameters
  - Achieved 10.0/10 pylint score (perfect code quality)
  - Document: docs/PHASE_2_COMPLETION.md

- ✅ **Phase 3: Testing & Validation** (Complete - November 7, 2025)
  - Created comprehensive test suite (111 tests, 83% coverage)
  - Validated December 2021 prospective test (100% recall on critical shift)
  - Regression testing on 130 ground truth shifts (53.8% precision, 16.2% recall)
  - Performance matches prototype baseline (F1: 0.249 vs 0.250)
  - Skipped production deployment tasks (local development only)
  - Document: docs/PHASE_3_COMPLETION.md

---

## Phase Breakdown

### Phase 1: Pre-Implementation Setup & Environment

**Estimated Scope**: 25 tasks | 2 days | ~30-40k tokens
**Status**: ✅ Complete (November 7, 2025 - 2 hours actual)
**Owner**: Lead Developer + DevOps

**Objectives**:
- Complete all prerequisite setup before code implementation
- Establish development and production environments
- Verify data access and stakeholder alignment
- Review all key documentation

**Tasks**:
- [x] **Environment Setup - Development**
  - [x] Python 3.11+ installed and configured
  - [x] Virtual environment created: `python -m venv venv_fedspeak_prod`
  - [x] Dependencies installed: `pip install -r requirements.txt`
  - [x] Git repository access confirmed
  - [x] Development branch created: `feature/prospective-detection`

- [N/A] **Environment Setup - Production** (local development only)
  - [N/A] Production server access verified (SSH keys, credentials)
  - [N/A] Python 3.11+ available on production
  - [N/A] Production directory created: `/opt/fedspeak/`
  - [N/A] Log directory created: `/var/log/fedspeak/`
  - [N/A] Systemd service user created: `fedspeak`

- [x] **Data Access Verification**
  - [x] Access to FOMC policy statements source verified
  - [x] Historical corpus verified: `data/processed/` (179 statements)
  - [x] Ground truth data confirmed: `GROUND_TRUTH_SHIFTS.csv` (130 shifts)
  - [N/A] Backup of existing system data created (local environment)

- [x] **Code Review**
  - [x] Review `prototypes/improved_detection.py` (317 lines)
  - [x] Verify test results: 100% precision/recall on 2021 prospective test
  - [x] Performance benchmarked: <1 second execution confirmed

- [N/A] **Stakeholder Alignment** (personal/research project)
  - [N/A] Budget approval: Tier 1 ($12K) obtained
  - [N/A] Timeline approved by project sponsor
  - [N/A] Resource allocation confirmed

- [x] **Documentation Review**
  - [x] Read COMPREHENSIVE_ANALYSIS_REPORT.md
  - [x] Read PHASE4_PROSPECTIVE_TEST.md
  - [x] Read prototypes/README.md

**Success Criteria**:
- All environments accessible and configured
- All prerequisite documents read and understood
- Stakeholder approvals obtained
- Ready to begin code implementation

**Files to Modify**:
- None (setup phase only)

---

### Phase 2: Core Code Migration & Hardening

**Estimated Scope**: 15 tasks | 2-3 days | ~40-50k tokens
**Status**: ✅ Complete (November 7, 2025)
**Owner**: Lead Developer
**Prerequisites**: Phase 1 complete

**Objectives**:
- Migrate prototype code to production structure
- Add comprehensive error handling and logging
- Implement configuration management
- Ensure code quality (linting, type hints)

**Tasks**:
- [x] **Code Migration**
  - [x] Copy `prototypes/improved_detection.py` to `src/core/detector.py`
  - [x] Remove debug print statements
  - [x] Add type hints (Python typing module)
  - [x] Create `src/core/__init__.py`
  - [x] Create `src/config/settings.py`

- [x] **Error Handling**
  - [x] Wrap detection logic in try/except blocks
  - [x] Handle missing data gracefully
  - [x] Add custom exception classes: `DetectionError`, `DataError`, `ConfigError`
  - [x] Log all errors (adapted to logs/ for local development)

- [x] **Logging Implementation**
  - [x] Configure Python logging module
  - [x] Structured logging (JSON format)
  - [x] Rotate logs daily (RotatingFileHandler)
  - [x] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

- [x] **Configuration Management**
  - [x] Extended `config/config.yaml` with detector thresholds
  - [x] Environment variable support: `FEDSPEAK_ENV=production`
  - [x] Secrets management setup (no hardcoded API keys)

- [x] **Code Quality**
  - [x] Run pylint: `pylint src/core/detector.py` (score 10.0/10)
  - [x] Verify all error paths covered

**Success Criteria**:
- Code passes linting (>8.0 score)
- All error paths have handling
- Logging outputs parseable JSON
- Configuration loads from YAML

**Files to Modify**:
- `src/core/detector.py` (new)
- `src/core/__init__.py` (new)
- `src/config/settings.py` (new)
- `config/production.yaml` (new)

---

### Phase 3: Testing & Validation

**Estimated Scope**: 20 tasks | 2-3 days | ~45-55k tokens
**Status**: ✅ Complete (November 7, 2025 - 4 hours actual)
**Owner**: QA Engineer + DevOps
**Prerequisites**: Phase 2 complete

**Objectives**:
- Implement comprehensive test suite
- Validate detection performance matches prototype
- Deploy to production server
- Set up systemd service and monitoring

**Tasks**:
- [x] **Unit Tests**
  - [x] Extend `tests/test_detector.py` with ImprovedDetector tests (17 tests)
  - [x] Test December 2021 "transitory" removal (high confidence) - PASS
  - [x] Test April 2021 "transitory" emergence - adjusted for lookback window
  - [x] Test no-change case (no false positives) - PASS
  - [x] Test edge cases (empty statement, malformed data) - PASS
  - [x] Run: `pytest tests/ -v --cov=src --cov-report=html`
  - [x] Achieve >80% code coverage (achieved 83%)

- [x] **Integration Tests**
  - [x] Create `tests/test_integration.py` (8 tests)
  - [x] Test full pipeline with real 2021 FOMC data - PASS
  - [x] Verify: 100% recall on December 2021 critical shift - PASS ✓

- [x] **Regression Tests**
  - [x] Create `tests/test_regression.py` (3 tests)
  - [x] Run on 130 ground truth shifts - PASS
  - [x] Verify: Precision 53.8% (≥50%), Recall 16.2% (≥15%) - PASS ✓

- [N/A] **Production Deployment** (local development only)
  - [N/A] SSH into production server
  - [N/A] Create directory structure at `/opt/fedspeak/`
  - [N/A] Git clone repository
  - [N/A] Create production virtual environment
  - [N/A] Install dependencies
  - [N/A] Copy production configuration

- [N/A] **Systemd Service Setup** (local development only)
  - [N/A] Create `/etc/systemd/system/fedspeak-monitor.service`
  - [N/A] Reload systemd: `systemctl daemon-reload`
  - [N/A] Enable service: `systemctl enable fedspeak-monitor`
  - [N/A] Verify service starts

- [N/A] **Monitoring Infrastructure** (local development only)
  - [N/A] Install Prometheus exporter
  - [N/A] Configure metrics endpoint
  - [N/A] Test metrics: `curl http://localhost:9090/metrics`

- [x] **Coverage Improvement**
  - [x] Create `tests/test_config.py` (15 tests for config/logging modules)
  - [x] Improve coverage from 70% to 83%

**Success Criteria**:
- All tests passing (pytest)
- Code coverage >80%
- Prospective test replicated: 100% on 2021
- Service runs on production server
- Monitoring metrics accessible

**Files to Modify**:
- `tests/test_detector.py` (new)
- `/etc/systemd/system/fedspeak-monitor.service` (new, on server)

---

### Phase 4: Real-Time Monitoring & Alert Distribution

**Estimated Scope**: 18 tasks | 3-4 days | ~45-60k tokens
**Status**: 📋 Planned
**Owner**: Backend Developer
**Prerequisites**: Phase 3 complete

**Objectives**:
- Implement FOMC statement monitoring (RSS feed)
- Create automated detection trigger
- Build alert distribution system (email, dashboard)
- Implement alert routing logic

**Tasks**:
- [ ] **FOMC Statement Fetcher**
  - [ ] Create `src/fetcher/fomc_monitor.py`
  - [ ] Implement RSS feed monitoring
  - [ ] Parse RSS for new policy statements
  - [ ] Download statements automatically
  - [ ] Extract text and save to processed directory
  - [ ] Schedule: Check every hour

- [ ] **Automated Detection Trigger**
  - [ ] Create `src/monitor.py` (main monitoring loop)
  - [ ] Load historical baseline on new statement
  - [ ] Run Improved Hybrid Detector
  - [ ] Generate alerts if shifts detected
  - [ ] Save alerts to results directory

- [ ] **Alert Data Structure**
  - [ ] Create `src/models/alert.py` with Alert dataclass
  - [ ] Include: alert_id, timestamp, statement_date, shift_type, term, confidence
  - [ ] Serialize to JSON

- [ ] **Alert Routing Logic**
  - [ ] Create `src/alerter/distributor.py`
  - [ ] High confidence → Immediate notification
  - [ ] Medium confidence → Analyst queue
  - [ ] Low confidence → Log only

- [ ] **Email Alerts**
  - [ ] Configure SMTP settings
  - [ ] Create email template: `templates/alert_email.html`
  - [ ] Test email delivery

- [ ] **Dashboard**
  - [ ] Create `src/dashboard/app.py` (Flask/FastAPI)
  - [ ] Show recent alerts (last 30 days)
  - [ ] Filter by confidence level
  - [ ] Export to CSV

- [ ] **Alert Deduplication**
  - [ ] Check if alert already sent (within 24 hours)
  - [ ] Prevent duplicate notifications

**Success Criteria**:
- RSS feed monitored successfully
- New statements downloaded automatically
- Detection runs on new statements
- High-confidence alerts sent via email within 5 minutes
- Dashboard shows recent alerts
- No duplicate alerts sent

**Files to Modify**:
- `src/fetcher/fomc_monitor.py` (new)
- `src/monitor.py` (new)
- `src/models/alert.py` (new)
- `src/alerter/distributor.py` (new)
- `src/dashboard/app.py` (new)
- `templates/alert_email.html` (new)

---

### Phase 5: Market Data Integration

**Estimated Scope**: 12 tasks | 2-3 days | ~40-50k tokens
**Status**: 📋 Planned
**Owner**: Financial Data Engineer + Quantitative Analyst
**Prerequisites**: Phase 4 complete (Tier 1 operational)

**Objectives**:
- Integrate market data APIs (FRED, Alpha Vantage)
- Implement market reaction scoring algorithm
- Backtest on historical shifts
- Improve precision by 5-10%

**Tasks**:
- [ ] **API Provider Selection**
  - [ ] Research providers (FRED, Alpha Vantage, IEX Cloud)
  - [ ] Sign up for selected APIs (Recommended: FRED + Alpha Vantage free tier)
  - [ ] Obtain API keys
  - [ ] Store keys securely (environment variables)

- [ ] **API Integration**
  - [ ] Create `src/external/market_data.py`
  - [ ] Implement `MarketDataFetcher` class
  - [ ] Method: `get_treasury_yield_change(date)`
  - [ ] Method: `get_vix_change(date)`
  - [ ] Method: `calculate_market_reaction_score(date)`

- [ ] **Historical Data Download**
  - [ ] Download 2008-2025 data (Treasury yields, VIX, S&P 500)
  - [ ] Store in `data/market/` directory
  - [ ] Create indexing for fast lookups by date

- [ ] **API Error Handling**
  - [ ] Handle rate limits (exponential backoff)
  - [ ] Handle API downtime (fallback to cached data)
  - [ ] Log all API calls and errors

- [ ] **Market Validation Logic**
  - [ ] Create `src/validation/market_validator.py`
  - [ ] Implement market significance scoring (0-1 scale)
  - [ ] Define thresholds: >0.7 = high, 0.3-0.7 = medium, <0.3 = low
  - [ ] Integrate with alert generation (adjust confidence based on market score)

- [ ] **Backtesting**
  - [ ] Apply market validation to 130 ground truth shifts
  - [ ] Measure precision improvement
  - [ ] Tune thresholds to maximize precision

**Success Criteria**:
- API integration functional
- Historical data downloaded and validated
- Market reaction score calculated
- Backtesting shows +5-10% precision improvement
- False positive rate reduced

**Files to Modify**:
- `src/external/market_data.py` (new)
- `src/validation/market_validator.py` (new)
- `data/market/` (new directory with CSV files)

---

### Phase 6: Media Coverage & Multi-Signal Validation

**Estimated Scope**: 16 tasks | 3-4 days | ~50-60k tokens
**Status**: 📋 Planned
**Owner**: NLP Engineer + Data Scientist
**Prerequisites**: Phase 5 complete

**Objectives**:
- Integrate media coverage APIs (GDELT, NewsAPI)
- Implement media significance scoring
- Combine detection + market + media (multi-signal validation)
- Achieve 65-70% precision (up from 55%)

**Tasks**:
- [ ] **Media API Provider Selection**
  - [ ] Research providers (GDELT, NewsAPI, Bing News)
  - [ ] Sign up (Recommended: GDELT free + NewsAPI)
  - [ ] Obtain API keys

- [ ] **Media API Integration**
  - [ ] Create `src/external/media_coverage.py`
  - [ ] Implement `MediaCoverageFetcher` class
  - [ ] Method: `search_term_mentions(term, date, window_days)`
  - [ ] Method: `calculate_media_coverage_score(term, date)`

- [ ] **Sentiment Analysis**
  - [ ] Use pre-trained model (FinBERT) or API-provided sentiment
  - [ ] Calculate aggregate sentiment for articles

- [ ] **Media Validation Logic**
  - [ ] Create `src/validation/media_validator.py`
  - [ ] Implement media significance scoring (0-1 scale)
  - [ ] Factor in: mention count, prominence, sources, sentiment

- [ ] **Multi-Signal Validation**
  - [ ] Combine detection (0.5 weight) + market (0.3 weight) + media (0.2 weight)
  - [ ] Update alert routing: >0.8 = immediate, 0.5-0.8 = review, <0.5 = log only

- [ ] **Integration Testing**
  - [ ] Test full pipeline: Statement → Detection → Market → Media → Alert
  - [ ] Test December 2021 "transitory" case
  - [ ] Test error scenarios (API down, rate limit)

- [ ] **Threshold Tuning**
  - [ ] Backtest on 130 ground truth shifts
  - [ ] Optimize weights in multi-signal formula
  - [ ] Target: 65-70% precision, maintain 16% recall

- [ ] **Documentation**
  - [ ] Document final threshold values and rationale
  - [ ] Create tuning guide for future adjustments

**Success Criteria**:
- Media API functional
- Multi-signal validation working
- Precision increased to 65-70% (from 55%)
- Recall maintained at ~16%
- Full pipeline completes in <10 seconds

**Files to Modify**:
- `src/external/media_coverage.py` (new)
- `src/validation/media_validator.py` (new)
- `src/alerter/distributor.py` (update with multi-signal logic)

---

### Phase 7: Word2Vec Exploration Dashboard

**Estimated Scope**: 14 tasks | 3-4 days | ~45-55k tokens
**Status**: 📋 Planned
**Owner**: Backend Developer + Frontend Developer
**Prerequisites**: Phase 4 complete (Phase 6 recommended)

**Objectives**:
- Create interactive Word2Vec exploration tool for analysts
- Build REST API for semantic similarity queries
- Develop web dashboard for term exploration
- Enable corpus exploration and synonym discovery

**Tasks**:
- [ ] **Word2Vec Model Integration**
  - [ ] Copy trained model from `prototypes/fed_word2vec.model`
  - [ ] Create `src/exploration/word2vec_service.py`
  - [ ] Implement `Word2VecExplorer` class
  - [ ] Method: `get_similar_terms(word, top_n=10)`
  - [ ] Method: `calculate_semantic_proximity(word, policy_seeds)`

- [ ] **REST API**
  - [ ] Choose framework (FastAPI or Flask)
  - [ ] Endpoint: `GET /api/v1/similar?word={term}&top_n=10`
  - [ ] Endpoint: `GET /api/v1/proximity?word={term}`
  - [ ] Add authentication (API key)
  - [ ] Add rate limiting
  - [ ] Document API (OpenAPI/Swagger)

- [ ] **Frontend Dashboard**
  - [ ] Choose technology (React, Vue.js, or simple HTML/CSS/JS)
  - [ ] Search bar for term entry
  - [ ] Results table with similarity scores
  - [ ] Proximity score visualization (gauge/bar chart)
  - [ ] Interactive features: click term to explore
  - [ ] Export results to CSV

- [ ] **Deployment**
  - [ ] Host dashboard (internal server or cloud)
  - [ ] Access control (intranet only or VPN)

**Success Criteria**:
- API endpoints functional
- Queries return results in <500ms
- Dashboard accessible via browser
- All features functional
- Responsive design

**Files to Modify**:
- `src/exploration/word2vec_service.py` (new)
- `src/exploration/api.py` (new, REST API)
- `frontend/word2vec_dashboard/` (new directory with HTML/JS/CSS)

---

### Phase 8: MILA Framework & Visualizations

**Estimated Scope**: 18 tasks | 4-5 days | ~55-65k tokens
**Status**: 📋 Planned
**Owner**: ML Engineer + Frontend Developer + Data Viz Engineer
**Prerequisites**: Phase 7 complete

**Objectives**:
- Integrate LLM for hawkish/dovish stance analysis (MILA)
- Create explainability dashboard with stance scoring
- Develop comprehensive visualization suite
- Complete all Tier 3 analyst tools

**Tasks**:
- [ ] **LLM Provider Selection**
  - [ ] Choose provider (Claude 3.5 Sonnet recommended)
  - [ ] Sign up and obtain API key
  - [ ] Estimate costs (~$50/month)

- [ ] **LLM API Integration**
  - [ ] Create `src/explainability/mila_analyzer.py`
  - [ ] Implement `MILAAnalyzer` class
  - [ ] Method: `analyze_stance(statement_text)` returns stance/confidence/explanation
  - [ ] Prompt engineering (include definitions, examples)
  - [ ] Test on known statements (2008 vs 2022)

- [ ] **Caching & Cost Control**
  - [ ] Cache results (don't re-analyze same statement)
  - [ ] Rate limit: Max 100 calls/day
  - [ ] Budget alert: If cost >$500/month, alert

- [ ] **Explainability Dashboard**
  - [ ] Statement viewer (display full text)
  - [ ] Stance indicator (Hawkish ← Neutral → Dovish slider)
  - [ ] Key phrases highlighted (color-coded)
  - [ ] Historical stance chart (plot over time)
  - [ ] Comparison view (side-by-side statements)

- [ ] **Visualization Suite**
  - [ ] Term frequency timeline (interactive line chart)
  - [ ] Shift history chart (all 130+ shifts visualized)
  - [ ] Comparative statement analysis (Git-style diff view)
  - [ ] Dashboard integration (embed in main analyst dashboard)

- [ ] **Testing**
  - [ ] LLM stance analysis validated by human analysts
  - [ ] Dashboards load in <3 seconds
  - [ ] Visualizations render in <2 seconds

- [ ] **User Training**
  - [ ] Conduct 1-hour training for analysts
  - [ ] Demo all tools
  - [ ] Collect feedback

**Success Criteria**:
- LLM integration functional
- Stance analysis accurate (validated by analysts)
- Cost under control (<$500/month)
- Word2Vec dashboard functional
- MILA framework functional
- Visualizations functional and interactive
- Analyst adoption >80%
- User feedback ≥4/5

**Files to Modify**:
- `src/explainability/mila_analyzer.py` (new)
- `frontend/explainability_dashboard/` (new directory)
- `frontend/visualizations/` (new directory)

---

### Phase 9: Documentation & Production Handoff

**Estimated Scope**: 12 tasks | 2 days | ~30-40k tokens
**Status**: 📋 Planned
**Owner**: Technical Writer + Lead Developer
**Prerequisites**: All previous phases complete (or at least Phase 4 for Tier 1)

**Objectives**:
- Create comprehensive production documentation
- Conduct user training
- Perform final testing and sign-off
- Complete project handoff to operations team

**Tasks**:
- [ ] **Production Runbook**
  - [ ] Create `docs/PRODUCTION_RUNBOOK.md`
  - [ ] Document deployment procedures
  - [ ] Document service management (start/stop/restart)
  - [ ] Document log locations and interpretation
  - [ ] Document common error messages and solutions
  - [ ] Document rollback procedures

- [ ] **User Guide**
  - [ ] Create `docs/USER_GUIDE.md` for analysts
  - [ ] Explain what system detects
  - [ ] Explain confidence levels
  - [ ] Explain recommended actions per alert type
  - [ ] Document dashboard usage

- [ ] **API Documentation**
  - [ ] Document all endpoints (if applicable)
  - [ ] Request/response formats
  - [ ] Authentication requirements

- [ ] **Training**
  - [ ] Schedule 1-hour training session
  - [ ] Demo: Receiving and interpreting alerts
  - [ ] Demo: Using dashboards (if Tier 3 complete)
  - [ ] Q&A session
  - [ ] Record session

- [ ] **Final Testing**
  - [ ] All unit tests passing
  - [ ] All integration tests passing
  - [ ] Prospective test validated
  - [ ] User acceptance testing complete

- [ ] **Sign-Off**
  - [ ] Developer sign-off
  - [ ] QA sign-off
  - [ ] Operations sign-off
  - [ ] Product owner sign-off

**Success Criteria**:
- All documentation complete and reviewed
- Training conducted, positive feedback
- All tests passing
- All sign-offs obtained
- System operational and monitored

**Files to Modify**:
- `docs/PRODUCTION_RUNBOOK.md` (new)
- `docs/USER_GUIDE.md` (new)

---

## Dependencies

**Phase Dependencies**:
- Phase 1 → Phase 2 → Phase 3 → Phase 4 (Tier 1 complete)
- Phase 4 → Phase 5 → Phase 6 (Tier 2 complete)
- Phase 4 → Phase 7 → Phase 8 (Tier 3 complete, Phase 6 recommended)
- Any complete tier → Phase 9 (Documentation)

**Critical Path**: Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 (14 weeks total)

**Parallelization Opportunities**:
- Phase 5 (Market) and Phase 4 completion can overlap
- Phase 7 (Word2Vec) can start after Phase 4 (doesn't require Phase 6)
- Phase 8 visualization work can partially overlap with Phase 7

---

## Success Metrics

**Overall Project Success Criteria**:
- Tier 1: 55% precision, 16% recall, same-day detection
- Tier 2: 65-70% precision, 16% recall maintained
- Tier 3: Analyst adoption >80%, user feedback ≥4/5
- All tests passing (>80% coverage)
- Production deployment successful
- $339K in costs avoided (failed methods not implemented)

---

## Notes

**Important Reminders**:
- Update this document continuously as tasks are completed
- Mark tasks [x] immediately when done (don't batch updates)
- Use TodoWrite tool during work sessions
- Only ONE task in_progress at a time
- When ready to compact, use COMPACTION_DECISION_TREE.md
- For mid-phase compaction, create checkpoint using MID_PHASE_COMPACTION_GUIDE.md
- For phase-complete compaction, create completion report using PHASE_COMPLETION_TEMPLATE.md

**Workflow Documents** (in `docs/` directory):
- `QUICKSTART_AFTER_COMPACTION.md` - Read this first after any compaction
- `COMPACTION_DECISION_TREE.md` - Decision guide and ready-to-paste prompts
- `PRE_COMPACTION_CHECKLIST.md` - Verification before phase-complete compaction
- `PHASE_COMPLETION_TEMPLATE.md` - Template for completion reports
- `MID_PHASE_COMPACTION_GUIDE.md` - Template for checkpoint documents

---

**END OF IMPLEMENTATION PLAN**

**Version**: 2.0 (Phase-Based)
**Last Updated**: November 7, 2025
**Status**: ✅ Ready to Begin Phase 1
