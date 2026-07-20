# Claim — directory-probe-follow-redirects

- `claude/directory-probe-follow-redirects` · **scope** — add `follow_redirects=True` to the `/directory` `.gba` download probe so a 302→CDN counts as reachable (scoped per-request to the web_presence probe; askverify's no-follow 302 signal untouched) · `app/github.py` + `app/web_presence.py` + `app/data/web_presence.json` + `tests/` · 2026-07-20
