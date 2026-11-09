# Audit Schema — P1 Pre-flight Runs

Append-only records. Public demos must use synthetic identifiers and masked/safe evidence only.

## Entities

### Run
```json
{
  "run_id": "run_20261109_001",
  "project": "campaign-v8-preflight-agent",
  "version": "0.1.0",
  "started_at": "2026-11-09T12:00:00Z",
  "finished_at": "2026-11-09T12:00:03Z",
  "actor": {"type": "user", "id": "reviewer.synthetic"},
  "input_ref": "data/synthetic/example-campaigns.json#synthetic-cmp-001",
  "adapter": {"mode": "mock", "name": "campaign-v8-mock", "read_only": true},
  "overall_verdict": "FAIL",
  "summary": "1 required check failed; release-impacting progression blocked pending review."
}
```

### Check result
```json
{
  "event_type": "check.result",
  "run_id": "run_20261109_001",
  "check_id": "PF-03",
  "name": "Suppression/consent coverage",
  "severity": "required",
  "result": "fail",
  "observed": {"suppression_applied": false, "consent_filter_applied": true},
  "threshold": {"suppression_applied": true},
  "explanation": "Suppression was not applied; sending could include contacts who should be excluded.",
  "evidence_refs": ["synthetic-cmp-001.audience"],
  "timestamp": "2026-11-09T12:00:01Z"
}
```

### Approval / rejection
```json
{
  "event_type": "approval.decision",
  "run_id": "run_20261109_001",
  "decision": "approve_override",
  "original_verdict": "FAIL",
  "approver": {"id": "approver.synthetic", "name": "Named Approver"},
  "reason": "Synthetic demo: approved only to exercise override logging; not a production decision.",
  "timestamp": "2026-11-09T12:00:02Z"
}
```

### Override (distinct event)
```json
{
  "event_type": "approval.override",
  "run_id": "run_20261109_001",
  "original_verdict": "FAIL",
  "failed_required_checks": ["PF-03"],
  "approver": {"id": "approver.synthetic", "name": "Named Approver"},
  "reason": "Synthetic demo: approved only to exercise override logging; not a production decision.",
  "timestamp": "2026-11-09T12:00:02Z"
}
```

## Rules
- `reason` is required for `FAIL`/`NOT_READY` overrides; minimum length configurable (default >= 15 chars).
- Agents/services cannot create approval events as self-approval.
- `approval.override` is always separate from the normal check/verdict flow for easy review.
- Store IDs/references, not raw PII. Mask or omit sensitive fields.
- Consider hash-chaining events in a later version (Safe to Send Ep06 pattern) for tamper evidence.

## Evidence bundle export
A portable export should include: run, normalized input reference (safe), all check results, final verdict, approval/rejection, override event(s), tool/adapter mode, and version metadata.
