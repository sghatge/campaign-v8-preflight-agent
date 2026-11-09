# Screenshots & GIF plan

Goal: each visual shows one **trust moment** from the story *problem → risk → agent check → human decision → audit record*. Reviewers skim images before reading code, so the images carry the governance story.

All captures use synthetic scenarios only. Put files in `/assets` with the names below; the README already references them.

## Shot list

| # | File | What to capture | Trust moment | How |
|---|---|---|---|---|
| 1 | `assets/01-demo-pass.png` | Demo UI, *Spring Reactivation*, green PASS badge and all 8 checks | Clean run, evidence for every check | Open `app/demo.html`, choose scenario, Run |
| 2 | `assets/02-demo-risk.png` | Demo UI, *Winback*, RISK badge, PF-02 row expanded (43.6% drift) | The agent flags; it doesn't silently pass | Same, RISK scenario |
| 3 | `assets/03-demo-fail.png` | Demo UI, *Black Friday Teaser*, FAIL badge with PF-03/05/06/08 failing | Release blocked before send | Same, FAIL scenario |
| 4 | `assets/04-cli-gate.png` | Terminal: FAIL run with `--fail-on fail` showing the `GATE:` line and `echo $?` → `1` | A CI pipeline can actually stop | See commands below |
| 5 | `assets/05-override-audit.png` | Terminal: override with approver + reason, then the `approval.override` line from `audit.jsonl` | Human decides; the decision is recorded | See commands below |
| 6 | `assets/06-ci-green.png` | GitHub Actions run: test matrix + gate-smoke all green | Claims are backed by CI | Crop the Actions summary |
| 7 | `assets/preflight-demo.gif` | 15–20 s: PASS → FAIL → override → audit line | Whole story in one loop | ScreenToGif (Windows) or LICEcap; ≤ 5 MB |

## Terminal commands for shots 4–5
```bash
python -m app.run_preflight --scenario synthetic-cmp-fail-003 --fail-on fail; echo "exit=$?"

python -m app.run_preflight --scenario synthetic-cmp-fail-003 --fail-on fail \
  --audit .local/audit.jsonl --approve --approver "Demo Approver" \
  --reason "Synthetic demo: suppression fix verified out-of-band."
grep approval.override .local/audit.jsonl
```

## Capture rules
- Width 1280–1440 px; dark or light theme, not both mixed across shots.
- Crop out the browser chrome, taskbar, file paths that show your Windows username, and any other open tabs.
- Approver names stay generic ("Demo Approver"). Never a real colleague.
- No Adobe Campaign console screenshots, real or redacted. The repo makes no claim of a live connection.
- Re-capture after any check-logic change. CI demo-parity keeps `demo.js` honest, but images don't update themselves.

## LinkedIn reuse
Lead with shot 3 or the GIF; the FAIL moment is the hook. Use shot 5 as the second image (the human decision). Shot 6 goes in the comments as proof.
