# 2026-07-12 — arcade probe: extend URL drift probe to download-availability entries

> **Status:** `in-progress` — branch `claude/arcade-download-probe`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** backlog promotion — the captured bullet
"Probe download-availability arcade URLs too" (`docs/ideas/backlog.md`,
source `.sessions/2026-07-12-arcade-url-drift-probe.md` 💡). The /arcade
page renders an outbound link for both `live` AND `download` entries with a
URL, but the drift probe shipped in PR #214 (`botsite/arcade_probe.py`) only
cold-fetches `live` entries — the moment lumen-drift's card flips to
`download`, its link re-enters the unverified-drift class the probe was
built to close. This session extends the probe's filter to `download`,
keeping final-200 semantics (redirect chains already followed via
`follow_redirects=True`; a FINAL redirect status stays flagged).

## What was done

- [[fill: changes with file paths]]
- Verified: [[fill: pytest + bootstrap check output]]

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

[[fill: one genuine idea, deduped against docs/ideas/backlog.md]]

## ⟲ Previous-session review

[[fill: one line on the envhub-group-chips session]]
