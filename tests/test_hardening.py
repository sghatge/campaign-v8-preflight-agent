"""Milestone 1 hardening: CLI gate exit codes and PF-07 schedule/timezone validation."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agents.checks import _timezone_status, check_pf07_schedule_timezone
from app.run_preflight import EXIT_ERROR, EXIT_GATE, EXIT_OK, main


def run_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class TestGateExitCodes(unittest.TestCase):
    def test_default_is_report_only(self):
        code, out, _ = run_cli("--scenario", "synthetic-cmp-fail-003")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Verdict: FAIL", out)

    def test_fail_gate_blocks_fail(self):
        code, _, err = run_cli("--scenario", "synthetic-cmp-fail-003", "--fail-on", "fail")
        self.assertEqual(code, EXIT_GATE)
        self.assertIn("GATE", err)

    def test_fail_gate_allows_pass_and_risk(self):
        self.assertEqual(run_cli("--scenario", "synthetic-cmp-pass-001", "--fail-on", "fail")[0], EXIT_OK)
        self.assertEqual(run_cli("--scenario", "synthetic-cmp-risk-002", "--fail-on", "fail")[0], EXIT_OK)

    def test_risk_gate_blocks_risk(self):
        self.assertEqual(run_cli("--scenario", "synthetic-cmp-risk-002", "--fail-on", "risk")[0], EXIT_GATE)

    def test_audited_override_releases_gate(self):
        with tempfile.TemporaryDirectory() as td:
            audit = Path(td) / "audit.jsonl"
            code, out, _ = run_cli(
                "--scenario", "synthetic-cmp-fail-003", "--fail-on", "fail", "--audit", str(audit),
                "--approve", "--approver", "Named Approver",
                "--reason", "Synthetic demo: exercising the audited override path.",
            )
            self.assertEqual(code, EXIT_OK)
            self.assertIn("approve_override", out)
            types = [json.loads(line)["event_type"] for line in audit.read_text(encoding="utf-8").splitlines()]
            self.assertIn("approval.override", types)

    def test_rejected_override_is_input_error(self):
        code, _, err = run_cli("--scenario", "synthetic-cmp-fail-003", "--fail-on", "fail",
                               "--approve", "--approver", "Named Approver", "--reason", "short")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("at least 15", err)

    def test_unknown_scenario_is_input_error(self):
        code, _, err = run_cli("--scenario", "does-not-exist")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Scenario not found", err)

    def test_json_output_is_valid(self):
        code, out, _ = run_cli("--scenario", "synthetic-cmp-pass-001", "--json")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(json.loads(out)["verdict"], "PASS")


def pf07(send_at, tz):
    return check_pf07_schedule_timezone({"campaign_id": "t", "schedule": {"send_at": send_at, "timezone": tz}})


class TestPF07Schedule(unittest.TestCase):
    def test_valid_utc_z_suffix(self):
        self.assertEqual(pf07("2026-11-15T09:00:00Z", "Europe/London").result, "pass")

    def test_valid_offset(self):
        self.assertEqual(pf07("2026-11-15T09:00:00+01:00", "Europe/Berlin").result, "pass")

    def test_word_containing_t_is_rejected(self):
        # Prototype only checked for a 'T' character, so "Tuesday" used to pass.
        self.assertEqual(pf07("Tuesday", "Europe/London").result, "fail")

    def test_impossible_date_is_rejected(self):
        self.assertEqual(pf07("2026-13-45T09:00:00Z", "Europe/London").result, "fail")

    def test_missing_fields_fail(self):
        self.assertEqual(pf07(None, "Europe/London").result, "fail")
        self.assertEqual(pf07("2026-11-15T09:00:00Z", "").result, "fail")

    @unittest.skipIf(_timezone_status("Europe/London") == "unverifiable", "no tz database on this runner")
    def test_invalid_timezone_fails(self):
        result = pf07("2026-11-15T09:00:00Z", "Europe/Atlantis")
        self.assertEqual(result.result, "fail")
        self.assertEqual(result.observed["timezone_validation"], "invalid")


if __name__ == "__main__":
    unittest.main()
