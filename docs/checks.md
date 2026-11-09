# Pre-flight Checks — Adobe Campaign v8 Ops Copilot (P1)

**Principle:** deterministic checks produce the verdict; explanations may be generated later but must not contradict rule results. Every check emits evidence.

## Verdict model
| Verdict | Rule | Human gate |
|---|---|---|
| `PASS` | All required checks pass; no blocking risks | Approval still required before release-impacting progression (configurable; default on) |
| `RISK` | No blocking failures, but warnings/anomalies exceed review threshold | Named approval required; reviewer sees warnings |
| `FAIL` | Any required check fails | Block progression; override requires named approver + written reason + audit event |
| `NOT_READY` | Required evidence missing/cannot be evaluated | Treat as block until evidence is available or explicitly overridden with reason |

## Check catalog (MVP candidates)
Confirm field names/availability against your Campaign v8 data model or adapter before implementation.

| ID | Check | Severity | Inputs (example) | Pass evidence | Fail/Risk example |
|---|---|---|---|---|---|
| PF-01 | **Audience count present** | Required | target count, extraction status | target > 0 and extraction complete | target is 0, null, or extraction failed |
| PF-02 | **Audience drift vs baseline** | Warning/Required* | current target, prior approved/baseline target, threshold % | within configured tolerance | drops/rises beyond threshold (e.g., >30% drop) |
| PF-03 | **Suppression/consent coverage** | Required | suppression applied, consent/opt-out filter status, counts | suppression/consent filters applied as required | no suppression step, consent filter missing, or unsubscribed segment included |
| PF-04 | **Seed/proof status** | Warning/Required* | proof sent/approved, seed list present | proof approved or explicitly waived by policy | no proof and no approved waiver |
| PF-05 | **Personalization fields available** | Required | template fields/tokens, mapped attributes, sample/null rate | required fields mapped; sample shows no blocking nulls | missing mapping or required field null rate above threshold |
| PF-06 | **Link/mirror sanity** | Required | links, mirror page/unsubscribe presence (as modeled) | required links present and well-formed | missing unsubscribe/mirror or malformed required URL pattern |
| PF-07 | **Schedule/timezone sanity** | Required | send/start time, timezone, campaign window, current time | schedule is valid, not in past (unless intentional), timezone explicit | past schedule, missing timezone, outside approved window |
| PF-08 | **Workflow/dependency readiness** | Required | upstream workflow status, approvals, blocking tasks | dependencies complete/approved | upstream failed, pending approval, or stale dependency |
| PF-09 | **Volume/pressure guard** *(optional MVP+)* | Warning | recent sends to audience/segment, pressure rules/typology status | within policy | exceeds frequency cap or pressure warning |
| PF-10 | **Change since last approval** *(optional MVP+)* | Warning/Required* | current config hash vs approved snapshot | unchanged or reviewed | content/audience/schedule changed after approval |

\*Severity can be policy-configurable (`Required` vs `Warning`) per environment/team.

## Implementation status (v0.1.0)
The catalog above is the target design. This is what the engine actually checks today. Keep this table honest: it is what the README links to.

| ID | Implemented in v0.1 | Not yet implemented |
|---|---|---|
| PF-01 | Target count present, numeric, > 0 | Extraction status |
| PF-02 | Drift vs baseline: RISK ≥ 30%, FAIL ≥ 50% (policy-configurable) | — |
| PF-03 | Suppression and consent filter flags both `true` | Counts; unsubscribed-segment inclusion |
| PF-04 | Proof approved; seed list noted. RISK by default, FAIL when `proof_required` | Waiver records |
| PF-05 | No missing personalization mappings | Null-rate sampling |
| PF-06 | Unsubscribe and mirror flags both `true` | URL well-formedness |
| PF-07 | Send time parses as ISO-8601; timezone is a valid IANA name | Send-in-past, approved window, quiet hours |
| PF-08 | Status ready, dependencies OK, 0 pending approvals | Stale-dependency detection |
| PF-09, PF-10 | — | Planned (MVP+) |

On a machine with no timezone database (Windows without `tzdata`), PF-07 reports `timezone_validation: "unverifiable"` and passes on format alone. Install it with `pip install tzdata`.

## Evidence bundle (per run)
For each check record:
- `check_id`, `name`, `severity`, `result` (`pass`/`risk`/`fail`/`not_ready`)
- `observed` values (masked/safe)
- `threshold/policy` used
- `explanation` (plain language)
- `evidence_refs` (synthetic fixture IDs or adapter query references)

## Adapter contract (mock now, read-only later)
The adapter should return normalized fields; checks must not depend on UI scraping. Example normalized shape:
```json
{
  "campaign_id": "synthetic-cmp-001",
  "name": "Spring Reactivation",
  "channel": "email",
  "schedule": {"send_at": "2026-11-15T09:00:00Z", "timezone": "Europe/London"},
  "audience": {"target_count": 12500, "baseline_count": 11800, "suppression_applied": true, "consent_filter_applied": true},
  "proof": {"status": "approved", "seed_list_present": true},
  "content": {"required_personalization_fields": ["first_name"], "missing_mappings": [], "unsubscribe_present": true, "mirror_present": true},
  "workflow": {"status": "ready", "dependencies_ok": true, "pending_approvals": 0}
}
```
*Replace with your actual Campaign v8 model after confirming access.*

## Safe explanation layer (later phase)
If an LLM is added:
- Provide only deterministic check results + masked evidence.
- Ask it to summarize/explain; never to decide pass/fail.
- Validate that summary does not contradict rule verdict (Verdict Lock pattern, Safe to Send Ep12).
- Log prompt/template version and redaction status.
