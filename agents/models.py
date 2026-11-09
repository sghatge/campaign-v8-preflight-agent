from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

VERDICTS = ("PASS", "RISK", "FAIL", "NOT_READY")
RESULTS = ("pass", "risk", "fail", "not_ready")
SEVERITIES = ("required", "warning")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CheckResult:
    check_id: str
    name: str
    severity: str
    result: str
    observed: dict[str, Any]
    threshold: dict[str, Any]
    explanation: str
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    run_id: str
    campaign_id: str
    verdict: str
    checks: list[CheckResult]
    summary: str
    adapter_mode: str = "mock"
    started_at: str = field(default_factory=utc_now)
    finished_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checks"] = [c.to_dict() for c in self.checks]
        return data
