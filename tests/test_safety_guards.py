"""Safety guards that enforce the repo's public promises in CI.

1. No send capability: engine code imports no network, mail or process-spawning modules.
2. Leak guard: no real-looking emails, phone numbers, tokens or card numbers in tracked text.
3. .env.example holds placeholders only.
4. Demo parity: the static demo UI shows exactly what the engine produces.
"""

import ast
import json
import re
import unittest
from pathlib import Path

from app.run_preflight import run_scenario

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIRS = [ROOT / "agents", ROOT / "app"]
TEXT_SUFFIXES = {".py", ".md", ".json", ".js", ".html", ".css", ".yml", ".yaml", ".txt", ".example", ".toml", ""}
SKIP_DIRS = {".git", "__pycache__", ".local", ".venv", "venv", "node_modules"}

FORBIDDEN_IMPORTS = {
    "socket", "smtplib", "ssl", "http", "urllib", "ftplib", "telnetlib", "poplib", "imaplib",
    "requests", "httpx", "aiohttp", "urllib3", "subprocess", "paramiko",
}

LEAK_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\+\d[\d\s-]{9,}\d"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "openai_style_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "card_number": re.compile(r"\b(?:\d[ -]?){15,16}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def tracked_text_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


class TestNoSendCapability(unittest.TestCase):
    def test_engine_imports_no_network_or_process_modules(self):
        offenders = []
        for d in ENGINE_DIRS:
            for py in d.rglob("*.py"):
                tree = ast.parse(py.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                        names = [node.module]
                    for n in names:
                        if n.split(".")[0] in FORBIDDEN_IMPORTS:
                            offenders.append(f"{py.relative_to(ROOT)} imports {n}")
        self.assertEqual(offenders, [], "Engine must stay read-only with no network/send path")

    def test_demo_js_makes_no_network_calls(self):
        js = (ROOT / "app" / "demo.js").read_text(encoding="utf-8")
        for token in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"):
            self.assertNotIn(token, js)


class TestLeakGuard(unittest.TestCase):
    def test_no_sensitive_patterns_in_repo(self):
        hits = []
        for path in tracked_text_files():
            if path.name == Path(__file__).name:
                continue  # this file defines the patterns
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in LEAK_PATTERNS.items():
                for m in pattern.finditer(text):
                    hits.append(f"{path.relative_to(ROOT)}: {label}: {m.group(0)[:40]}")
        self.assertEqual(hits, [], "Possible sensitive data found:\n" + "\n".join(hits))

    def test_env_example_has_placeholders_only(self):
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            key, _, value = stripped.partition("=")
            value = value.split("#")[0].strip()
            if any(word in key for word in ("SECRET", "TOKEN", "PASSWORD", "CLIENT_ID", "BASE_URL")):
                self.assertEqual(value, "", f"{key} must be empty in .env.example")

    def test_no_dotenv_committed(self):
        self.assertFalse((ROOT / ".env").exists(), ".env must never be committed")


class TestDemoParity(unittest.TestCase):
    """The demo UI hardcodes results; fail CI if it drifts from the engine."""

    BLOCK_RE = re.compile(r"id:\s*'(synthetic-[^']+)'")
    VERDICT_RE = re.compile(r"verdict:\s*'([A-Z_]+)'")
    CHECK_RE = re.compile(r"\{id:'(PF-\d+)'.*?result:'([a-z_]+)'")

    def parse_demo(self, js: str) -> dict:
        starts = [(m.start(), m.group(1)) for m in self.BLOCK_RE.finditer(js)]
        demo = {}
        for i, (pos, cid) in enumerate(starts):
            block = js[pos: starts[i + 1][0] if i + 1 < len(starts) else len(js)]
            demo[cid] = (self.VERDICT_RE.search(block).group(1), dict(self.CHECK_RE.findall(block)))
        return demo

    def test_demo_matches_engine(self):
        js = (ROOT / "app" / "demo.js").read_text(encoding="utf-8")
        data = json.loads((ROOT / "data" / "synthetic" / "example-campaigns.json").read_text(encoding="utf-8"))
        by_id = {c["campaign_id"]: c for c in data}
        demo = self.parse_demo(js)
        self.assertEqual(set(demo), set(by_id), "Demo scenarios must match synthetic data")
        for cid, (demo_verdict, demo_checks) in demo.items():
            run, _ = run_scenario(by_id[cid])
            self.assertEqual(demo_verdict, run.verdict, f"{cid}: demo verdict drifted")
            self.assertEqual(demo_checks, {c.check_id: c.result for c in run.checks},
                             f"{cid}: demo check results drifted")


if __name__ == "__main__":
    unittest.main()
