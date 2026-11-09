# MVP Milestones — P1 Campaign v8 Pre-flight & Ops Copilot

Assumes read-only MVP, mock adapter, synthetic data. Adjust dates/owners before use.

## Milestone 0 — Spec & safety (1–2 days)
- [ ] Confirm target: Campaign v8/ACC v8 vs AJO vs AEP.
- [ ] Confirm available access (none/mock only, sandbox read access, or production read access — never start with production writes).
- [ ] Finalize MVP checks (start with PF-01 to PF-08).
- [ ] Create repo `[REPO_P1]` from template; add `.env.example`, leak guard, CI skeleton.
- [ ] Add agent contract, checks, audit schema docs.

**Exit:** approved spec; no real credentials/data in repo.

## Milestone 1 — Deterministic engine (3–4 days)
- [ ] Implement normalized synthetic input loader.
- [ ] Implement PF-01–PF-08 as deterministic checks with evidence.
- [ ] Implement verdict aggregation (`PASS`/`RISK`/`FAIL`/`NOT_READY`).
- [ ] Unit tests per check (pass/fail/edge cases).
- [ ] Golden/snapshot tests for verdict stability.

**Exit:** `pytest`/test suite passes locally and in CI for synthetic scenarios.

## Milestone 2 — Demo UI/report (2–3 days)
- [ ] Simple UI or CLI report: scenario selector, verdict banner, check table, evidence, plain-language summary.
- [ ] Pass/risk/fail states visually distinct.
- [ ] “Start with sample scenario” flow.
- [ ] Mobile-friendly if web UI.

**Exit:** non-technical reviewer can understand result in < 2 minutes.

## Milestone 3 — Approval & audit (2–3 days)
- [ ] Named approval/reject flow.
- [ ] Override requires written reason for `FAIL`/`NOT_READY`; reason length validated.
- [ ] Append-only run ledger; `approval.override` emitted as distinct event.
- [ ] Evidence bundle export (JSON/Markdown/PDF-lite as appropriate).
- [ ] Tests for “no silent approval” and override logging.

**Exit:** failed result cannot be approved without reason; audit shows who/when/why.

## Milestone 4 — Release & publish (1–2 days)
- [ ] README with problem, safety model, known limits, run steps.
- [ ] Screenshots/GIF: pass, fail, override, audit.
- [ ] Demo URL/homepage set; desktop + mobile check.
- [ ] Version tag + changelog + release notes.
- [ ] Hub card + LinkedIn “building in public” post (story-first, no unverified integration claims).

**Exit:** release checklist passes.

## Milestone 5 — Approved read-only integration (later, gated)
- [ ] Confirm legal/security approval and environment.
- [ ] Implement read-only Campaign v8 adapter behind the same normalized interface.
- [ ] Map real fields to PF checks; document unsupported checks.
- [ ] Run in sandbox/stage first; compare results with manual review.
- [ ] Keep credentials outside repo; use approved secret handling.

**Exit:** read-only adapter verified in an approved non-production environment; limitations documented.
