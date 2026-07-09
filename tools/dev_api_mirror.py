#!/usr/bin/env python3
"""Dev-only GitHub API mirror for egress-restricted local verification.

Provenance / reliability header (kit Q-0105 convention):
  - Added 2026-07-09 (control-plane-site session). WHY: agent containers route
    HTTPS through a policy proxy that blocks api.github.com directly (the
    sanctioned agent path is the GitHub MCP server), so the app cannot be
    curl-verified against the real API base from inside a session. This stub
    serves REAL responses fetched moments earlier via MCP from a directory,
    letting the production code path (app/github.py) be exercised end-to-end
    locally. raw.githubusercontent.com IS reachable, so file bodies stay live.
  - Unverified beyond its authoring session; it is a disposable convenience.
    DELETE THIS if it proves unreliable or unused over multiple sessions.
  - Never used in production; never committed with data (data dir lives in the
    session scratchpad).

Usage:
    python3 tools/dev_api_mirror.py <data_dir> [port]

Lookup for GET <path>?<query>:
  1. <data_dir><path>.q.<k1=v1&...>.json   (exact, sorted query)
  2. <data_dir><path>.json                 (query-insensitive)
  3. <data_dir><path>.403                  -> 403 with the file's JSON body
  4. otherwise 404 {"message": "Not Found"}
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

DATA_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "mirror-data").resolve()
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        rel = parsed.path.lstrip("/")
        query = "&".join(f"{k}={v}" for k, v in sorted(parse_qsl(parsed.query)))
        candidates = []
        if query:
            candidates.append(DATA_DIR / f"{rel}.q.{query}.json")
        candidates += [DATA_DIR / f"{rel}.json", DATA_DIR / f"{rel}.403"]
        for cand in candidates:
            try:
                cand.resolve().relative_to(DATA_DIR)
            except ValueError:
                continue  # path escape -> skip
            if cand.is_file():
                body = cand.read_bytes()
                status = 403 if cand.suffix == ".403" else 200
                self._send(status, body)
                return
        self._send(404, json.dumps({"message": "Not Found"}).encode())

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # quieter: one line per request
        sys.stderr.write("mirror: %s\n" % (fmt % args))


if __name__ == "__main__":
    print(f"dev_api_mirror serving {DATA_DIR} on 127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
