from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import CheckResult


def _parse_iso_datetime(value: str) -> datetime | None:
    """Parse an ISO-8601 datetime; accepts a trailing 'Z' on Python 3.10."""
    text = str(value).strip()
    if "T" not in text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _timezone_status(tz: str) -> str:
    """Return 'valid', 'invalid', or 'unverifiable' (no tz database, e.g. Windows without tzdata)."""
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones
    except ImportError:  # pragma: no cover - zoneinfo is stdlib on 3.9+
        return "unverifiable"
    try:
        ZoneInfo(str(tz))
        return "valid"
    except (ZoneInfoNotFoundError, ValueError):
        return "invalid" if available_timezones() else "unverifiable"


DEFAULT_POLICY = {
    "audience_drift_risk_pct": 30.0,
    "audience_drift_fail_pct": 50.0,
    "proof_required": False,
    "override_reason_min_length": 15,
    "require_approval_for_pass": True,
}


def _ref(campaign_id: str, *parts: str) -> list[str]:
    base = campaign_id or "campaign"
    return [f"{base}.{p}" for p in parts] if parts else [base]


def check_pf01_audience_present(campaign: dict[str, Any]) -> CheckResult:
    audience = campaign.get("audience") or {}
    target = audience.get("target_count")
    observed = {"target_count": target}
    threshold = {"target_count_gt": 0}
    if target is None:
        return CheckResult("PF-01", "Audience count present", "required", "not_ready", observed, threshold,
                           "Target count is missing; cannot evaluate readiness.", _ref(campaign.get("campaign_id"), "audience"))
    try:
        target_n = float(target)
    except (TypeError, ValueError):
        return CheckResult("PF-01", "Audience count present", "required", "fail", observed, threshold,
                           "Target count is not a valid number.", _ref(campaign.get("campaign_id"), "audience"))
    if target_n > 0:
        return CheckResult("PF-01", "Audience count present", "required", "pass", observed, threshold,
                           f"Target audience contains {int(target_n)} contacts.", _ref(campaign.get("campaign_id"), "audience"))
    return CheckResult("PF-01", "Audience count present", "required", "fail", observed, threshold,
                       "Target audience is empty; campaign should not progress.", _ref(campaign.get("campaign_id"), "audience"))


def check_pf02_audience_drift(campaign: dict[str, Any], policy: dict[str, Any]) -> CheckResult:
    audience = campaign.get("audience") or {}
    current = audience.get("target_count")
    baseline = audience.get("baseline_count")
    risk_pct = float(policy.get("audience_drift_risk_pct", DEFAULT_POLICY["audience_drift_risk_pct"]))
    fail_pct = float(policy.get("audience_drift_fail_pct", DEFAULT_POLICY["audience_drift_fail_pct"]))
    observed = {"target_count": current, "baseline_count": baseline}
    threshold = {"risk_abs_pct": risk_pct, "fail_abs_pct": fail_pct}
    refs = _ref(campaign.get("campaign_id"), "audience")
    if current is None or baseline is None:
        return CheckResult("PF-02", "Audience drift vs baseline", "warning", "not_ready", observed, threshold,
                           "Current or baseline audience count is missing; drift cannot be evaluated.", refs)
    try:
        current_n = float(current)
        baseline_n = float(baseline)
    except (TypeError, ValueError):
        return CheckResult("PF-02", "Audience drift vs baseline", "warning", "fail", observed, threshold,
                           "Audience counts are not valid numbers.", refs)
    if baseline_n == 0:
        return CheckResult("PF-02", "Audience drift vs baseline", "warning", "risk", observed, threshold,
                           "Baseline count is zero; cannot compute a stable drift percentage.", refs)
    drift_pct = abs(current_n - baseline_n) / baseline_n * 100.0
    observed["drift_abs_pct"] = round(drift_pct, 2)
    if drift_pct >= fail_pct:
        return CheckResult("PF-02", "Audience drift vs baseline", "required", "fail", observed, threshold,
                           f"Audience drift is {drift_pct:.1f}% (>= {fail_pct:.0f}%); requires investigation before progression.", refs)
    if drift_pct >= risk_pct:
        return CheckResult("PF-02", "Audience drift vs baseline", "warning", "risk", observed, threshold,
                           f"Audience drift is {drift_pct:.1f}% (>= {risk_pct:.0f}%); review before approval.", refs)
    return CheckResult("PF-02", "Audience drift vs baseline", "warning", "pass", observed, threshold,
                       f"Audience drift is {drift_pct:.1f}%, within tolerance.", refs)


