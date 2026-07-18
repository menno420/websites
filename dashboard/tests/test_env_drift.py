"""Env config-drift classifier (B6).

The dashboard's env map is static analysis of the bot source — variable NAMES
and code locations, never a value. Railway's live set-var list is deliberately
never committed, so the LITERAL referenced-but-unset / set-but-unused signal is
out of honest reach. What IS computable from the feed's own fields (``required``
+ per-usage ``has_default``) is drift between a var's declared requiredness and
how the code actually reads it. These tests pin that honest classifier: the two
drift buckets fire on the right shapes, and consistent vars stay clean.
"""

from __future__ import annotations

from dashboard import data_source as ds


def _var(name="X", required=False, defaults=()):
    """A minimal env_usage var: one usage per bool in ``defaults``."""
    return {
        "name": name,
        "required": required,
        "usages": [{"file": "f.py", "line": i, "has_default": d} for i, d in enumerate(defaults)],
    }


# --- classify_env_var: the two honest drift buckets + clean ---------------
def test_optional_but_undefended_is_flagged():
    """Referenced-but-unset RISK analog: declared optional, but a read has no
    default — if unset that read gets no fallback."""
    v = _var("OPTIONAL_NO_DEFAULT", required=False, defaults=(False,))
    assert ds.classify_env_var(v) == ds.ENV_DRIFT_OPTIONAL_UNDEFENDED


def test_required_but_defaulted_is_flagged():
    """Set-but-effectively-optional analog: declared required, yet every read
    supplies a default — the requiredness is misleading."""
    v = _var("REQUIRED_ALL_DEFAULTED", required=True, defaults=(True, True))
    assert ds.classify_env_var(v) == ds.ENV_DRIFT_REQUIRED_DEFAULTED


def test_required_with_hard_read_is_clean():
    """Required + at least one no-default read is CORRECT — not drift."""
    v = _var("DATABASE_URL", required=True, defaults=(False,))
    assert ds.classify_env_var(v) == ""


def test_optional_all_defaulted_is_clean():
    """Optional + every read defaulted is CORRECT (properly defended)."""
    v = _var("CACHE_TTL", required=False, defaults=(True, True))
    assert ds.classify_env_var(v) == ""


def test_required_mixed_defaults_is_clean():
    """A required var with even one hard read is defensible — not over-declared."""
    v = _var("MIXED", required=True, defaults=(True, False))
    assert ds.classify_env_var(v) == ""


# --- degrade gracefully, never raise --------------------------------------
def test_no_usages_degrades_clean():
    assert ds.classify_env_var({"name": "X", "required": True, "usages": []}) == ""


def test_missing_fields_degrade_clean():
    assert ds.classify_env_var({"name": "X"}) == ""


# --- env_drift summary over the feed --------------------------------------
def test_env_drift_summary_counts_and_flags():
    data = {
        "env_usage": [
            _var("DATABASE_URL", required=True, defaults=(False,)),         # clean
            _var("OPTIONAL_NO_DEFAULT", required=False, defaults=(False,)),  # undefended
            _var("REQUIRED_ALL_DEFAULTED", required=True, defaults=(True,)), # required-defaulted
        ]
    }
    summary = ds.env_drift(data)
    assert summary["any"] is True
    assert summary["counts"][ds.ENV_DRIFT_OPTIONAL_UNDEFENDED] == 1
    assert summary["counts"][ds.ENV_DRIFT_REQUIRED_DEFAULTED] == 1
    flagged_names = {v["name"] for v in summary["flagged"]}
    assert flagged_names == {"OPTIONAL_NO_DEFAULT", "REQUIRED_ALL_DEFAULTED"}
    # The clean var is never in the flagged list, and each flagged var carries its bucket.
    assert "DATABASE_URL" not in flagged_names
    assert all(v.get("drift") for v in summary["flagged"])


def test_env_drift_clean_feed_reports_no_drift():
    data = {"env_usage": [_var("DATABASE_URL", required=True, defaults=(False,))]}
    summary = ds.env_drift(data)
    assert summary["any"] is False
    assert summary["flagged"] == []


def test_env_drift_empty_feed_is_clean():
    assert ds.env_drift({})["any"] is False
