# Release checklist: v0.1.0 (Milestone 1)

Applied from the portfolio-wide `RELEASE-CHECKLIST.md`.
**✅ = done and verified in this package · ☐ = needs you (reason given)**

## 1. Scope & honesty
- ✅ README opens with problem, audience, what the agent checks, and where a human decides.
- ✅ **Known limits** section is accurate: mock adapter, synthetic data, no RBAC, unimplemented parts of PF-07.
- ✅ Claims match code. `docs/checks.md` now separates the target catalog from what v0.1 implements. The earlier doc claimed PF-07 checked send-in-past; it doesn't yet.
- ✅ `CHANGELOG.md` written for v0.1.0.
- ☐ Set the release date in `CHANGELOG.md` when you tag.

## 2. Safety & data
- ✅ Synthetic data only. All three scenarios are fictional; no real names, emails or IDs.
- ✅ Leak guard runs in CI (`tests/test_safety_guards.py`) and was proven to catch a planted email address.
- ✅ No-send guard: CI fails if `agents/` or `app/` import any network, mail or process module. Proven with a planted `import smtplib`.
- ✅ `.env.example` has placeholders only (enforced by test); `.gitignore` excludes `.env` and `.local/`.
- ☐ **Manual pass before going public:** the automated guard can't judge context. Skim every file once for employer, client or market references.
- ☐ Optional: enable GitHub secret scanning and push protection (Settings → Code security).

## 3. Agent governance
- ✅ Agent contract in `docs/agent-contract.md`.
- ✅ FAIL/NOT_READY override needs a named approver plus a reason of at least 15 characters.
- ✅ Override logged as a distinct `approval.override` event; schema in `docs/audit-schema.md`.
- ✅ The `--fail-on` gate is released only by a recorded approval.
- Known gap (documented, not blocking v0.1): approvers are self-declared and self-approval isn't prevented. Two-person override is planned for v0.2.

## 4. Quality & reproducibility
- ✅ 28 tests pass on Python 3.10, 3.11, 3.12 and 3.13 (run locally on Linux).
- ✅ CI workflow covers Ubuntu + Windows × Python 3.10–3.13, plus a CLI gate smoke test.
- ☐ **Confirm the first CI run is green on GitHub.** Windows runners weren't available here; the tz-database fallback was written for them, but Windows itself is untested.
- ☐ Add the CI badge. It's already in the README; it renders once the repo exists at `sghatge/campaign-v8-preflight-agent`.
- ✅ "Run locally" commands verified, with expected output shown in the README.
- ✅ Demo scenarios cover PASS, RISK, FAIL and override.
- ✅ Demo-parity test fails CI if `app/demo.js` drifts from the engine (proven by injecting drift).

## 5. Demo & publishing
- ☐ Enable GitHub Pages (Settings → Pages → `main` / root) so the demo is at `https://sghatge.github.io/campaign-v8-preflight-agent/app/demo.html`.
- ☐ Set the repo **Homepage** URL to the demo link.
- ☐ Test the demo on desktop and mobile.
- ☐ Capture screenshots/GIF per `docs/screenshots-plan.md`.
- ☐ **Choose a license** (see `LICENSE`). Until you do, the code is "all rights reserved" even though it's public.

## 6. Portfolio integration
- ☐ Add or update the project card on `sghatge.github.io` and in `SHOWCASE-ALL-IN-ONE.md`.
- ☐ Pin the repo if P1 becomes a flagship.
- ☐ LinkedIn post: story-first format, FAIL screenshot as the hook, one CTA.
- ☐ Cross-link from OPSFORGE, ACC Agent Gate and Safe to Send READMEs.

## Tag
```bash
git tag -a v0.1.0 -m "Milestone 1: read-only pre-flight engine on synthetic data"
git push origin v0.1.0
```
Then create a GitHub Release from the tag and paste the v0.1.0 section of `CHANGELOG.md`.
