# 2026-07-12 — ORDER 021 slice 2: env-creation plan/manifest generator

> **Status:** `complete` — PR branch `claude/order-envhub-manifest`; one
> slice, lands via the auto-merge-enabler on green.

- **📊 Model:** claude-fable-5 · websites worker · order (ORDER 021)

**What this session was about:** ORDER 021 slice 2 (rung: order; slice 1 =
merged #202) — the "create the complete environments per project group"
half of the owner's directive, built strictly inside the
docs/RAILWAY-SAFETY.md boundary: for each registry project group, GENERATE
the complete-environment manifest (service definitions, env-var schema as
NAMES + placeholders, copyable owner-executed setup commands) — no
provisioning code, no Railway mutations, no API-key handling anywhere.

## What was done

- **Generator** `app/envhub.py`: `manifest(group_id)` builds the plan from
  the committed registry alone (no network): per-surface service
  definitions with the slice-1 manage-link ladder; env-var schema pairing
  every variable NAME with a kind-specific placeholder
  (`<SET-IN-RAILWAY-CONSOLE>` / `<SET-IN-GITHUB-SECRETS>` /
  `<SET-IN-CLAUDE-SETTINGS>` — never a value; none exists to leak, the
  slice-1 loader hard-rejects value-like fields); copyable setup commands
  (`railway variables --service … --set "NAME=<…>"`, console
  service-creation steps, `gh secret set` + `settings/secrets/actions`
  steps); unrecorded names render an honest record-by-PR note, never a
  guess. Single-source `BOUNDARY_NOTICE` constant.
- **Route** `GET /owner/environments-hub/manifest/{group}` in
  `app/owner.py` behind the exact `require_owner` gate (same Discord-OAuth
  seam), read-only; unknown group → 404.
- **Template** `owner_envhub_manifest.html`: boundary notice rendered
  prominently (banner), service-definitions + schema tables, and the same
  plan as copyable plain-text AND JSON `<pre>` blocks on the same gated
  page (copycode.js buttons) — no new unauthenticated endpoint.
- **Hub link-up** `owner_environments_hub.html`: per-group
  "create-complete-environment manifest →" link in each section; footer
  updated (slice 2 no longer "follows separately"). `app/nav.py` untouched
  (IA session owns it; slice 1's entry suffices).
- **Tests** `tests/test_envhub_manifest.py` (14): 401/503 gate, one
  manifest per known group renders, unknown group 404, the
  placeholders-never-values invariant (every generated `NAME=` is followed
  only by a `<…>` placeholder, page-level and commands-level), boundary
  notice present, no mutation strings in the generator source, honest
  unrecorded-names notes.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 719 passed; `python3 bootstrap.py check --strict` —
  green.

⚑ Self-initiated: no — ORDER 021 (slice 2 of the coordinator's slicing;
slice 1 merged as #202).

## 💡 Session idea

**Manifest completeness diff — "what is missing to finish this
environment"** — merge the slice-1 live variable-NAME read into the
manifest page so each schema row shows set-live / missing-live for the
superbot-websites group, turning the plan into a checklist the owner can
run down. Worth having because the owner executes these plans by hand and
today has to eyeball the console against the plan to know what remains.
Deduped against `docs/ideas/backlog.md` + queue-state NEXT: the existing
"/owner/environments drift check" bullet covers documented-vs-live on the
estate page, not manifest-vs-live per project group. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 1 (#202) laid exactly the seams this slice needed — registry loader
with the no-values guarantee, manage-link ladder, auth seam comments — all
reused verbatim with zero rework; it missed nothing this slice had to
repair.
