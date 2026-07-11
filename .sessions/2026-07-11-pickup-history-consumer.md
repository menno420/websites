# 2026-07-11 — Consumer-first pickup history: parse `pickup:` notes tokens (rung 3, build-and-hold)

> **Status:** `in-progress` — branch `claude/pickup-history-consumer`; flips
> to `complete` + the real PR number after the PR exists. BUILT UNDER THE
> #141 MERGE HOLD: this PR goes READY + green and WAITS UNMERGED (held-list
> position #2, after #147).

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 34 — 18:54Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 18:54Z nudge under the
build-not-merge hold; ritual clean (no new orders; #141 open but now
mergeable_state=behind — noted for the manager; stamp frozen 16:27Z), so
the designated build-and-hold slice: **the latency-persistence ask's
buildable LOCAL half**. The #135 rollup can only see CURRENTLY-standing
claims (done orders drop their claimed-by annotation, taking the latency
datum with them — live-verified on ORDER 011). The proposed one-line
convention (`pickup: <id> <mins>m` in heartbeat notes on the done= move)
fixes that at the protocol layer — and shipping the CONSUMER first means
the convention works the moment the first lane adopts it (exactly how the
tooling:/landing: tokens rolled out: parser #67, first foreign writer the
same day).

## What was done

- (work in progress — filled at close-out)
