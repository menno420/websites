# 2026-07-15 — Launch preflight verdicts: auto-verified owner asks

> **Status:** `complete` — PR #348, branch
> `claude/launch-preflight-verdicts-20260715`; new domain module
> `app/askverify.py` + verdict chips on the gated owner console
> (/owner, /owner/briefing, /owner/queue); public /queue byte-identical.

- **📊 Model:** Claude Fable · medium · feature build (askverify domain module + owner console verdict chips)

**What this session is about:** the mission phrase "auto-verified
owner-actions", implemented as read-only launch-preflight verdicts. A new
domain module `app/askverify.py` holds a probe REGISTRY keyed by stable
keyword signatures matched against the parsed ⚑ OWNER-ACTION asks (the
same `owner_queue.parse_owner_actions` parse /queue and the briefing use).
Each matched ask gets a live, side-effect-free probe (GETs and the existing
read-only Railway names query only — never a write, never a value fetched)
and renders a verdict chip on the GATED owner console surfaces:
`/owner/briefing` asks section, `/owner/queue` cards, and a one-line
rollup chip on the `/owner` board ("N of M asks machine-verified").

Verdict ladder (honest-unknown beats inferred-done, everywhere):
`done-detected` (positive probe; wording carries "ledger update pending") /
`still-open` / `not machine-checkable — <reason>` / `unknown — <probe
error>`. Unmatched or ambiguously-matched asks stay honestly unverified —
no fuzzy-match tuning. The public `/queue` stays byte-identical (pinned by
test). Zero new POST routes.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice.

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-launch-preflight-verdicts.md`
  + `control/claims/claude-launch-preflight-verdicts-20260715.md` (first
  commit; claim deleted at this flip), `app/askverify.py` (new — registry,
  6 live probes, 5 explicit not-machine-checkable registrations, claim-once
  annotate + rollup), `app/briefing.py` (asks() gains `verify`),
  `app/owner.py` (/owner/queue annotation, /owner board `askcov`),
  `app/templates/owner.html` + `owner_briefing.html` + `owner_queue.html`
  (chips + rollups), `tests/test_askverify.py` (new, 28 tests),
  `tests/test_prompt_surfacing.py` (`_patch_owner_siblings` cans the new
  briefing.asks sibling — the one existing-test edit needed).
- probes, all read-only: botsite SITE_PASSWORD via GET `/testing/owner`
  (503 fail-closed = still-open / 401 challenge = done-detected); BAKE_PAT
  among websites Actions secret NAMES; ORDER-020 contents-write PAT via
  `permissions.push` on GET /repos/menno420/websites (a write is NEVER
  attempted); dashboard SITE_PASSWORD deletion via the names-only
  `railway.live_overview` ladder; gba-homebrew `lumen-drift-v1.3` release
  tag + product-forge Pages status (public GETs). Q-0004 / Discord OAuth /
  armed-service token / botsite DATABASE_URL / PayPal creds registered
  explicitly not machine-checkable with reasons. Matcher verified against
  the REAL committed ledger: all 9 open asks matched, 9 distinct entries.
- git: branch `claude/launch-preflight-verdicts-20260715`, based on `main`
  @ `8fb3ac5`; PR #348. Work in an isolated `git worktree` (the recorded
  EnterWorktree wall — manual worktree substitute).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1442 passed, 1 warning** (was 1414 at base; +28);
  `python3 bootstrap.py check --strict` — green except the DESIGNED
  born-red hold on this card (released by this flip; seat-digest-stale and
  orientation-headroom advisories pre-exist on main `8fb3ac5`).

**Judgment:**

- Decisions made: (1) matching is claim-once per pass — a second ask
  hitting an already-claimed registry entry gets the honest "ambiguous —
  never a verdict" chip, so done-detected can never ride an ambiguous
  signature; (2) annotation happens in the GATED route / briefing
  composition only — `owner_queue.overview()` is untouched, which is what
  keeps the public /queue byte-identical by construction (and pinned by a
  probes-must-not-run test); (3) the ORDER-020 chip's done-detected wording
  names the limit of its evidence (control-plane token only — the botsite
  half is not observable from here).
- Next session should know: 9/9 open asks matched the registry (0
  unmatched — well inside the ≤2 honesty tolerance, no fuzzy tuning
  needed). The chips are live on the next deploy; when the owner completes
  an errand the chip flips done-detected but the LEDGER row still needs its
  human move to Decided — the chip wording says "ledger update pending" for
  exactly that reason. Signatures are keyword-stable against today's ask
  texts; a reworded ask degrades to honest-unmatched, never a wrong match.

## 💡 Session idea

**Stable ask IDs in the OWNER-ACTIONS ledger** — askverify matches asks by
keyword signatures over their WHAT lines, which is deliberately
conservative: a reworded ask silently falls to honest-unmatched. If each
`⚑ OWNER-ACTION` block carried one extra line (`ID: ASK-NNNN`, assigned
once, never reused), the probe registry could key on exact IDs — matching
becomes drift-proof, the claim-once ambiguity rung disappears, and the
same IDs give /owner/queue writeback targets and the reconcile ritual a
stable join key across ledger edits. Cheap: the parser already tolerates
unknown lines; only new asks need IDs. Deduped against
`docs/ideas/backlog.md`: no ask-ID / ledger-key bullet exists (the ledger
appears there only as a fetch source), and no session card proposes it.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` is this card's format
reference and its close-out held up under reuse: its recorded EnterWorktree
wall (manual `git worktree add` substitute) was consumed verbatim by this
session's isolation setup — the wall entry paid for itself one session
later, which is the capability ledger working as designed. One observation:
its evidence section pins the advisory baseline ("seat-digest-stale and
orientation-headroom pre-exist on main, verified against a pristine
baseline worktree"), and this session leaned on that pin instead of
re-deriving the baseline — a small but real compounding effect of honest
close-outs. Improvement it points at: it fixed model-line grammar across
fourteen cards by hand; the window-0 sweep idea it filed would have made
that a one-command check — still worth promoting.
