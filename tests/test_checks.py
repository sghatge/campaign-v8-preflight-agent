import json
import tempfile
import unittest
from pathlib import Path

from agents.checks import run_all_checks
from agents.verdict import aggregate_verdict
from app.run_preflight import run_scenario


DATA = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "example-campaigns.json"


def load(campaign_id: str) -> dict:
    items = json.loads(DATA.read_text(encoding="utf-8"))
    return next(i for i in items if i["campaign_id"] == campaign_id)


class TestSyntheticScenarios(unittest.TestCase):
    def test_pass_scenario(self):
        run, _ = run_scenario(load("synthetic-cmp-pass-001"))
        self.assertEqual(run.verdict, "PASS")
        self.assertTrue(all(c.result == "pass" for c in run.checks))

    def test_risk_scenario_audience_drift(self):
        run, _ = run_scenario(load("synthetic-cmp-risk-002"))
        self.assertEqual(run.verdict, "RISK")
        pf02 = next(c for c in run.checks if c.check_id == "PF-02")
        self.assertEqual(pf02.result, "risk")
        self.assertGreater(pf02.observed["drift_abs_pct"], 30)

    def test_fail_scenario_has_required_failures(self):
        run, _ = run_scenario(load("synthetic-cmp-fail-003"))
        self.assertEqual(run.verdict, "FAIL")
        failed_required = {c.check_id for c in run.checks if c.severity == "required" and c.result == "fail"}
        self.assertTrue({"PF-03", "PF-05", "PF-06", "PF-08"}.issubset(failed_required))

    def test_all_checks_emit_evidence(self):
        run, _ = run_scenario(load("synthetic-cmp-fail-003"))
        for c in run.checks:
            self.assertIn(c.result, {"pass", "risk", "fail", "not_ready"})
            self.assertIsInstance(c.observed, dict)
            self.assertIsInstance(c.threshold, dict)
            self.assertTrue(c.explanation)

    def test_override_requires_reason_for_fail(self):
        with self.assertRaises(ValueError):
            run_scenario(load("synthetic-cmp-fail-003"), approve=True, approver="Named Approver", reason="short")

    def test_override_requires_approver_for_fail(self):
        with self.assertRaises(ValueError):
            run_scenario(load("synthetic-cmp-fail-003"), approve=True, approver=None, reason="This is a long enough override reason.")

    def test_override_records_distinct_event(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = Path(td) / "audit.jsonl"
            run, approval = run_scenario(
                load("synthetic-cmp-fail-003"),
                audit_path=str(audit_path),
                approve=True,
                approver="Named Approver",
                reason="Synthetic demo: exercising override logging for a failed pre-flight result.",
            )
            self.assertEqual(run.verdict, "FAIL")
            self.assertEqual(approval["decision"], "approve_override")
            events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
            types = [e["event_type"] for e in events]
            self.assertIn("approval.decision", types)
            self.assertIn("approval.override", types)
            override = next(e for e in events if e["event_type"] == "approval.override")
            self.assertEqual(override["original_verdict"], "FAIL")
            self.assertEqual(override["approver"]["name"], "Named Approver")

    def test_pass_approval_has_no_override_event(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = Path(td) / "audit.jsonl"
            run, approval = run_scenario(
                load("synthetic-cmp-pass-001"),
                audit_path=str(audit_path),
                approve=True,
                approver="Named Approver",
                reason="Approved.",
            )
            self.assertEqual(run.verdict, "PASS")
            self.assertEqual(approval["decision"], "approve")
            events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
            self.assertNotIn("approval.override", [e["event_type"] for e in events])


if __name__ == "__main__":
    unittest.main()
