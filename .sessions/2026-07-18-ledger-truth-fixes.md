# 2026-07-18 — Ledger/doc truth fixes (read-only claim + ASK recon)

> **Status:** `in-progress` — branch `claude/ledger-truth-fixes`; a DOCS/LEDGER
> truth PR (no product code, no serialized payload, no env, no workflow). It
> corrects a factually wrong wind-down claim and appends dated recon/clarify
> notes to two open owner asks. Four corrections: **(A)** the repo does NOT go
> read-only on 2026-07-21 — only the Claude Code Projects EAP *session surface*
> winds down; the repo + all four Railway services stay live/writable and work
> continues via normal chat, so the deadline-pressure framing is removed;
> **(B)** ASK-0002 (Discord OAuth) gains a dated recon note (0/4 live services
> have Discord login) — status stays OPEN; **(C)** ASK-0007 (the O-020 write
> PAT) gains a status clarification (code fully built/merged; only the Railway
> `GITHUB_TOKEN` paste + a live commit-SHA confirm remains; plus the
> direct-to-main vs `WRITEBACK_BRANCH`+PR design question) — stays OPEN;
> **(D)** CAPABILITIES records the PAT-proxy wall (the agent seat cannot
> exercise a GitHub PAT against api.github.com; the proxy overrides the auth
> header, so PAT write scope must be verified live on Railway).

- **📊 Model:** Claude Opus 4.8 · high · docs-only

**What this session is about:** two owner-live corrections + two recon findings
converge on one truth PR. The living ledger and current-state doc carried a
deadline-pressure claim — "the repo goes read-only 2026-07-21 (read-only
Tuesday)" — that is wrong: only the EAP agent apparatus (the Projects session
surface) winds down; the repo stays a normal writable GitHub repo the owner
drives via chat afterward, and the four Railway services keep serving. Left
uncorrected, that claim manufactures false urgency ("land before then",
"freezes") on every future card. Alongside it, two open owner asks were
ambiguous: ASK-0002 (Discord OAuth) read as if a Discord login already existed
on these sites (it does not — recon proves 0/4), and ASK-0007 (the write PAT)
read as if writeback were unbuilt (the code is fully merged; only an owner infra
paste + a live confirm remains). This PR pins all four to truth.

⚑ Self-initiated: no — coordinator-dispatched ledger-truth correction.

## Close-out

**Evidence:**

- [[fill: corrections applied A-D with file:line]]
- files touched: [[fill]]
- git: [[fill: branch + commits]]
- verify: [[fill: four-suite + strict + require-session-log exit codes]]

**Judgment:**

- Decisions made: [[fill]]
- Next session should know: [[fill]]

## 💡 Session idea

[[fill: one idea]]

## ⟲ Previous-session review

[[fill: one-line review of .sessions/2026-07-18-test-coverage-bundle.md]]
