# 2026-07-13 — botsite /should-i-build-it: venture-eval rubric scorer page

> **Status:** complete — branch `claude/rubric-scorer`, PR #262 opened READY
> (not draft) against main right after this flip was pushed; merge is the
> auto-merge lane / owner's call — this worker opens, never merges.

- **📊 Model:** Fable 5 · worker · self-initiated build slice

**What this session was about:** self-initiated rung — ORDER 022 item 4 (the
generative mandate: "treat venture's WEBSITE-IDEA markers as priority
intake"), venture WEBSITE-IDEA batch-2 marker "'Should I build it?' rubric
scorer" (venture-lab `control/outbox.md`, 2026-07-13 morning tally). The
fleet's real vetting rubric — venture-eval-001, distribution-first, weighted
0–5 — scores every candidate in venture-lab's intake packets, but existed
nowhere as an interactive surface. This session ships a GET-only botsite
page `/should-i-build-it`: the rubric's actual five axes and anchors as a
form, verdict computed entirely client-side with the rubric's own bands,
zero server state.

## What was done

- `botsite/data/rubric.json` — venture-eval-001 curated verbatim-faithfully
  from venture-lab `docs/research/venture-eval-001.md` (axes + weights:
  Distribution 35 / Agent-buildability 20 / Owner-click cost 15 / Speed to
  first dollar 15 / WTP-moat 15) and
  `candidates/kill-rule-intake-kit/pack/SCORING-RUBRIC.md` (0–5 anchors,
  verdict bands below ~3.0 / 3.0–3.5 / above 3.5, anti-gaming rules, the
  worked 3.55 example) @ `0679327a463c063dcd9fc62b33ffb9a3789fa7d3`,
  retrieved 2026-07-13; provenance block in-file. Nothing invented.
- `botsite/rubric.py` — validating loader mirroring `stripe_gotchas.py`
  (required fields, degrade-to-empty, invalid entries skipped) plus
  `scorer_config()` serializing the client config from the SAME loaded
  rubric (single-sourced weights/thresholds, `<` escaped against script
  breakout).
- `GET /should-i-build-it` route + NAV entry ("Rubric Scorer") in
  `botsite/app.py`; `botsite/templates/should_i_build_it.html`
  (`sb-page-hero` + lede naming the source file and stating plainly this is
  the fleet's real vetting rubric, not a toy; per-axis slider on the real
  0–5 half-step scale; honest empty state; cross-links to /products/catalog,
  /products, /graveyard); `botsite/static/rubric_scorer.js` — vanilla JS,
  weighted total with the arithmetic shown (anti-gaming rule 4), the two
  lowest scores called out (rule 3), verdict in the rubric's own band
  wording + comparative-not-absolute caveat, textContent-only rendering.
- `botsite/tests/test_rubric.py` — 15 tests: render + all five axes/weights,
  clarity lede + source citation, verdict thresholds/categories in the
  served page AND the JS config, JS served + single-sourced, catalog
  cross-link, no POST handler for the path (405 + route introspection),
  provenance, nav, degradation (missing/corrupt), loader validation,
  committed-data fidelity (weights sum 1.00, bands verbatim), script-breakout
  escaping. The page also rides the existing `test_clarity_structure.py`
  route walk automatically.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1172 passed (was 1157; +15 new rubric tests);
  `python3 bootstrap.py check --strict` — green after this card's designed
  born-red hold was released at the flip.
- Evidence: PR #262; rubric source venture-lab
  `docs/research/venture-eval-001.md` @ c22922d9 +
  `candidates/kill-rule-intake-kit/pack/SCORING-RUBRIC.md` @ f974455
  (repo HEAD 0679327 at retrieval).
- Decisions made: axis names follow venture-eval-001 (what the intakes cite);
  where the shipped kit edition names an axis differently (Buildability,
  Launch-effort cost) the page says so inline. Slider step 0.5 because the
  lane's real intakes score in half points (e.g. 2.5, 3.5). Band boundaries:
  exact 3.0 and 3.5 read as the middle band, matching "below ~3.0" /
  "3.0–3.5" / "above 3.5".
- Next session should know: pick up from PR #262 (auto-merge armed on open);
  the rescue branch `rescue/2026-07-13-pre-rubric-scorer` holds a pre-session
  dirty `.substrate/state.json` + an auto-drafted `2026-07-13-session-3.md`
  stub — dispose or ignore deliberately.

⚑ Self-initiated: yes — ORDER 022 item 4 generative mandate (venture
WEBSITE-IDEA batch-2 "'Should I build it?' rubric scorer"); contained (one
new GET-only page + static JS inside botsite, no existing behavior changed,
no POST/state) and reversible (delete the page to revert).

## 💡 Session idea

**Score-a-candidate permalinks** — the sliders already write their values as
GET query params (`?distribution=3&…`); a tiny enhancement (JS reads the
params on load and pre-sets the sliders) makes every scored candidate a
shareable, zero-state URL — the owner could paste a scored idea into an
inbox order or a venture intake as one link. Worth having because the rubric
is comparative by design: comparing two ideas is exactly two tabs. Still
zero server state; degrade is automatic (no params = defaults).

## ⟲ Previous-session review

The swtk-gotchas session (PR draft on `claude/swtk-gotchas`) set the exact
pattern this session reused wholesale — committed-JSON provenance block,
validating loader, honest empty state, born-red card discipline — which cut
this build to a single pass; what it missed is that its "shared provenance
schema" idea (its own 💡) is now needed by a third loader (`rubric.py`
re-implements provenance validation again), strengthening the case to
actually land `botsite/provenance.py` next.
