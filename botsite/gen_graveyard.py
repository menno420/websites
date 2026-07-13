"""Strategy-graveyard bake for botsite — trading-strategy ledger to JSON.

The /graveyard page is the honest leaderboard of the trading-strategy lab's
experiment ledger (ORDER 022 item 4, venture WEBSITE-IDEA batch-2 intake):
every recorded run, what beat its benchmark and what didn't, and the plain
program truth — **zero strategies promoted**. Cross-repo data arrives only
as committed JSON (the review-service bake pattern, ``review/gen_fleet.py``):
this script is the bake half — run it from the repo root and it fetches
``experiments/index.jsonl`` from menno420/trading-strategy over
raw.githubusercontent.com, reduces the ~256KB ledger to a compact aggregate,
and writes the committed ``botsite/data/graveyard.json`` the page reads from
disk at request time. **No network ever happens in the request path.**

The ledger's real schema (verified 2026-07-13): one JSON object per recorded
run with ``run_id``, ``file``, ``strategy``, ``instrument``, ``timeframe``,
``params``, ``sharpe`` (stitched OOS), ``benchmark_sharpe`` (same-window
same-cost buy & hold), ``cagr``, ``max_drawdown``, ``data_start``,
``data_end``, ``variants_tried``, and (on a few rows) ``holdout_unlocked``.
There is **no verdict field in the ledger**, so verdicts here are DERIVED at
bake time with the lab's own documented dev rule (trading-strategy
``docs/research-round-3-results.md``: "stitched OOS vs same-window same-cost
buy & hold, Round-2 KEEP/KILL rule"):

- ``keep``  — the run's OOS Sharpe beats its buy-and-hold benchmark
  (dev-candidate ONLY; the lab is explicit that a KEEP is not a finding);
- ``kill``  — it doesn't;
- ``promoted`` — **always 0**: the lab's holdout is SPENT and promotion is
  CLOSED (same doc), and no ledger record carries a promotion. The zero is
  the page's point, so the bake records it explicitly rather than leaving
  it implied.

Honesty rules: malformed ledger lines are skipped and counted, never fatal;
``source_sha`` comes over anonymous git transport (``git ls-remote`` — the
gen_fleet idiom; the REST API is walled from session containers) and
degrades to ``null`` with its reason; if the fetch fails and a previously
committed graveyard.json exists, the old file is left untouched (fail-soft,
its ``as_of`` ages honestly) and the script exits 0.

    python3 botsite/gen_graveyard.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OWNER = "menno420"
SOURCE_REPO = "trading-strategy"
SOURCE_PATH = "experiments/index.jsonl"
SOURCE_RAW = (
    f"https://raw.githubusercontent.com/{OWNER}/{SOURCE_REPO}/main/{SOURCE_PATH}"
)
SOURCE_URL = f"https://github.com/{OWNER}/{SOURCE_REPO}/blob/main/{SOURCE_PATH}"

OUT_PATH = Path(__file__).resolve().parent / "data" / "graveyard.json"
TIMEOUT = 20

# Top-N cap per verdict — the committed JSON stays a compact summary
# (well under 50KB), never a copy of the raw 256KB ledger.
TOP_N = 20

# Every numeric field a record must carry to be aggregated.
_NUMERIC_REQUIRED = ("sharpe", "benchmark_sharpe", "cagr", "max_drawdown")
_STR_REQUIRED = ("run_id", "strategy", "instrument", "timeframe")


def _fetch(url: str) -> tuple[str | None, str]:
    """(body, "") on success; (None, reason) on any failure — never raises."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace"), ""
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — fail-soft bake, reason recorded
        return None, f"{type(exc).__name__}: {exc}"


