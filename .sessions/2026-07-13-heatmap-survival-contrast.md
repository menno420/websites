# 2026-07-13 — botsite: heatmap survival contrast — lethality shading + finisher counts in the drop-off strip

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion slice

**What this session is about:** backlog promotion ("Heatmap survival
contrast — fold finishers' guide chats into the strip", captured
2026-07-13 from the heatmap-tail session 💡). The drop-off heatmap
aggregates ONLY abandoned claims — `guided_step_dropoff()` scopes to
status='claimed' with no submission row — so a step where many finishers
chatted heavily but pushed through renders identically to a wall.
Finished claims' guide exchanges are already persisted (PR #292 stores
them regardless of outcome); this session joins a per-step survivor
signal ("N finishers also asked here") into the same heatmap cells and
re-scales the shading by died-share among ALL touchers, so the strip
ranks steps by lethality ("hard but passable" vs "wall").

## What was done

(in progress — filled at close-out)
