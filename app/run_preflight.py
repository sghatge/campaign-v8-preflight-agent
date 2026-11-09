from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from agents.audit import AuditLog
from agents.checks import DEFAULT_POLICY, run_all_checks
from agents.models import RunResult, utc_now
from agents.verdict import aggregate_verdict, summarize


def load_scenario(data_path: Path, campaign_id: str) -> dict:
    items = json.loads(data_path.read_text(encoding="utf-8"))
    for item in items:
        if item.get("campaign_id") == campaign_id:
            return item
    raise ValueError(f"Scenario not found: {campaign_id}")


# Exit codes: 0 = OK / gate not tripped, 1 = gate tripped by verdict, 2 = input or approval error.
EXIT_OK, EXIT_GATE, EXIT_ERROR = 0, 1, 2
GATE_VERDICTS = {
    "never": set(),
    "fail": {"FAIL", "NOT_READY"},
    "risk": {"FAIL", "NOT_READY", "RISK"},
}


def gate_exit_code(verdict: str, fail_on: str, approval: dict | None) -> int:
    """Non-zero when the verdict trips the gate, unless a named human approval was recorded.

    An approved override is the human decision the gate exists to capture, so it releases the
    gate; the override is still written to the audit log as `approval.override`.
    """
    if verdict in GATE_VERDICTS[fail_on] and not approval:
        return EXIT_GATE
    return EXIT_OK


def format_report(result: RunResult) -> str:
    lines = [
        f"Run: {result.run_id}",
        f"Campaign: {result.campaign_id}",
        f"Verdict: {result.verdict}",
        f"Summary: {result.summary}",
        "",
        "Checks:",
    ]
    for c in result.checks:
        lines.append(f"- [{c.result.upper():8}] {c.check_id} {c.name} ({c.severity})")
        lines.append(f"  observed: {json.dumps(c.observed, ensure_ascii=False)}")
        lines.append(f"  threshold: {json.dumps(c.threshold, ensure_ascii=False)}")
        lines.append(f"  why: {c.explanation}")
    return "\n".join(lines)


def record_approval(audit: AuditLog | None, run: RunResult, approve: bool, approver: str | None, reason: str | None, policy: dict) -> dict | None:
    if not approve:
        return None
    min_len = int(policy.get("override_reason_min_length", DEFAULT_POLICY["override_reason_min_length"]))
    if run.verdict in {"FAIL", "NOT_READY"}:
        if not approver or not approver.strip():
            raise ValueError("Named approver is required for FAIL/NOT_READY override.")
        if not reason or len(reason.strip()) < min_len:
            raise ValueError(f"Override reason must be at least {min_len} characters for FAIL/NOT_READY.")
    if not approver or not approver.strip():
        raise ValueError("Named approver is required for approval.")

    decision = {
        "event_type": "approval.decision",
        "run_id": run.run_id,
        "campaign_id": run.campaign_id,
        "decision": "approve" if run.verdict in {"PASS", "RISK"} else "approve_override",
        "original_verdict": run.verdict,
        "approver": {"id": approver.strip().lower().replace(" ", "."), "name": approver.strip()},
        "reason": (reason or "").strip() or None,
    }
    if audit:
        audit.append(decision)
    if run.verdict in {"FAIL", "NOT_READY"}:
        override = {
            "event_type": "approval.override",
            "run_id": run.run_id,
            "campaign_id": run.campaign_id,
            "original_verdict": run.verdict,
            "failed_required_checks": [c.check_id for c in run.checks if c.severity == "required" and c.result in {"fail", "not_ready"}],
            "approver": decision["approver"],
            "reason": decision["reason"],
        }
        if audit:
            audit.append(override)
        decision["override_event"] = override
    return decision


def run_scenario(campaign: dict, policy: dict | None = None, adapter_mode: str = "mock", audit_path: str | None = None,
                 approve: bool = False, approver: str | None = None, reason: str | None = None) -> tuple[RunResult, dict | None]:
    policy = {**DEFAULT_POLICY, **(policy or {})}
    started = utc_now()
    checks = run_all_checks(campaign, policy)
    verdict = aggregate_verdict(checks)
    run = RunResult(
        run_id=f"run_{uuid4().hex[:12]}",
        campaign_id=campaign.get("campaign_id", "unknown"),
        verdict=verdict,
        checks=checks,
        summary=summarize(checks, verdict),
        adapter_mode=adapter_mode,
        started_at=started,
        finished_at=utc_now(),
    )
    audit = AuditLog(audit_path) if audit_path else None
    if audit:
        audit.append({"event_type": "run.started", "run_id": run.run_id, "campaign_id": run.campaign_id, "input_ref": campaign.get("campaign_id"), "adapter": {"mode": adapter_mode, "read_only": True}})
        for c in checks:
            audit.append({"event_type": "check.result", "run_id": run.run_id, "campaign_id": run.campaign_id, **c.to_dict()})
        audit.append({"event_type": "run.completed", "run_id": run.run_id, "campaign_id": run.campaign_id, "overall_verdict": verdict, "summary": run.summary})
    approval = record_approval(audit, run, approve=approve, approver=approver, reason=reason, policy=policy)
    return run, approval


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Adobe Campaign v8 pre-flight checks on synthetic scenarios (mock adapter).")
    parser.add_argument("--scenario", required=True, help="campaign_id in the synthetic data file")
    parser.add_argument("--data", default=str(Path(__file__).resolve().parents[1] / "data" / "synthetic" / "example-campaigns.json"))
    parser.add_argument("--audit", default=None, help="Optional JSONL audit log path")
    parser.add_argument("--approve", action="store_true", help="Record approval (requires --approver; FAIL/NOT_READY also require --reason)")
    parser.add_argument("--approver", default=None, help="Named approver")
    parser.add_argument("--reason", default=None, help="Approval/override reason")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--fail-on", choices=sorted(GATE_VERDICTS), default="never",
                        help="Exit 1 when the verdict trips this gate: 'fail' = FAIL/NOT_READY, "
                             "'risk' = also RISK. Default 'never' (report only).")
    args = parser.parse_args(argv)

    try:
        campaign = load_scenario(Path(args.data), args.scenario)
        run, approval = run_scenario(campaign, audit_path=args.audit, approve=args.approve, approver=args.approver, reason=args.reason)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        payload = run.to_dict()
        if approval:
            payload["approval"] = approval
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_report(run))
        if approval:
            print(f"\nApproval recorded: {approval['decision']} by {approval['approver']['name']}")
    code = gate_exit_code(run.verdict, args.fail_on, approval)
    if code == EXIT_GATE:
        print(f"\nGATE: verdict {run.verdict} blocks progression (--fail-on {args.fail_on}).", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
