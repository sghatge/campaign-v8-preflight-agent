# Changelog

## v0.1.0 — Milestone 1 (unreleased)

Deterministic, read-only pre-flight engine on synthetic data.

### Added
- Eight pre-flight checks, PF-01 to PF-08: audience presence, audience drift, suppression/consent, proof/seed, personalization mappings, unsubscribe/mirror links, schedule/timezone, workflow readiness.
- Verdict aggregation: `PASS` / `RISK` / `FAIL` / `NOT_READY`, with a plain-language summary.
- Named approval flow. Overrides of `FAIL`/`NOT_READY` need a named approver and a reason of at least 15 characters, and are logged as a distinct `approval.override` event.
- Append-only JSONL audit log.
- CLI (`python -m app.run_preflight`) with text and JSON output.
- `--fail-on {never,fail,risk}` gate with exit codes `0` OK, `1` gate tripped, `2` input/approval error. An audited override releases the gate.
- Static demo UI (`app/demo.html`) showing the three synthetic scenarios.
- CI on Ubuntu and Windows, Python 3.10–3.13, plus a CLI gate smoke test.
- Safety guards in CI: a no-send import check, a leak guard, `.env.example` placeholder enforcement, and demo/engine parity.

### Changed (hardening of the prototype)
- PF-07 now parses the send time as real ISO-8601 and validates the IANA timezone name. Previously any value containing a "T" passed, so `"Tuesday"` was accepted.
- An unknown scenario or unreadable data file now exits with code `2` and a clear error.

### Known limits
- Mock adapter only. No connection to any Adobe Campaign instance.
- Synthetic data cannot prove production readiness.
- No authentication/RBAC. Approver names are self-declared, and self-approval is not yet prevented.
- PF-07 does not check send-in-past, quiet hours, or market calendars.
