# 2026-07-18 — Ledger/doc truth fixes (read-only claim + ASK recon)

> **Status:** `complete` — branch `claude/ledger-truth-fixes`; a DOCS/LEDGER
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

- corrections applied:
  - **(A) read-only claim corrected** — `docs/current-state.md`: the status
    badge (was line 4, "The Claude Code Projects EAP goes **read-only
    2026-07-21** (read-only Tuesday)") now reads "The Claude Code Projects EAP
    **session surface** winds down ~**2026-07-21**; the **repo + all four
    Railway services stay live and writable** and the owner continues via
    normal chat afterward (no repo freeze, no deadline)". The wind-down bullet
    (was line 118, "The EAP is winding down… goes **read-only on 2026-07-21
    (read-only Tuesday)**") is retitled "The EAP session surface is winding
    down — the repo is NOT" and states the repo stays a normal writable GitHub
    repo with **no repo read-only date and no land-before-then deadline**. The
    seven other `read-only` hits in the file (lines ~26/37/239/292/389/616/625)
    describe read-only *data surfaces* (dashboard oversight, the TTL-cache
    pattern, form-free interaction, the review render), NOT the repo — left
    unchanged. `control/status.md`'s own wrong claim (its old lines 13 + 38)
    was removed by the heartbeat rewrite (below).
  - **(B) ASK-0002 recon note** — `docs/owner/OWNER-ACTIONS.md`: appended a
    dated blockquote after the ASK-0002 block — 0/4 live websites-repo services
    have Discord *login* (`/login`+`/auth/callback` → 404; dashboard
    `/admin/login` → 200 static "not configured"), the lookalikes are botsite's
    bot-*install* link (`botsite/data_source.py:33`) and dashboard's
    not-configured `/admin/login` stub (`dashboard/app.py:454`). Folded in the
    owner's mid-task evidence: the working login is the **SuperBot dashboard**
    (different fleet repo), so ASK-0002's cheapest path is likely REUSE of the
    existing SuperBot Discord app vs a fresh one — pending owner preference.
    Status unchanged: **OPEN**.
  - **(C) ASK-0007 clarification** — `docs/owner/OWNER-ACTIONS.md`: appended a
    dated blockquote — O-020 writeback CODE is fully built/merged
    (`app/writeback.py` + gated `/owner/queue` routes, honest SQLite degrade
    reading `GITHUB_TOKEN` live); only the Railway control-plane `GITHUB_TOKEN`
    paste + a live commit-SHA confirm remains, plus the direct-to-`main`
    (`DEFAULT_BRANCH`) vs `WRITEBACK_BRANCH`+PR design question. Status
    unchanged: **OPEN**.
  - **(D) CAPABILITIES PAT-proxy wall** — `docs/CAPABILITIES.md`: appended a
    dated `wall` finding — the agent seat CANNOT exercise a GitHub PAT against
    api.github.com (the HTTPS proxy overrides the Authorization header with the
    Claude-GitHub-App identity; proven with a garbage token returning identical
    results), so any PAT's write scope must be verified LIVE on Railway.
    `docs/seat-digest.md` regenerated (derived render) to carry this finding
    fleet-wide.
- files touched: `.sessions/2026-07-18-ledger-truth-fixes.md` (this card),
  `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`, `docs/CAPABILITIES.md`,
  `docs/seat-digest.md`, `control/status.md` (heartbeat). No product code,
  serialized JSON, env, or workflow.
- git: branch `claude/ledger-truth-fixes` from `origin/main` @ `42da7b7` (#395);
  commits `c67d6e0` (born-red card), `72cd41f` (corrections A–D), `4b0789a`
  (owner-evidence fold into ASK-0002 + seat-digest regen), `8a6b11d`
  (heartbeat), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1828 passed, 1 warning** (exit 0; the one warning is the pre-existing
  Starlette/httpx TestClient deprecation, not this work). `python3 bootstrap.py
  check --strict` and `--require-session-log` — the only red is the DESIGNED
  born-red hold on this card (exit 1 until this flip; released here). Verified
  the seat-digest advisory did NOT pre-exist on origin/main and regenerated it,
  so this PR introduces no new drift.

**Judgment:**

- Decisions made: (1) fixed ONLY the tracked-doc framing (`current-state.md` +
  the heartbeat body) and left the seven legitimate "read-only" data-surface
  usages and the completed `.sessions/` cards untouched — the claim was wrong
  about the *repo*, not about the sites being read-only data views. (2) Appended
  the ASK-0002/0007 notes as dated blockquotes rather than editing the WHAT/WHY
  fields, keeping the original ask text verbatim (the ledger's "do not delete,
  move / append" doctrine) and both statuses OPEN — these are recon findings,
  not resolutions. (3) Regenerated `docs/seat-digest.md` because my CAPABILITIES
  add is one of its two sources and the drift did not pre-exist — shipping the
  stale derived render would push a stale ledger fleet-wide.
- Next session should know: the read-only-Tuesday framing is now corrected in
  the tracked docs — do NOT reintroduce land-before-then urgency; only the EAP
  session surface winds down, the repo stays writable via normal chat. ASK-0002
  now points at REUSE of the existing SuperBot Discord OAuth app as the likely
  cheapest path (owner to choose reuse vs fresh). ASK-0007/O-020 is one owner
  infra paste + a design choice away from live — the code is done. The seat
  cannot verify a PAT against api.github.com (new CAPABILITIES wall).

## 💡 Session idea

**A "ledger-claim expiry" lint for dated absolute claims.** This PR existed
because a hard-dated wind-down claim ("read-only 2026-07-21") sat in the living
ledger as settled fact and silently manufactured deadline pressure on later
cards until an owner correction. The recurring class is a docs line that pins a
future-dated absolute ("goes read-only on <date>", "freezes <date>",
"deprecated after <date>") with no re-verification hook — it ages into a false
fact the moment reality diverges. A cheap kit check could grep the tracked docs
for future-dated claim phrases (a small verb list × an ISO date in the future)
and, once that date is within N days or past, emit an advisory nudging a
re-verify-or-rewrite — the same discovery-rule instinct CAPABILITIES already
applies to walls, extended to time-boxed ledger claims.

## ⟲ Previous-session review

`.sessions/2026-07-18-test-coverage-bundle.md` (X2) pinned three
existing-but-untested honesty signals (the `prs.capped` truncation flag, the
TTL-cache poison guard, the answer-debt nag) so a regression trips CI instead of
shipping silently — a "make the true thing un-regressable" move. This card is
the same instinct pointed at prose instead of code: it makes the *ledger* honest
(correcting a false wind-down claim, pinning two asks to their real state) the
way X2 made the *board's* signals honest — both replace a trusted-but-unverified
surface with a checked one.
