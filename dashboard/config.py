"""Configuration for the developer dashboard service.

Everything runtime-tunable comes from env vars (documented in docs/dashboard.md):
  SITE_PASSWORD   shared secret for the HTTP Basic auth gate (REQUIRED; the whole
                  surface is internal oversight data). Fail-closed: the app 503s
                  every route if this is unset — an unset password never opens the door.
  PORT            bind port (Railway injects this; default 8080).

Feed URLs / cache TTL live in data_source.py (DASHBOARD_JSON_URL, CONSOLE_JSON_URL,
DATA_CACHE_TTL_SECONDS) — all default to superbot@main over raw.githubusercontent.com.

This service holds NO bot control credential. It deliberately does not read any bot
control-API token or Discord OAuth secret var — the live-write control panel is a stub
(see app.py / docs/dashboard.md). A test guards that those literal names never appear
anywhere in this service's source.
"""

import os

SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
