# 2026-08-13 — substrate-kit v1.20.1 → v1.21.0 (distribution wave, phase 3)

> **Status:** `complete` — branch `claude/substrate-kit-v1-21-0`, PR #499. This
> flip releases the born-red hold; the reviewed head is `86a9554` and the flip
> commit changes only this card's close-out text (the session-close exemption,
> taken and named).

- **📊 Model:** fable-5 · high · mechanical refactor

## previous-session review

The previous card (2026-07-18, arcade go-live) closed its two owner blockers
cleanly and left the repo dormant since — nothing it recorded contradicted the
tree this session found (vendored v1.20.1, pin v1.20.1, `kit: v1.20.1`, all
mutually consistent).

## Shipped

- Vendored dist v1.20.1 → v1.21.0 (`bootstrap.py`, sha256 `8807a00e…9cc7356`
  agreeing four ways: downloaded asset = sidecar = `release.json` = kit's
  committed `dist/bootstrap.py` @ `0021adc`), pin → 1.21.0, `control/status.md`
  `kit:` line → v1.21.0 (version token only). Commit `fc6c8b3`.
- Rollback banked byte-identical: `.substrate/backup/bootstrap-1.20.1.py`
  (`d6c4f815…` = pre-upgrade tree copy).
- Carve-out scan verbatim: `.github/workflows/auto-merge-enabler.yml — ran,
  0 found` · enabler `kept (kit-owned, already current)` — zero workflow
  changes in this PR.
- `docs/SKILLS.md` refreshed via `upgrade --apply-docs` (template-improved,
  consumer-untouched) after Codex round 1 caught the seat-digest naming
  `continuation-prompt` while the index predated it. Commit `86a9554`.

## Verify

- `python3 bootstrap.py check --strict` → exit 1 on exactly the designed
  born-red hold on this card (`HOLD (by design)`), nothing else; flips green
  with this commit.
- Codex: two rounds. R1 5 findings (1 P1) — 1 fixed here (`--apply-docs`),
  4 `[conceded]` as dist defects routed upstream. R2 6 findings — all
  `[conceded]` as dist defects, recorded as rows 8–12 of fleet-manager's
  `docs/findings/2026-08-13-substrate-kit-v1210-followups.md`; zero
  adopter-side changes owed, loop terminated at the two-round cap.

💡 The kit's own release checklist ends with "update the adopter's `kit:`
line", but nothing verifies the token matches the vendored header — a
one-line `currency`-side cross-check (self-report vs tree, already computed)
would turn silent drift into a DRIFT row automatically. Routed to the kit
worklist session.
