# Provenance — source files, SHAs, and claim verdicts

> Provenance: compiled 2026-07-12 from read-only clones of menno420/superbot
> (HEAD `abb1ce115f9dc5077636f6d000bc62888da0ec07`) and menno420/fleet-manager
> (HEAD `791772fab1f9616e243221bb4022a894285f6981`). All SHAs below are
> last-touch commit SHAs for the named path.

## Source files → commit SHAs

| Repo | Path | Last-touch SHA | What it is |
|---|---|---|---|
| superbot | `docs/current-state.md` | `0999c3315eb6dd48d15c8731b549a249a693ea44` | banner: second Anthropic email SENT 2026-07-12 13:24Z |
| superbot | `docs/eap/night-review-2026-07-12.md` | `8558179e6a90670ed18c778234d789c65c2b5789` | THE scheduler-incident record (email "finding 7") |
| superbot | `docs/eap/night-review-2026-07-11.md` | `e1090dbcfdf63ffd955399dc2325b9ad1a2f8c8d` | 07-10→07-11 batch review, 13 lanes |
| superbot | `docs/eap/external-review-pack-2026-07-09.md` | `b0e9ab20601e8a44da87c6e72f712f517b62adc0` | outside-reviewer entry point (07-09 snapshot) |
| superbot | `docs/eap/anthropic-email-2-draft-2026-07-11.md` | `8558179e6a90670ed18c778234d789c65c2b5789` | canonical framing; status = SENT |
| superbot | `docs/eap/screenshots-2026-07-11/index.md` | `e3eb0eb2bf3683794dd0d8c40bbf3988832c31ea` | figs 1–19 + 15a/15b/15c/17 |
| superbot | `docs/eap/screenshots-2026-07-12/index.md` | `cbb549539c64e0ce3b4fea268e27b7ac49eeaf08` | figs 20–35 (incident batch) |
| superbot | `docs/owner/fleet-8seat-structure-2026-07-11.md` | `95fc025bb56d0901940ccd5a9b6184a2d8a813de` | the 8-seat decision doc |
| superbot | `docs/owner/websites-review-site-order-2026-07-12.md` | `0999c3315eb6dd48d15c8731b549a249a693ea44` | the order driving this site refresh |
| fleet-manager | `docs/roster.md` | `10fc4f7a95c3ca2be96eac7017dbb2fdb3e6a172` | GENERATED roster gen #13, 2026-07-12T08:13Z |
| fleet-manager | `projects/README.md` | (in HEAD tree `791772f`) | 8-seat registry, restructure slices 1–4 |
| fleet-manager | `docs/research/2026-07-12-staleness-sweep-8seat.md` | `4111da44ae218bb37442ad958d740b782b1c859a` | first 8-seat staleness sweep (PR #105) |
| fleet-manager | restructure slice 1 (PR #88) | `639b0f09d7e99056cb8be83abc733edc198f1728` (2026-07-12T03:15:10Z) | registry → 8 standing seats |

## Claim → evidence verdicts

The assistant must carry these verdicts through verbatim in spirit: a
VERIFIED claim can be asserted with its citation; an UNVERIFIED claim may
only be *attributed* ("the sent email states…"), never independently
asserted.

| Claim | Verdict | Evidence |
|---|---|---|
| 2026-07-12 scheduler-degradation incident (~02:30–08:00Z; 9 dropped one-shots, 2 wedged crons) | VERIFIED (as documented record) | superbot `docs/eap/night-review-2026-07-12.md` @ `8558179` §1; figures @ `cbb5495` |
| Dead-man failsafe crons (Q-0265) production-proven | VERIFIED (documented) | same file §3.1; fig-24 |
| Serialization-vs-real-drop distinction | VERIFIED (documented) | same file §8 (Addendum ~12:00Z); fig-35 |
| Duplicate-fire clean stand-down (zero writes) | VERIFIED (documented) | same file §8; fig-34 |
| Previous night ran 84/85 one-shots clean | UNVERIFIABLE from git — cited to a live trigger-registry export not committed as raw data; quote as "the fleet's own registry evidence" | night-review-2026-07-12 §1 @ `8558179` |
| Consolidation: ~15 Projects → 8 standing seats | PARTLY VERIFIED — the 8-seat side is hard-verified (superbot `docs/owner/fleet-8seat-structure-2026-07-11.md` @ `95fc025`; fleet-manager PR #88 `639b0f0`); the "~15" peak is screenshot-supported (fig-01) and consistent with the 07-11 night review's lane table, but **no machine count of exactly 15 exists — always say "~15", never an exact 15** | see roster chunk |
| Consolidation happened "on 07-11" | NUANCE — decided late 2026-07-11 (`95fc025`); registry restructure landed 2026-07-12T03:15Z (`639b0f0`). Say "decided 07-11, canonicalized early 07-12" | |
| The 8 seats' names/repos | VERIFIED | `95fc025` + fleet-manager `projects/README.md` @ `791772f` |
| Second Anthropic email SENT 2026-07-12 13:24Z | VERIFIED (documented) | superbot `docs/current-state.md` banner @ `0999c33` |
| Review site live 2026-07-12 11:34Z at review-production-fc91.up.railway.app | VERIFIED (documented) | email draft @ `8558179` |
| gen-2 relaunch "116 PRs across 13 repos in ~6 hours, zero stuck" | UNVERIFIED here — email-draft claim; attribute to the email/fleet reviews or soften | `8558179` |
| superbot-next 37/49 subsystems, 218/218 goldens | UNVERIFIED here — email-draft claim; attribute, don't assert | `8558179` |
| substrate-kit v1.7 → v1.12.1 in ~3 days | UNVERIFIED here (email-draft claim); roster gen #13 shows lanes on v1.12.x and fm #114 upgraded to v1.13.0 — version numbers at least consistent | `8558179`, `10fc4f7` |
| Trading lane's honest null result ("no strategy cleared significance") | VERIFIED (documented) — keep; the honesty is deliberate | email draft (e) @ `8558179` |
| One Game Lab lane private by design (Nintendo-derived; unnamed here — ORDER 017 D) | VERIFIED (documented) — do not surface its name or internals | email draft (e); roster gen #13 (NOT MEASURED, auth wall) |

## ANTHROPIC_API_KEY (references only — no secret values anywhere)

- superbot `docs/owner/websites-review-site-order-2026-07-12.md` @ `0999c33`:
  the AI-assistant workstream's single owner-provided secret; if absent from
  the service env, report it as a blocker rather than faking the feature.
- fleet-manager `environments/env-grant-policy.md`: policy-classified as a
  budget-capped, owner-issued key for lanes that genuinely call models.
- Whether the key is set on the Railway review service is only knowable at
  runtime in the service env — never from these repos.