def check_pf03_suppression_consent(campaign: dict[str, Any]) -> CheckResult:
    audience = campaign.get("audience") or {}
    suppression = audience.get("suppression_applied")
    consent = audience.get("consent_filter_applied")
    observed = {"suppression_applied": suppression, "consent_filter_applied": consent}
    threshold = {"suppression_applied": True, "consent_filter_applied": True}
    refs = _ref(campaign.get("campaign_id"), "audience")
    if suppression is None or consent is None:
        return CheckResult("PF-03", "Suppression/consent coverage", "required", "not_ready", observed, threshold,
                           "Suppression or consent filter status is missing.", refs)
    if suppression is True and consent is True:
        return CheckResult("PF-03", "Suppression/consent coverage", "required", "pass", observed, threshold,
                           "Suppression and consent filters are applied.", refs)
    missing = []
    if suppression is not True:
        missing.append("suppression")
    if consent is not True:
        missing.append("consent filter")
    return CheckResult("PF-03", "Suppression/consent coverage", "required", "fail", observed, threshold,
                       f"Required protection missing: {', '.join(missing)}.", refs)


def check_pf04_proof_seed(campaign: dict[str, Any], policy: dict[str, Any]) -> CheckResult:
    proof = campaign.get("proof") or {}
    status = proof.get("status")
    seed = proof.get("seed_list_present")
    required = bool(policy.get("proof_required", DEFAULT_POLICY["proof_required"]))
    observed = {"proof_status": status, "seed_list_present": seed}
    threshold = {"proof_approved_or_waived": True, "proof_required": required}
    refs = _ref(campaign.get("campaign_id"), "proof")
    if status is None and seed is None:
        result = "not_ready" if required else "risk"
        return CheckResult("PF-04", "Seed/proof status", "required" if required else "warning", result, observed, threshold,
                           "Proof/seed evidence is missing.", refs)
    approved = str(status).lower() == "approved"
    if approved:
        msg = "Proof is approved." + (" Seed list is present." if seed else " Seed list status not confirmed.")
        return CheckResult("PF-04", "Seed/proof status", "required" if required else "warning", "pass", observed, threshold,
                           msg, refs)
    if required:
        return CheckResult("PF-04", "Seed/proof status", "required", "fail", observed, threshold,
                           "Proof approval is required by policy but not present.", refs)
    return CheckResult("PF-04", "Seed/proof status", "warning", "risk", observed, threshold,
                       "Proof is not approved; review before release or record an approved waiver.", refs)


def check_pf05_personalization(campaign: dict[str, Any]) -> CheckResult:
    content = campaign.get("content") or {}
    required = content.get("required_personalization_fields") or []
    missing = content.get("missing_mappings") or []
    observed = {"required_personalization_fields": required, "missing_mappings": missing}
    threshold = {"missing_mappings_empty": True}
    refs = _ref(campaign.get("campaign_id"), "content")
    if not isinstance(required, list) or not isinstance(missing, list):
        return CheckResult("PF-05", "Personalization fields available", "required", "not_ready", observed, threshold,
                           "Personalization field metadata is missing or invalid.", refs)
    if missing:
        return CheckResult("PF-05", "Personalization fields available", "required", "fail", observed, threshold,
                           f"Required personalization mappings missing: {', '.join(map(str, missing))}.", refs)
    return CheckResult("PF-05", "Personalization fields available", "required", "pass", observed, threshold,
                       "Required personalization mappings are present.", refs)


def check_pf06_links_mirror(campaign: dict[str, Any]) -> CheckResult:
    content = campaign.get("content") or {}
    unsub = content.get("unsubscribe_present")
    mirror = content.get("mirror_present")
    observed = {"unsubscribe_present": unsub, "mirror_present": mirror}
    threshold = {"unsubscribe_present": True, "mirror_present": True}
    refs = _ref(campaign.get("campaign_id"), "content")
    if unsub is None or mirror is None:
        return CheckResult("PF-06", "Link/mirror sanity", "required", "not_ready", observed, threshold,
                           "Unsubscribe/mirror presence is not fully known.", refs)
    if unsub is True and mirror is True:
        return CheckResult("PF-06", "Link/mirror sanity", "required", "pass", observed, threshold,
                           "Unsubscribe and mirror indicators are present.", refs)
    missing = []
    if unsub is not True:
        missing.append("unsubscribe")
    if mirror is not True:
        missing.append("mirror page")
    return CheckResult("PF-06", "Link/mirror sanity", "required", "fail", observed, threshold,
                       f"Required link indicators missing: {', '.join(missing)}.", refs)


