from __future__ import annotations

from .models import CheckResult


def aggregate_verdict(checks: list[CheckResult]) -> str:
    # Precedence: required not_ready/fail dominate; then risk; else pass.
    has_required_not_ready = any(c.severity == "required" and c.result == "not_ready" for c in checks)
    has_required_fail = any(c.severity == "required" and c.result == "fail" for c in checks)
    has_risk = any(c.result == "risk" for c in checks)
    has_any_fail = any(c.result == "fail" for c in checks)
    has_any_not_ready = any(c.result == "not_ready" for c in checks)

    if has_required_fail or has_any_fail and any(c.severity == "required" for c in checks if c.result == "fail"):
        return "FAIL"
    if has_required_not_ready:
        return "NOT_READY"
    if has_risk or has_any_fail or has_any_not_ready:
        return "RISK"
    return "PASS"


def summarize(checks: list[CheckResult], verdict: str) -> str:
    failed = [c.check_id for c in checks if c.result == "fail"]
    not_ready = [c.check_id for c in checks if c.result == "not_ready"]
    risks = [c.check_id for c in checks if c.result == "risk"]
    parts = [f"Overall verdict: {verdict}."]
    if failed:
        parts.append(f"Failed checks: {', '.join(failed)}.")
    if not_ready:
        parts.append(f"Evidence not ready: {', '.join(not_ready)}.")
    if risks:
        parts.append(f"Risk/warning checks: {', '.join(risks)}.")
    if verdict == "PASS":
        parts.append("All configured checks passed; named approval may still be required by policy.")
    elif verdict == "FAIL":
        parts.append("Release-impacting progression is blocked pending review; override requires a written reason and audit event.")
    elif verdict == "NOT_READY":
        parts.append("Required evidence is missing; resolve or explicitly override with reason.")
    else:
        parts.append("Review warnings before approval.")
    return " ".join(parts)
