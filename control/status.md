# websites · status

updated: 2026-07-21T18:45:52Z
phase: FAILSAFE WAKE — heartbeat truing only. Correcting the prior heartbeat's `updated:` timestamp (it read 2026-07-21T19:40:00Z, which was already in the future relative to when it was committed at 08:49Z the same morning — a date-computation slip, not a real event; flagging rather than silently carrying it forward). Substance otherwise unchanged: cycle 2026-07-20 product-frontier COMPLETE — all six slices S1–S6 landed + live (#463/#464/#466/#467/#469/#470), plus PR #452's kit v1.20.1 upgrade merged since (b2f5013) and #471 trued main tip to 97c44a9. Main has been quiet ~10h since 08:49Z. No new inbox orders (still 039, done). Per this repo's own NEXT-2-TASKS "HONESTY GUARD: do not invent backlog" — the queue is genuinely dry, so no new work was started this wake; today is also the EAP's flagged 2026-07-21 read-only date, which may explain reduced activity independent of any fault.
health: green — unchanged from the prior heartbeat (2176 tests, strict check clean); not independently re-run this wake since no code changed.
last-shipped: #471 — control: heartbeat truing after S5+S6 cycle slices landed live, merged 2026-07-21T08:49:00Z; main tip 97c44a9 (kit v1.20.1 live since #452/b2f5013).
blockers: none
orders: acked=001-039 done=001-039 (021 closed w/ evidence #444; 036-039 done; 039 = the PR #452 kit-upgrade gate fix, landed via b2f5013)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` — this wake fired on it; six prior wakes today tracked PR #452 through fix→CI-never-fired→owner close/reopen→merged, then five more wakes of the current ~10h quiet spell with no crash signature (0 stuck PRs, no red CI). send_later pacemaker: not re-armed by this failsafe session.
landing: pushed-unmerged claude/heartbeat-truing-20260721 — this heartbeat-truing commit only. 1 open PR fleet-wide (#465, routine bake refresh, owner-authored) at write; 0 open claude/* PRs.
deployed: main 97c44a9 · kit v1.20.1 live (PR #452 merged, b2f5013) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); not re-verified live this wake, treat as last-known-good per the prior heartbeat's S6 verification. botsite /submit is DURABLE — DATABASE_URL live; S5 GET /submit/status/{ref} live. The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006/0017).
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
Cycle drained — the groomed 2026-07-20 product-frontier cycle (S1–S6) is fully landed and live as of 2026-07-21. No seat-buildable ungated slices remain queued from that plan. HONESTY GUARD: do not invent backlog. Next groomed queue: docs/NEXT-TASKS.md. Standing routed-out follow-ons unchanged — the S1 review-bake cron wiring (auto-draft+land editions on the BAKE_PAT path) stays a HUB-VENUE follow-on (.github/workflows/**); owner-gated items are the ⚑ rows below.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set the four Discord-login vars (+ redirect URI) on the botsite Railway service (SITE_PASSWORD now optional fallback); this also unlocks the /submit owner moderation queue (GET /submit/queue.json) + /testing owner reads now that intake persists. Its console chip now auto-flips: /owner/login 302 (Discord) or /testing/owner 401 (SITE_PASSWORD) → done-detected.
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.
- ASK-0017 — set the same four Discord-login values + one redirect URI on the dashboard service (unlocks the dashboard admin surface's owner-gated dry-run actions). Its console chip now auto-flips: /admin/login 302 → done-detected.

kit: v1.20.1