def check_pf07_schedule_timezone(campaign: dict[str, Any]) -> CheckResult:
    schedule = campaign.get("schedule") or {}
    send_at = schedule.get("send_at")
    tz = schedule.get("timezone")
    observed = {"send_at": send_at, "timezone": tz}
    threshold = {"send_at_present": True, "timezone_present": True}
    refs = _ref(campaign.get("campaign_id"), "schedule")
    if not send_at or not tz:
        return CheckResult("PF-07", "Schedule/timezone sanity", "required", "fail", observed, threshold,
                           "Schedule or timezone is missing.", refs)
    # ISO-8601 parse + IANA timezone validation. Business-calendar rules (quiet hours,
    # send-in-past vs. a reference clock) are environment-specific and out of MVP scope.
    if _parse_iso_datetime(send_at) is None:
        return CheckResult("PF-07", "Schedule/timezone sanity", "required", "fail", observed, threshold,
                           "Send time format is not recognized; expected an ISO-8601 datetime.", refs)
    tz_status = _timezone_status(tz)
    observed["timezone_validation"] = tz_status
    if tz_status == "invalid":
        return CheckResult("PF-07", "Schedule/timezone sanity", "required", "fail", observed, threshold,
                           f"Timezone '{tz}' is not a recognised IANA timezone (e.g. Europe/Berlin).", refs)
    if tz_status == "unverifiable":
        return CheckResult("PF-07", "Schedule/timezone sanity", "required", "pass", observed, threshold,
                           "Schedule is valid ISO-8601; timezone present but not verifiable "
                           "(no timezone database installed - `pip install tzdata`).", refs)
    return CheckResult("PF-07", "Schedule/timezone sanity", "required", "pass", observed, threshold,
                       "Schedule and timezone are present (format sanity check passed).", refs)


def check_pf08_workflow_readiness(campaign: dict[str, Any]) -> CheckResult:
    workflow = campaign.get("workflow") or {}
    status = workflow.get("status")
    deps_ok = workflow.get("dependencies_ok")
    pending = workflow.get("pending_approvals")
    observed = {"status": status, "dependencies_ok": deps_ok, "pending_approvals": pending}
    threshold = {"dependencies_ok": True, "pending_approvals": 0}
    refs = _ref(campaign.get("campaign_id"), "workflow")
    if status is None or deps_ok is None or pending is None:
        return CheckResult("PF-08", "Workflow/dependency readiness", "required", "not_ready", observed, threshold,
                           "Workflow readiness evidence is incomplete.", refs)
    try:
        pending_n = int(pending)
    except (TypeError, ValueError):
        return CheckResult("PF-08", "Workflow/dependency readiness", "required", "fail", observed, threshold,
                           "Pending approvals value is invalid.", refs)
    if deps_ok is True and pending_n == 0 and str(status).lower() in {"ready", "ok", "approved", "pass"}:
        return CheckResult("PF-08", "Workflow/dependency readiness", "required", "pass", observed, threshold,
                           "Workflow dependencies and approvals are ready.", refs)
    reasons = []
    if deps_ok is not True:
        reasons.append("dependencies not ready")
    if pending_n != 0:
        reasons.append(f"{pending_n} pending approval(s)")
    if str(status).lower() not in {"ready", "ok", "approved", "pass"}:
        reasons.append(f"status={status}")
    return CheckResult("PF-08", "Workflow/dependency readiness", "required", "fail", observed, threshold,
                       "Workflow not ready: " + ", ".join(reasons) + ".", refs)


def run_all_checks(campaign: dict[str, Any], policy: dict[str, Any] | None = None) -> list[CheckResult]:
    policy = {**DEFAULT_POLICY, **(policy or {})}
    return [
        check_pf01_audience_present(campaign),
        check_pf02_audience_drift(campaign, policy),
        check_pf03_suppression_consent(campaign),
        check_pf04_proof_seed(campaign, policy),
        check_pf05_personalization(campaign),
        check_pf06_links_mirror(campaign),
        check_pf07_schedule_timezone(campaign),
        check_pf08_workflow_readiness(campaign),
    ]