def source_sha_probe() -> tuple[str | None, str]:
    """HEAD sha of the source repo over anonymous git transport.

    ``git ls-remote`` needs no token and works where the REST API is walled
    (session proxies) — the ``review/gen_fleet.py`` head_probe idiom.
    Returns ``(sha, "")`` or ``(None, reason)``; a sha is never invented.
    """
    url = f"https://github.com/{OWNER}/{SOURCE_REPO}"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        out = subprocess.run(
            ["git", "ls-remote", url, "HEAD"],
            capture_output=True, text=True, timeout=TIMEOUT * 2, env=env,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if out.returncode != 0:
        tail = (out.stderr or "").strip().splitlines()
        return None, tail[-1] if tail else "ls-remote failed"
    first = out.stdout.strip().splitlines()
    sha = first[0].split("\t")[0].strip() if first else ""
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        return None, "no HEAD advertised"
    return sha, ""


def _valid(rec: Any) -> bool:
    if not isinstance(rec, dict):
        return False
    for field in _STR_REQUIRED:
        value = rec.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    for field in _NUMERIC_REQUIRED:
        value = rec.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
    vt = rec.get("variants_tried")
    if not isinstance(vt, int) or isinstance(vt, bool) or vt < 0:
        return False
    return True


def parse_records(text: str) -> tuple[list[dict[str, Any]], int]:
    """JSONL → (valid records, skipped-line count). Malformed lines and
    records missing required fields are skipped and counted, never fatal."""
    records: list[dict[str, Any]] = []
    skipped = 0
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if _valid(rec):
            records.append(rec)
        else:
            skipped += 1
    return records, skipped


def derive_verdict(rec: dict[str, Any]) -> str:
    """The lab's dev rule, applied to the ledger's own fields: KEEP
    (dev-candidate only) when the run's stitched-OOS Sharpe beats its
    same-window buy-and-hold benchmark; KILL otherwise. PROMOTED is never
    derivable from the ledger — promotion is closed (holdout spent)."""
    return "keep" if rec["sharpe"] > rec["benchmark_sharpe"] else "kill"


def _round(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def _entry(rec: dict[str, Any]) -> dict[str, Any]:
    """One compact leaderboard row from one ledger record."""
    return {
        "strategy": rec["strategy"],
        "instrument": rec["instrument"],
        "timeframe": rec["timeframe"],
        "sharpe": _round(rec["sharpe"]),
        "benchmark_sharpe": _round(rec["benchmark_sharpe"]),
        "cagr": _round(rec["cagr"]),
        "max_drawdown": _round(rec["max_drawdown"]),
        "variants_tried": rec["variants_tried"],
    }


def compute_graveyard(
    records: list[dict[str, Any]],
    *,
    as_of: str,
    source_sha: str | None,
    source_sha_reason: str = "",
    skipped: int = 0,
) -> dict[str, Any]:
    """Pure transform: ledger records → the committed graveyard summary.

    Network-free by design so tests can feed it fixture records directly.
    """
    by_verdict: dict[str, list[dict[str, Any]]] = {"keep": [], "kill": []}
    for rec in records:
        by_verdict[derive_verdict(rec)].append(rec)

    sharpes = [r["sharpe"] for r in records]
    strategies = sorted({r["strategy"] for r in records})
    instruments = sorted({r["instrument"] for r in records})
    timeframes = sorted({r["timeframe"] for r in records})

    aggregate: dict[str, Any] = {
        "runs": len(records),
        "config_evals": sum(r["variants_tried"] for r in records),
        "skipped_ledger_lines": skipped,
        "verdicts": {
            # 0 by the program's own record: promotion is CLOSED (holdout
            # spent) and no ledger row carries a promotion. The zero is the
            # page's point — recorded explicitly, never implied.
            "promoted": 0,
            "keep": len(by_verdict["keep"]),
            "kill": len(by_verdict["kill"]),
        },
        "strategies": len(strategies),
        "instruments": len(instruments),
        "timeframes": timeframes,
        "best_sharpe": _round(max(sharpes)) if sharpes else None,
        "median_sharpe": _round(statistics.median(sharpes)) if sharpes else None,
        "worst_sharpe": _round(min(sharpes)) if sharpes else None,
        "holdout_unlocked_runs": sum(
            1 for r in records if r.get("holdout_unlocked") is True
        ),
        "data_start": min((str(r.get("data_start") or "") for r in records), default=""),
        "data_end": max((str(r.get("data_end") or "") for r in records), default=""),
    }

    top = {
        verdict: [
            _entry(r)
            for r in sorted(rows, key=lambda r: r["sharpe"], reverse=True)[:TOP_N]
        ]
        for verdict, rows in by_verdict.items()
    }

    strategy_rows: list[dict[str, Any]] = []
    for name in strategies:
        rows = [r for r in records if r["strategy"] == name]
        keeps = [r for r in rows if derive_verdict(r) == "keep"]
        strategy_rows.append({
            "strategy": name,
            "runs": len(rows),
            "config_evals": sum(r["variants_tried"] for r in rows),
            "keep": len(keeps),
            "kill": len(rows) - len(keeps),
            "best_sharpe": _round(max(r["sharpe"] for r in rows)),
            "best_cagr": _round(max(r["cagr"] for r in rows)),
            "worst_max_drawdown": _round(min(r["max_drawdown"] for r in rows)),
        })
    # Best strategy first — most KEEPs, then best sharpe (the leaderboard order).
    strategy_rows.sort(key=lambda s: (-s["keep"], -s["best_sharpe"]))

    return {
        "as_of": as_of,
        "source": SOURCE_URL,
        "source_sha": source_sha,
        "source_sha_reason": source_sha_reason,
        "verdict_rule": (
            "derived at bake time from the ledger's own fields — KEEP "
            "(dev-candidate only) when a run's stitched-OOS Sharpe beats its "
            "same-window buy-and-hold benchmark, KILL otherwise; PROMOTED "
            "requires the lab's closed validation protocol (holdout spent) "
            "and is 0 by the program's own record"
        ),
        "aggregate": aggregate,
        "top": top,
        "strategies": strategy_rows,
    }


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body, err = _fetch(SOURCE_RAW)
    if body is None or not body.strip():
        reason = err or "empty file"
        if OUT_PATH.exists():
            print(
                f"ledger unavailable ({reason}) — keeping the previously "
                f"committed {OUT_PATH.name} untouched (fail-soft)."
            )
            return 0
        print(f"ledger unavailable ({reason}) and no committed {OUT_PATH.name} exists — nothing written.")
        return 1

    records, skipped = parse_records(body)
    if not records:
        if OUT_PATH.exists():
            print(
                f"ledger parsed to zero valid records ({skipped} skipped) — "
                f"keeping the previously committed {OUT_PATH.name} untouched (fail-soft)."
            )
            return 0
        print(f"ledger parsed to zero valid records ({skipped} skipped) — nothing written.")
        return 1

    sha, sha_reason = source_sha_probe()
    out = compute_graveyard(
        records, as_of=now, source_sha=sha, source_sha_reason=sha_reason,
        skipped=skipped,
    )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    agg = out["aggregate"]
    print(
        f"wrote {OUT_PATH.name}: {agg['runs']} runs / "
        f"{agg['config_evals']} config evals ({skipped} lines skipped), "
        f"verdicts promoted={agg['verdicts']['promoted']} "
        f"keep={agg['verdicts']['keep']} kill={agg['verdicts']['kill']}, "
        f"{agg['strategies']} strategies, source_sha={sha or f'null ({sha_reason})'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
