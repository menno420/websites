# 2026-07-13 — Agent-PR diagnostic tree (/agent-pr-check)

> **Status:** `complete` — branch `claude/agent-pr-diagnostic`; the static
> GET-only diagnostic tree at /agent-pr-check on botsite is built: 7
> questions and 14 cited leaves walking a visitor through the fleet's
> proven agent merge-wall lore (verbatim production errors + verified
> fixes), committed JSON + stdlib loader + recursive details/summary
> template, honest coming-soon CTA for the Merge-Wall Cookbook; lands via
> the normal PR path (auto-merge enabler on green).

- **📊 Model:** Claude Fable 5 · worker · initiation-slice

**What this session was about:** initiation under ORDER 022 item 4
(`control/inbox.md` @ `2a4c78a` — SCAN AND INITIATE; venture WEBSITE-IDEA
markers are priority intake). The marker (venture-lab `control/outbox.md`,
2026-07-13 morning-tally WEBSITE-IDEA batch 2, verbatim): "'Can your agent
land its own PR?' diagnostic tree". The build: an interactive-but-static
decision tree that tells a visitor exactly why their AI agent cannot open
or merge its own pull request — every branch drawn from this fleet's real
production walls (verbatim error strings, verified fixes), every leaf
cited to file@sha or a fleet-doc URL, with an honest coming-soon CTA for
The Agent Merge-Wall Cookbook per `botsite/data/catalog.json`.

## What was done

- `botsite/data/agent_pr_tree.json` — the committed tree: 7 question nodes
  + 14 leaves, every leaf verdict + concrete fix + ≥1 citation
  (`docs/CAPABILITIES.md@2a4c78a`, `docs/owner/OWNER-ACTIONS.md@2a4c78a`,
  the four `.github/workflows/*@2a4c78a` landing-machinery files, and the
  fleet-manager enabler-install-verification + substrate-kit lab-loop
  findings URLs). Verbatim production errors stored exactly as captured —
  the Actions `createPullRequest` refusal, the session-gate 403 JSON, the
  org-app install line, the live self-merge classifier refusal — nothing
  invented or paraphrased.
- `botsite/agent_pr_tree.py` — stdlib-only loader mirroring `graveyard.py`:
  validates meta (title/as_of/sources), explicit root, node ids, option
  targets resolving, cited leaves (uncited lore degrades the whole tree),
  and acyclicity (a cycle would infinitely recurse the template); returns
  `available: False` + exact reason on any miss; module-level
  `TREE_JSON_PATH` for test monkeypatching.
- `botsite/app.py` — GET `/agent-pr-check` in the exact handler idiom
  (`ds.fetch_site` → `_base_ctx` → TemplateResponse), long provenance
  docstring, NAV entry `("agent-pr-check", "PR Check", "/agent-pr-check")`;
  the cookbook CTA state is read from the committed catalog at request
  time (publish-ready + `url: null` → coming-soon, never a buy link). No
  state-changing routes.
- `botsite/templates/agent_pr_check.html` — sb-page-hero + h1 + sb-lead
  (structural gate #241 walks it green with NO registry entry — verified,
  not guessed); recursive Jinja macro rendering nested native
  `<details>`/`<summary>` (zero JS): question nodes are details with the
  question as summary, options nest their subtrees; leaves are sb-panel
  verdict cards with polarity badges (`sb-badge-ok` proven pattern /
  `sb-badge-danger` verified wall), verbatim `sb-mono` error strings,
  the fix, and citation lines; `sb-empty` honest degrade branch;
  provenance footer with sources + as_of.
- `botsite/tests/test_agent_pr_check.py` — 19 network-free tests: page +
  nav + GET-only pins; honesty pins (every committed leaf's verdict, fix,
  error and citations render; every option target resolves in the RAW
  JSON; the verbatim Actions error appears exactly once in the data);
  cookbook CTA honesty pin (no buy/checkout link, coming-soon copy
  consistent with catalog.json's publish-ready + null url); degrade tests
  via `TREE_JSON_PATH` monkeypatch (missing / corrupt / unresolvable ref →
  page still 200 with sb-empty); loader unit tests incl. cycle rejection.
- `docs/ideas/backlog.md`: this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1126 passed, 1 warning (+19 over this branch-base's
  1107, main @ `2a4c78a`); `python3 bootstrap.py check --strict` — green
  (exit-affecting findings: none; the CI added-card lane shows this card's
  own designed born-red HOLD, flipped by this commit: `[session-card-hold]
  .sessions/2026-07-13-agent-pr-diagnostic.md: born-red HOLD: this PR ADDS
  a session card that declares an in-progress/drafted Status`); plus the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: yes — an initiation under ORDER 022 item 4's standing
venture-marker intake (marker: venture-lab `control/outbox.md`, 2026-07-13
morning-tally WEBSITE-IDEA batch 2); contained (one new GET route +
committed data on botsite, no live fetch, no payment surface, one NAV
entry) and reversible (revert the PR).

## 💡 Session idea

**Cited-fact drift pin for /agent-pr-check — nag when the tree's quoted
sources move on main** — every leaf in `botsite/data/agent_pr_tree.json`
quotes facts pinned at `@2a4c78a` (guard wording from
`auto-merge-enabler.yml`, the fast-lane rationale from `quality.yml`, the
landing ladder from `review-bake.yml`, wall entries from
`docs/CAPABILITIES.md`). A CI-time check that extracts each `file@sha`
citation, verifies the path still exists, and diffs the cited file between
the pinned sha and HEAD (pure `git diff --name-only <sha>..HEAD -- <path>`
— no network) would nag when a cited source changed while the tree still
quotes its old text. Worth having because this page's whole value is
"every verdict cited" — a workflow guard rewritten upstream while the tree
still quotes the old wording is exactly the rot the citations exist to
prevent. Deduped against `docs/ideas/backlog.md`: the catalog sha-drift
pin compares a pin against a REMOTE repo's HEAD over the raw channel, and
the storefront-freshness bullet is time-based; nothing checks THIS repo's
own file@sha citations against local HEAD, and nothing covers
agent_pr_tree.json. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (`.sessions/2026-07-13-venture-vetting-
catalog.md`, PR #248) holds up under evidence: #248 is merged on main
(`4ddb876`), the committed `botsite/data/catalog.json` really carries 22
entries in exactly the claimed 1 live / 12 publish-ready / 2 hard-gated /
7 parked breakdown (re-counted this session), its 15 catalog tests pass
green in today's suite, and its 💡 (the catalog sha-drift pin) was
genuinely captured in `docs/ideas/backlog.md` — the card's claims and the
repo agree on every point I could check. The honest gap: the card's own
freshness worry is already live — every entry pins venture-lab @ `2c039e3`
and the drift-pin idea that would notice upstream movement is still
`captured`, not built, so the catalog's honesty currently decays silently;
this session leaned on that same catalog (the cookbook CTA reads its
publish-ready/null-url state at request time), which makes the drift pin
worth promoting from backlog to a build slice soon.
