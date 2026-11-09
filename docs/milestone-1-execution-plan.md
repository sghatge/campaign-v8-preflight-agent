# Milestone 1 — Execution Plan (Deterministic Engine + Synthetic Scenarios)

**Goal:** produce stable, testable pre-flight verdicts for synthetic Campaign v8 scenarios with evidence, no UI polish required beyond a clear CLI/report.

## File-by-file build steps

| File | Purpose | Key behaviors |
|---|---|---|
| `agents/__init__.py` | Package marker | empty |
| `agents/models.py` | Typed structures (dataclasses) | `CheckResult`, `RunResult`, verdict enums/constants; keep JSON-serializable |
| `agents/checks.py` | Deterministic PF checks | Implement PF-01..PF-08 from `docs/checks.md`; each returns `CheckResult` with `observed`, `threshold`, `explanation`, `evidence_refs` |
| `agents/verdict.py` | Verdict aggregation | `FAIL` if any required check fails; `NOT_READY` if required evidence missing; `RISK` if warnings exceed policy; else `PASS` |
| `agents/audit.py` | Append-only JSONL audit | Write run, `check.result`, `approval.decision`, `approval.override` events; mask/safe values only; create parent dirs |
| `app/__init__.py` | Package marker | empty |
| `app/run_preflight.py` | CLI entrypoint | Load scenario by `campaign_id` from JSON; run checks; print verdict/report; optional `--approve --approver "Name" --reason "..."`; enforce override reason length for FAIL/NOT_READY |
| `tests/__init__.py` | Package marker | empty |
| `tests/test_checks.py` | Unit/scenario tests | Per-check cases + 3 synthetic scenarios (pass/risk/fail) + “no silent override” behavior |
| `tests/test_audit.py` | Audit tests | Events written; override emits distinct `approval.override`; reason required for FAIL override |
| `README.md` | Run/test instructions | Add verified commands |

## Test cases

### Per-check (representative)
- **PF-01:** target 12500 => pass; target 0 => fail; missing/null => not_ready/fail (decide and document).
- **PF-02:** 12500 vs 11800 (<=30% drift default) => pass; 6200 vs 11000 => risk/fail based on policy (default risk/warning threshold configurable).
- **PF-03:** suppression false => fail (required).
- **PF-04:** proof not_sent + no waiver => risk or fail per policy (default warning; make configurable).
- **PF-05:** missing mapping for required field => fail.
- **PF-06:** mirror missing => fail.
- **PF-07:** missing timezone or past send time => fail (past allowed only with explicit policy flag).
- **PF-08:** dependencies not ok / pending approvals => fail.

### Scenario tests (from `data/synthetic/example-campaigns.json`)
| Scenario | Expected verdict | Expected notable checks |
|---|---|---|
| `synthetic-cmp-pass-001` | `PASS` | all required checks pass |
| `synthetic-cmp-risk-002` | `RISK` | PF-02 audience drift warning/risk |
| `synthetic-cmp-fail-003` | `FAIL` | PF-03, PF-04 (per policy), PF-05, PF-06, PF-08 fail/risk as configured; overall FAIL due to required failures |

*Exact PF-04 severity is policy-configurable; tests must assert the configured behavior.*

### Approval/audit tests
- FAIL verdict + approve without reason => rejected/error, no approval event.
- FAIL verdict + approve with short reason (<15 chars default) => rejected/error.
- FAIL verdict + approve with valid approver+reason => `approval.decision` and `approval.override` written.
- PASS verdict + approve (if required) => `approval.decision` written, no override event.

## Acceptance criteria
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] CLI runs: `python -m app.run_preflight --scenario synthetic-cmp-pass-001` prints `PASS`; fail scenario prints `FAIL` with check evidence.
- [ ] Deterministic: same input => same verdict and check results.
- [ ] Evidence present for every check (`result`, `observed`, `threshold/policy`, `explanation`).
- [ ] Override cannot be recorded without valid reason for `FAIL`/`NOT_READY`.
- [ ] Override creates a distinct `approval.override` audit event.
- [ ] No external network calls, no credentials required, synthetic data only.
- [ ] Code/docstrings state mock/synthetic scope and known limits.

## Policy defaults (configurable constants)
```text
AUDIENCE_DRIFT_RISK_PCT = 30
AUDIENCE_DRIFT_FAIL_PCT = 50   # optional
PROOF_REQUIRED = false          # warning if missing; teams can set true
OVERRIDE_REASON_MIN_LENGTH = 15
REQUIRE_APPROVAL_FOR_PASS = true
```
Document defaults in README/config; tests should use explicit config where helpful.
