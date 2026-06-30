# Loop Engineering — Audio AI Editor

## Purpose
Define continuous improvement loops, quality gates, self-evaluation protocols, and learning mechanisms for autonomous AI agent development workflows.

---

## Core Loop: OBSERVE → ANALYZE → PLAN → EXECUTE → VERIFY → LEARN

### 1. OBSERVE Phase
**Inputs**: Code changes, test results, performance metrics, user feedback
**Outputs**: Observation report

```yaml
observe:
  code_quality:
    - lint_warnings: 0        # Target: zero warnings
    - type_errors: 0          # Target: zero type errors
    - test_coverage: ">80%"   # Target: 80%+ coverage
  performance:
    - build_time: "<30s"      # Frontend build
    - api_latency_p95: "<200ms"
    - model_load_time: "<10s"
  audio_quality:
    - sdr_score: ">7.0"      # Signal-to-Distortion Ratio for stem separation
    - snr_improvement: ">10dB" # Noise reduction effectiveness
```

### 2. ANALYZE Phase
**Pattern Detection**:
- Recurring test failures → flaky test identification
- Performance regression → bottleneck analysis
- Code duplication → abstraction opportunity
- API contract drift → schema sync needed

**Automated Analysis Rules**:
```
IF test_coverage < 80% THEN flag("coverage_gap", affected_modules)
IF build_time > 30s THEN flag("build_regression", diff_from_baseline)
IF api_schema_mismatch THEN flag("contract_drift", mismatched_endpoints)
IF audio_sdr < 7.0 THEN flag("quality_regression", affected_models)
```

### 3. PLAN Phase
**Task Prioritization Matrix**:
| Priority | Criteria | Action |
|----------|----------|--------|
| P0 - Critical | Broken build, failing tests, security issue | Fix immediately |
| P1 - High | Performance regression, quality drop | Fix within session |
| P2 - Medium | Tech debt, missing tests, docs gap | Plan for next session |
| P3 - Low | Nice-to-have, optimization | Backlog |

**Planning Rules**:
- Max 1 P0/P1 task in flight at a time
- P2 tasks bundled into coherent improvement PRs
- Each plan must have a verification step

### 4. EXECUTE Phase
**Execution Constraints**:
- One logical change per commit
- Tests written/updated alongside implementation
- No force-pushes to protected branches
- API changes require both frontend + backend updates

**Commit Message Format**:
```
<type>(<scope>): <subject>

Types: feat, fix, refactor, test, docs, chore, perf
Scopes: frontend, backend, audio, ci, deps
```

### 5. VERIFY Phase
**Verification Checklist**:
```bash
# Frontend
npm run lint          # Zero warnings
npm run typecheck     # Zero errors  
npm run test          # All passing
npm run build         # Successful build

# Backend
black --check .       # Formatting
isort --check .       # Import order
mypy .                # Type checking
pytest --cov          # Tests + coverage

# Integration
docker compose build  # Container build
docker compose up -d  # Services start
curl /health          # Health check passes
```

### 6. LEARN Phase
**Knowledge Capture**:
- Document new patterns in CLAUDE.md
- Update AGENTS.md with new responsibilities
- Record performance baselines
- Log architecture decisions with rationale

---

## Feedback Loops

### Short Loop (Per-Change)
```
Code Change → Lint → Type Check → Unit Test → Commit
Duration: < 2 minutes
```

### Medium Loop (Per-Feature)
```
Feature Branch → Integration Tests → Code Review → Merge → Deploy
Duration: < 1 hour
```

### Long Loop (Per-Sprint)
```
Sprint Goals → Implementation → Quality Audit → Retrospective → Improve
Duration: 1-2 weeks
```

---

## Self-Evaluation Protocol

### After Each Session
1. **What was accomplished?** — List concrete deliverables
2. **What was the quality?** — Check against quality gates
3. **What was learned?** — New patterns, anti-patterns, or insights
4. **What's next?** — Clear handoff for next session

### Quality Scoring Rubric
| Dimension | Score 1 (Poor) | Score 3 (Good) | Score 5 (Excellent) |
|-----------|---------------|----------------|---------------------|
| Correctness | Bugs present | Works with edge cases | Handles all cases + error states |
| Completeness | Missing features | Core features done | Full feature + tests + docs |
| Code Quality | Lint errors | Clean + typed | Clean + typed + well-abstracted |
| Performance | Regression | No regression | Measurable improvement |
| Audio Quality | Audible artifacts | Clean output | Studio-grade output |

---

## Anti-Patterns to Avoid
1. **Big Bang Changes**: Never rewrite more than one module at a time
2. **Test Skipping**: Never skip or delete tests to make CI green
3. **Implicit Dependencies**: Always declare dependencies explicitly
4. **Premature Optimization**: Profile before optimizing
5. **Gold Plating**: Ship the MVP, iterate later
6. **Broken Windows**: Fix quality issues immediately, don't defer

## Recovery Protocols
### Build Failure
1. Check error message
2. Identify failing component (frontend/backend/docker)
3. Fix minimal change
4. Verify with clean build
5. Document root cause

### Test Failure
1. Read assertion error
2. Check if test or implementation is wrong
3. Fix the correct side
4. Run full suite to verify no cascade
5. Add regression guard if needed

### Model Loading Failure
1. Check GPU memory availability
2. Try CPU fallback
3. Try smaller model variant
4. Check model file integrity
5. Report if all fails
