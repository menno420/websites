# 2026-07-14 — reconcile the automerge race on workflow-touching PRs (audit finding 4)

> **Status:** `complete` — PR #324, branch `claude/automerge-reconcile-0714`;
> workflow-touching PRs now park deterministically under the kit enabler's own
> `do-not-automerge` carve-out (label first, disarm, one settle re-check). This
> PR touches `.github/workflows/**`, so it parks itself by design —
> owner-merge-only is the fix working, not a failure.

- **📊 Model:** Claude Fable 5 · medium · runtime bugfix (CI automerge-race reconciliation)

**What this session was about:** order — the fleet cleanup audit
(`docs/audits/2026-07-13-fleet-cleanup-audit.md`, finding/suggestion 4, landed
via PR #312) flags the self-documented unreconciled overlap between the
kit-owned `auto-merge-enabler.yml` (arms squash auto-merge on non-draft
`claude/*` PRs on `pull_request` events, no workflow-touching rail) and the
host-owned `host-automerge-extras.yml` (wants workflow-touching PRs
owner-merge-only). On a PR touching `.github/workflows/**` the two race —
PR #321 observed it live: on the final head, host `arm-on-open` disarmed at
01:41:09Z and the kit `enable-auto-merge` re-armed at 01:41:25Z (its 15 s
label-grace sleep means the kit arm reliably lands AFTER the host disarm), so
the rail was defeated and the workflow-touching PR auto-merged anyway.

## What was done

- `.github/workflows/host-automerge-extras.yml` (the ONLY file changed —
  `auto-merge-enabler.yml` is kit-owned and regenerated in place on every
  `bootstrap.py` adopt/upgrade, byte-identical today to the staged
  `.substrate/ci/auto-merge-enabler.yml`; hand edits there are overwritten
  and flagged as carve-outs, which is exactly how this host file was born):
  the workflow-touching rail now PARKS instead of fighting — it applies the
  `do-not-automerge` label FIRST (the kit enabler's own documented carve-out,
  honored by its job-level `if` on every future event AND by its fresh
  pre-arm API label re-read on the current event), then disarms, then does
  one settle re-check after the kit's arm window to catch the narrow
  same-event interleaving where the kit's re-read predates the label.
  Deterministic final state: parked (labeled + not armed), owner-merge-only.
- Header comment rewritten: the "KNOWN OVERLAP (lane-owed to reconcile)"
  caveat is gone, replaced by the reconciled-behavior description.
- `permissions:` gains `issues: write` (repo-level ensure-create of the
  `do-not-automerge` label — it did not exist in the repo yet).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1389 passed; `python3 bootstrap.py check --strict` —
  green except this card's own designed born-red HOLD.

⚑ Self-initiated: no — audit finding 4 reconciliation, coordinator-assigned.

## 💡 Session idea

**Teach the sweep job the `do-not-automerge` label** — the half-hourly sweep
in `host-automerge-extras.yml` selects open unarmed `claude/*` PRs and arms
them without ever checking labels; a PR the owner (or the new rail) parked
with `do-not-automerge` but that does NOT touch `.github/workflows/**` would
be re-armed by the next sweep, silently overriding the kit's own carve-out.
Worth having because the label is now load-bearing for the reconciled rail,
and one `--jq` clause in the sweep's PR selection closes the only remaining
writer that ignores it. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: no existing bullet touches the sweep or the label.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The smoke-crawl session (PR #321) did well — a real browser-level standing
gate with honest scope cuts and a live 100-page proof; what it missed: its
own PR was the workflow-touching PR that demonstrated this race (armed by the
kit enabler 16 s after the host rail disarmed it), which this session now
closes. Also checked the venture-vetting-catalog card (2026-07-13): it
delivered what it claimed — 22 entries in `botsite/data/catalog.json`, the
`/products/catalog` route, loader and template all present with the honest
1/12/2/7 status breakdown pinned by its own test.
