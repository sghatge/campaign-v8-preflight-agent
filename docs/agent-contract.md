# Agent Contract — Adobe Campaign v8 Pre-flight & Ops Copilot (P1)

**Project:** `[REPO_P1]` (suggested name: `campaign-v8-preflight-agent`)  
**Phase:** MVP read-only, mock adapter, synthetic data.

## Goal
Evaluate campaign/delivery/workflow readiness before send/execute and produce an evidence-backed verdict that a named human can approve, reject, or override with an audited reason.

## Audience journey
*Problem → Risk → Agent check → Human decision → Audit record → Business impact*

## Allowed inputs
- Normalized campaign metadata/counts from the mock adapter or synthetic fixtures.
- Policy/config thresholds (audience drift %, proof required, override reason length, etc.).
- Human approval/rejection/override input.

## Allowed actions
- Read normalized inputs.
- Run fixed deterministic checks (PF catalog).
- Generate verdict, check evidence, and plain-language summary.
- Persist run ledger/audit events and export evidence bundles.
- Request/record named human approval.

## Disallowed actions
- Send, schedule, activate, pause, or modify real campaigns/workflows/deliveries.
- Use real production credentials or customer data in MVP/public demos.
- Bypass required approval or override reason validation.
- Self-approve release-impacting decisions.
- Let an LLM determine pass/fail verdicts (if/when LLM summaries are added later).

## Decision thresholds
- `PASS`: no required failures; warnings within acceptable policy.
- `RISK`: warnings/anomalies require review; no required hard block unless policy escalates.
- `FAIL`: any required check fails.
- `NOT_READY`: required evidence missing or cannot be evaluated.
See `checks.md` for PF-01–PF-08 and severity rules.

## Approval point
- Named human approval required before release-impacting progression (default).
- `FAIL`/`NOT_READY` override requires: named approver identity, written reason (>= 15 chars by default), timestamp, original verdict, failed checks.
- Override is logged as a separate `approval.override` event.
- v2 target: two-person approval for overrides.

## Audit record
Minimum fields: run ID/version/timestamps, actor, input reference, adapter mode, per-check results/evidence, overall verdict, approval decision, approver, reason, override event. See `audit-schema.md`.

## Output format
- Verdict banner (`PASS`/`RISK`/`FAIL`/`NOT_READY`).
- Check table with severity, result, observed evidence, threshold/policy, explanation.
- Plain-language summary.
- Audit/evidence export.

## Known limits
- Mock adapter and synthetic data in MVP.
- Field mappings to real Adobe Campaign v8 objects must be verified before any real read integration.
- Does not replace organizational approval processes, legal/compliance review, or deliverability controls.
- No RBAC/SSO/authentication in MVP.
