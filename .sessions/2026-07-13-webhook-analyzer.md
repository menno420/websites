# 2026-07-13 — botsite /webhook-analyzer: client-side webhook payload analyzer

> **Status:** `complete` — branch `claude/webhook-analyzer`, PR #266 opened
> READY (not draft) against main; merge is the auto-merge lane / owner's
> call — this worker opens, never merges.

- **📊 Model:** Claude Fable 5 · worker · build

**What this session was about:** self-initiated rung — ORDER 022 item 4
(SCAN AND INITIATE: "treat venture's WEBSITE-IDEA markers as priority
intake"), executing the LAST venture WEBSITE-IDEA batch-2 marker
"webhook-payload analyzer" (venture-lab `control/outbox.md`, 2026-07-13
morning tally line, venture-lab sha
`0679327a463c063dcd9fc62b33ffb9a3789fa7d3`). The build: a CLIENT-SIDE-ONLY
tool page on botsite — paste a webhook JSON payload into a textarea and
vanilla in-browser JS parses and classifies it (provider detection, field
classification, signature-verification guidance). Zero server involvement
with pasted data: GET-only route, no form POST, no network calls from the
analyzer JS — and the page states that privacy property prominently,
because it IS the feature.

## What was done

- `botsite/data/webhook_analyzer.json` — the analyzer knowledge base with
  a per-source provenance block. Grounding, honestly tiered: Stripe
  signature guidance + field notes sourced ONLY from the SWTK material
  already committed as `botsite/data/stripe_gotchas.json` (venture-lab @
  0679327); GitHub guidance verified against the official docs fetched
  2026-07-13 (X-Hub-Signature-256, HMAC-SHA256 hex digest, sha256= prefix,
  constant-time compare; common body properties action/sender/repository);
  Discord's interaction body fields verified from the official docs
  (id/application_id/type/token) but its signature specifics were NOT on
  the fetched page, so that guidance is a downgraded "not verified from
  source this session" pointer at the official docs — nothing invented.
- `botsite/webhook_analyzer.py` — validating loader (returns None on
  missing/corrupt file or no valid provider → honest unavailable state;
  invalid providers/sources/notes skipped, never fatal) +
  `analyzer_config()` serializing the client config from the SAME loaded
  data with a source label + verified flag resolved onto every guidance
  line, `<` escaped against script breakout (the rubric.py pattern).
- `GET /webhook-analyzer` route + NAV entry ("Webhook Analyzer") in
  `botsite/app.py`; `botsite/templates/webhook_analyzer.html`
  (`sb-page-hero` + lede stating what it does AND the privacy property;
  textarea + Analyze + Load-sample buttons with NO `<form>` at all; second
  privacy note at the textarea; single-sourced heuristics copy; provenance
  section; cross-links to /stripe-gotchas and /products);
  `botsite/static/webhook_analyzer.js` — vanilla, zero network primitives,
  textContent-only rendering; honest parse errors with position context;
  detection reported with evidence ("Looks like…" / "Possibly… (matched N
  of M markers)" / "Unrecognized — generic analysis only"); field walk
  capped 6 levels / 500 fields and says so when truncated; SYNTHETIC
  sample (evt_TESTsample… ids, customer_email null + customer_details
  .email filled) demos the gotcha note instantly.
- `botsite/tests/test_webhook_analyzer.py` — 19 tests: tool UI renders
  with no form; privacy lede + textarea-adjacent note; nav; cross-links;
  POST → 405 + route introspection; config script tag valid JSON with no
  raw `</script`; served JS contains none of the network primitives and no
  markup sink; provenance sha + grounding tiers on the page; headers-not-
  body reminder; synthetic-sample labeling; degrade on missing/corrupt
  file; loader validation (None without a valid provider, invalid entries
  skipped); committed-data grounding (Stripe lines all swtk-sourced,
  GitHub lines doc-verified with fetch date, Discord line unverified and
  header claim withheld); config source-label resolution; script-breakout
  escaping; heuristics + caps copy single-sourced onto the page.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1191 passed (was 1172; +19 new tests); `python3
  bootstrap.py check --strict` — green after this card's designed
  born-red hold was released at the flip. Playwright end-to-end (chromium
  vs local uvicorn): sample analyzes (detection + gotcha note +
  classifications render), garbage input shows an honest parse error, and
  network requests fired by analyze actions: 0.
- Evidence: PR #266; GitHub docs fetched 2026-07-13 (validating-webhook-
  deliveries + webhook-events-and-payloads); Discord docs fetch redirected
  to docs.discord.com and confirmed body fields only.
- Next session should know: the backlog bullet for this card's 💡 idea is
  NOT yet in `docs/ideas/backlog.md` — this session's diff was scoped to
  botsite/** + card + claim; add the bullet as a follow-up.

⚑ Self-initiated: yes — contained + reversible (new page, no existing
behavior touched; GET-only, zero server state — delete the page to revert).

## 💡 Session idea

**In-browser signature verifier (WebCrypto) on /webhook-analyzer** — the
page already tells visitors a pasted body alone can never be verified; a
second textarea pair (raw body bytes + Stripe-Signature or
X-Hub-Signature-256 header value + a TEST-mode secret) could compute the
HMAC locally via `crypto.subtle` and show match/mismatch — still zero
network, same privacy property. Worth having because it completes the loop
the analyzer explicitly declares out of scope, on the exact raw-bytes
doctrine the SWTK material teaches. Deduped against
`docs/ideas/backlog.md`: no webhook/signature/HMAC/analyzer bullet exists
there. Capture into the backlog is queued as a follow-up (this session's
diff was deliberately scoped; see "Next session should know").

## ⟲ Previous-session review

The rubric-scorer session (.sessions/2026-07-13-rubric-scorer.md, PR #262)
did well: its config-in-script-tag + predicate-free vanilla-JS + no-POST
test pattern transplanted here wholesale, cutting this build to one pass;
what it missed is that its own card's "shared provenance schema" review
note keeps compounding — `webhook_analyzer.py` is now the FOURTH loader
re-implementing provenance validation, and `botsite/provenance.py` still
does not exist.
