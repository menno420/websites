# 2026-07-10 — Rescue-landing of the 16:01Z routine session's work + Project env/instructions package

> **Status:** `complete` — fleet-manager worker session (owner dispatch via the
> coordinator). Work was finished before the PR opened, so the card ships
> complete in one commit (no in-flight window for a born-red hold to protect).

- **📊 Model:** claude-fable-5 · rescue + root-cause + console-text package

## What happened

The 2026-07-10 16:01Z routine-fired session (ORDER 008 first-fire) built real
work but could not land it. Its session card claimed branch
`claude/order008-manifest-smoke-2026-07-10` was pushed; the remote had **no
such branch** at ~19:15Z — the push never landed (its chat said so; the card
did not). The owner relayed its `git format-patch` to the fleet manager.

## Part 1 — rescue (done, separate PR)

- Applied the patch verbatim via `git am` onto a fresh
  `claude/order008-manifest-smoke-2026-07-10` off `main` (`d493792`).
- Verified locally: `python3 -m pytest tests/ -q` → 85 passed;
  `python3 bootstrap.py check --strict` → all checks passed.
- **PR #59**, `quality` green, squash-merged → `main` @ `2c89e96`.

## Part 2 — root cause (evidence in `docs/CAPABILITIES.md` append log 2026-07-10)

Three distinct gaps in a routine-fired websites session, characterized:

1. **No GitHub PR tooling in the toolset** (session's own ToolSearch probe) —
   instruction-text workaround only (branch + handoff); owner can attach
   GitHub tooling to the Project environment.
2. **`api.github.com` 403 from the session proxy** — verbatim: "GitHub access
   to this repository is not enabled for this session. Use add_repo…" — a
   per-session repo-grant gate; owner-side environment/repo attachment, not
   script-fixable.
3. **Push did not work**, contradicting the card — most consistent with the
   same missing repo grant; a commit-signing requirement (CCR env default:
   `commit.gpgsign=true` + `/tmp/code-sign` env-runner signer, observed in a
   sibling env's `/root/.gitconfig`; the session's chat mentioned a stop hook
   demanding SSH-signed commits) is the second candidate wall. A setup script
   cannot mint the credential but CAN probe and print the truth at provision.

## Part 3 — the package (this PR)

- `docs/project/setup-script.sh` — environment Setup-script field text:
  fail-soft (substrate-kit PR #47 lesson), Python 3.12 note, all three
  services' pinned deps + pytest, git identity + safe.directory, and a printed
  capability probe (signing config, ls-remote, push dry-run, api.github.com).
- `docs/project/project-instructions.md` — Custom Instructions text (5.4k
  chars): orientation order, landing path (branch → PR ready → squash on green
  `quality`, born-red card), ROUTINE-FIRED SESSION protocol (probe before
  claiming "pushed"; branch + card + heartbeat handoff; patch-to-owner only
  after a probe proves push dead), discovery rule, heartbeat-last,
  family-level model names. Grounding citations in the HTML footer.
- `docs/project/README.md` — where each text gets pasted; repo = source of truth.
- `docs/CAPABILITIES.md` — appended the landing-failure wall entry (verbatim
  errors + workaround).

## 💡 Session idea

**Heartbeat "landing-state" field**: add a `landing:` line to the
`control/status.md` format (`landing: all-merged` | `landing: branch <name>
pushed-unmerged` | `landing: LOCAL-ONLY work at <where>`) so the manager's
`/fleet` view can surface stranded work mechanically instead of a human
noticing a card/chat contradiction. Cheap: one line in `control/README.md`'s
format spec + the status template; the 16:01Z incident is exactly the case it
would have caught.

## ⟲ Previous-session review

The 16:01Z routine session did excellent bounded work (the manifest smoke
check is well-tested and its CAPABILITIES entries are exemplary), but it
committed the one sin its own discovery rule forbids: it **recorded an
unverified claim** ("branch is pushed") in three files. Improvement shipped
this session: the setup-script probe + the "never record 'pushed' without
`git ls-remote` proof" rule in the Project instructions and CAPABILITIES —
verification-before-recording is now written where every future session reads.
