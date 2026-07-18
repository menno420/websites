# 2026-07-18 — Dashboard consolidation redirects: /games + /reviews → re-homed content

> **Status:** `in-progress` — branch `claude/dashboard-consolidation-redirects`;
> flips to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** opus-4.8 · medium · feature build

**What this session is about:** a duplicate-sites consolidation gap slice. The
OLD dashboard (`superbot-dashboard.up.railway.app`, legacy `menno420/superbot`)
carries `/games` and `/reviews` routes; the NEW dashboard (`dashboard/`, this
repo) **404s** on both — their CONTENT was deliberately RE-HOMED (games → the
botsite service's `/games`, reviews → the review service's `/reviews`). We are
NOT re-adding the content (that re-homing is doctrine); we add **redirects** so
an inbound link to dashboard `/games` or `/reviews` lands on the re-homed
surface instead of a 404. This matters at cutover, when OLD is retired and its
URL is repointed to NEW. Rung: coordinator-dispatched consolidation-track slice.

## What was done

- <filled at flip>
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — <N passed>; `python3 bootstrap.py check --strict` — <verdict>.

⚑ Self-initiated: no — coordinator-dispatched (duplicate-sites consolidation track).

## 💡 Session idea

<filled at flip>

## ⟲ Previous-session review

<filled at flip>
