# 2026-07-18 — B6 config-drift flags: code-referenced vs declared env NAMES

> **Status:** `in-progress` — branch `claude/env-config-drift`; born-red card
> committed first (the gate HOLDs the merge red until this badge flips to
> `complete` as the session's last commit). B6 from the backlog (owner-decided
> **Q1=a**: a CONTAINED, NAMES-ONLY, STATIC check — never a value, never a live
> Railway/secret call in the running service).

- **📊 Model:** Claude Opus 4.8 · high · feature build

**What this session is about:** the gated `/owner/environments` page already
holds two of the three env-name views it needs — the COMMITTED per-service
declared manifest (`app/railway.py` `SERVICES`: names + a one-line purpose
each) and the LIVE Railway variable NAMES, DIFFED against each other by
`app/envdrift.py` (committed-vs-live). B6 adds the missing THIRD axis:
**code-referenced-vs-declared** drift. A static AST scan of each service's
runtime source (`app/gen_env_coderefs.py`, the `review/gen_*.py` build-time
idiom) records the env-var NAMES the code actually reads into a committed
names-only snapshot (`app/data/env_coderefs.json`); a pure diff
(`app/codedrift.py`) then flags two classes per service:
**referenced-but-undeclared** (code reads a var the manifest omits → a deploy
silently gets an empty value, no warning) and **declared-but-unreferenced** (the
manifest lists a var no code reads → stale/unused). Names only, both halves
static/committed — the deployed control-plane never scans source (its image
ships only `app/`) nor calls Railway; it reads the baked snapshot.

⚑ Self-initiated: no — coordinator-dispatched (B6, Q1=a).

## Close-out

**Evidence:**

- _(filled at flip)_ [[fill: build + wiring + template + tests + verify]]

**Judgment:**

- _(filled at flip)_ [[fill: decisions + next-session note]]

## 💡 Session idea

- _(filled at flip)_ [[fill: one idea]]

## ⟲ Previous-session review

- _(filled at flip)_ [[fill: one-line review of the o020-verified-ledger card]]
