# Campaign v8 Pre-flight Agent

[![CI](https://github.com/sghatge/campaign-v8-preflight-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/sghatge/campaign-v8-preflight-agent/actions/workflows/ci.yml)
![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)
![Runtime deps: 0](https://img.shields.io/badge/runtime%20deps-0-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Mode: read-only](https://img.shields.io/badge/mode-read--only%20%C2%B7%20no%20send-orange)

**Agents check. Humans decide. Every decision is logged.**

A deterministic pre-flight gate for Adobe Campaign Classic v8 deliveries. It runs eight readiness checks, returns `PASS` / `RISK` / `FAIL` / `NOT_READY`, blocks a CI pipeline on failure, and records any human override as an auditable event.

> **Milestone 1 · read-only · synthetic data · no send capability.**
> This repo does not connect to Adobe Campaign. It evaluates synthetic delivery metadata. CI fails the build if engine code ever imports a network or mail module.

**[▶ Live demo](https://sghatge.github.io/campaign-v8-preflight-agent/app/demo.html)** · [Check catalog](docs/checks.md) · [Agent contract](docs/agent-contract.md) · [Audit schema](docs/audit-schema.md)

<!-- Uncomment once captured (see docs/screenshots-plan.md, shot 7):
![Pre-flight demo: PASS → FAIL → audited override](assets/preflight-demo.gif)
-->

---

## The problem
Campaign teams often find avoidable risks only after a delivery is prepared, or after it has gone out: a missing suppression step, an unmapped personalization field, no mirror page, an upstream workflow that isn't ready, or an audience that silently halved. The email can look perfect while the operational context is unsafe.

## How it works
```
 delivery metadata ──▶ 8 deterministic checks ──▶ verdict ──▶ human decision ──▶ audit log
   (synthetic)          PF-01 … PF-08               PASS        approve /          JSONL,
                        each emits evidence         RISK        override with      append-only
                                                    FAIL        named approver
                                                    NOT_READY   + written reason
```

| ID | Check | Severity |
|---|---|---|
| PF-01 | Audience count present | Required |
| PF-02 | Audience drift vs baseline (RISK ≥ 30%, FAIL ≥ 50%) | Warning → Required |
| PF-03 | Suppression and consent filters applied | Required |
| PF-04 | Proof approved / seed list present | Warning (Required by policy) |
| PF-05 | Personalization mappings complete | Required |
| PF-06 | Unsubscribe and mirror page present | Required |
| PF-07 | Send time is valid ISO-8601; timezone is a valid IANA name | Required |
| PF-08 | Workflow ready, dependencies OK, no pending approvals | Required |

The rules decide the verdict. No LLM is involved in pass/fail. [Exactly what each check covers today →](docs/checks.md#implementation-status-v010)

## Run locally
No dependencies, Python 3.10+.

```bash
git clone https://github.com/sghatge/campaign-v8-preflight-agent
cd campaign-v8-preflight-agent

python -m app.run_preflight --scenario synthetic-cmp-pass-001     # PASS
python -m app.run_preflight --scenario synthetic-cmp-risk-002     # RISK  (43.6% audience drift)
python -m app.run_preflight --scenario synthetic-cmp-fail-003     # FAIL
python -m unittest -v                                             # 28 tests
```

On Windows, also run `pip install tzdata` so PF-07 can validate timezone names.

### Use it as a CI gate
```bash
$ python -m app.run_preflight --scenario synthetic-cmp-fail-003 --fail-on fail
Verdict: FAIL
- [FAIL    ] PF-03 Suppression/consent coverage (required)
  why: Required protection missing: suppression.
- [FAIL    ] PF-05 Personalization fields available (required)
  why: Required personalization mappings missing: first_name.
...
GATE: verdict FAIL blocks progression (--fail-on fail).
$ echo $?
1
```

| `--fail-on` | Exits 1 on | Exit codes |
|---|---|---|
| `never` *(default)* | nothing (report only) | `0` OK |
| `fail` | `FAIL`, `NOT_READY` | `1` gate tripped |
| `risk` | `FAIL`, `NOT_READY`, `RISK` | `2` input or approval error |

### Override, with an audit trail
```bash
$ python -m app.run_preflight --scenario synthetic-cmp-fail-003 --fail-on fail \
    --audit .local/audit.jsonl --approve --approver "Demo Approver" \
    --reason "Synthetic demo: suppression fix verified out-of-band."
Approval recorded: approve_override by Demo Approver        # exit 0

$ grep approval.override .local/audit.jsonl
{"event_type": "approval.override", "original_verdict": "FAIL",
 "failed_required_checks": ["PF-03", "PF-05", "PF-06", "PF-08"],
 "approver": {"id": "demo.approver", "name": "Demo Approver"},
 "reason": "Synthetic demo: suppression fix verified out-of-band.", ...}
```
An override of `FAIL`/`NOT_READY` is rejected without a named approver and a reason of at least 15 characters.

## Safety model
| Area | Behaviour | Enforced by |
|---|---|---|
| Data | Synthetic fixtures only (`data/synthetic/`) | CI leak guard: emails, phones, tokens, card numbers, keys |
| Send capability | None. No network, mail or process imports in `agents/` or `app/` | CI import check (`tests/test_safety_guards.py`) |
| Credentials | None read or stored; `.env.example` holds empty placeholders | CI placeholder check, `.gitignore` |
| Human gate | Named approver + written reason for FAIL/NOT_READY | Unit tests |
| Audit | Append-only JSONL; overrides are a distinct `approval.override` event | Unit tests + CI smoke test |
| Demo honesty | Static demo must match engine output exactly | CI demo-parity test |

## Known limits
- **Mock adapter only.** No connection to any Adobe Campaign instance; synthetic data can't prove production readiness.
- **No authentication/RBAC.** Approver names are self-declared, and self-approval isn't prevented yet.
- **PF-07** doesn't check send-in-past, quiet hours or market calendars.
- Check thresholds (e.g. 30%/50% drift) are illustrative defaults, not tuned to a real program.
- The demo UI is static; it displays engine results, and CI keeps it in sync.

## Project structure
```text
agents/      checks, verdict aggregation, audit log (the engine)
app/         CLI (run_preflight.py) and static demo UI
data/        synthetic scenarios: PASS, RISK, FAIL
docs/        check catalog, agent contract, audit schema, milestones,
             release checklist, screenshots plan
tests/       engine, CLI gate, PF-07, safety guards, demo parity
.github/     CI workflow, PR template
```

## Roadmap
- **v0.1** (this release): deterministic checks, verdict, CLI gate, audited override, demo.
- **v0.2:** evidence-bundle export, audit-log viewer, two-person override approval.
- **v0.3:** approved read-only Campaign adapter (credentials handled outside the repo).
- **v1.0 (gated):** optional prepare/proof actions behind explicit approval. Never auto-send.

## Related projects
- [OPSFORGE](https://github.com/sghatge/opsforge): governed agent platform (checks, named approval, audited override)
- [ACC Agent Gate](https://github.com/sghatge/acc-agent-gate): policy-as-code for Adobe Campaign tool calls
- [Safe to Send Ep28](https://github.com/sghatge/safe-to-send-28-preflight): GO/NO-GO pre-flight pattern
- [CRM Ops AI Skills](https://github.com/sghatge/crm-ops-ai-skills): evidence-first CRM ops workflows

## License
[MIT](LICENSE) © 2026 Sangram Ghatge
