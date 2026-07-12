"""Offline unit tests for app/listfilter.py — the centralized server-rendered
list filter/sort/search core (ORDER 019): state parsing (key whitelisting,
length/count caps), unknown-value honesty (kept + flagged, never silently
dropped — the /ideas ?state= precedent), multi-select combination (AND across
dimensions, OR within one), search, every sort, reachable option counts,
empty results, and the URL toggle/clear helpers (always urlencoded, always
relative, other params preserved).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import listfilter as lf  # noqa: E402
from app.listfilter import Dimension, ListSpec, ListState, SortOption  # noqa: E402

ITEMS = [
    {"repo": "alpha", "kinds": ["ask"], "name": "Mint the PAT", "age": 3},
    {"repo": "beta", "kinds": ["note"], "name": "decide window", "age": 30},
    {"repo": "beta", "kinds": ["ask", "money"], "name": "pay the bill", "age": 200},
]

SPEC = ListSpec(
    path="/list",
    dimensions=(
        Dimension("repo", "repo", get=lambda it: [it["repo"]]),
        Dimension("kind", "kind", derived=True,
                  values=("ask", "note", "money", "other"),
                  get=lambda it: it["kinds"]),
    ),
    sorts=(
        SortOption("default", "default"),  # sort_key=None keeps input order
        SortOption("oldest", "oldest", sort_key=lambda it: it["age"],
                   reverse=True),
        SortOption("az", "A-Z", sort_key=lambda it: it["name"].casefold()),
    ),
    search=lambda it: it["name"],
)


# --------------------------------------------------------------------------- #
# parse — whitelisting + caps
# --------------------------------------------------------------------------- #


def test_parse_whitelists_keys_and_sort_and_keeps_extras():
    state = lf.parse(SPEC, {
        "repo": ["alpha", "beta", "alpha"],   # dupes collapse
        "bogus_key": "x",                     # not owned, not a dimension
        "sort": "not-a-sort",                 # unknown -> default
        "q": "  hi  ",
        "refresh": "1",
    })
    assert state.selected == {"repo": ["alpha", "beta"]}
    assert state.sort == "default"
    assert state.q == "hi"
    assert ("refresh", "1") in state.extra
    assert ("bogus_key", "x") in state.extra  # preserved as opaque extra
    assert not any(k == "repo" for k, _ in state.extra)


def test_parse_caps_lengths_and_counts():
    state = lf.parse(SPEC, {
        "repo": [f"v{i}" for i in range(50)] + ["x" * 500],
        "q": "y" * 500,
        "sort": "z" * 500,
    })
    assert len(state.selected["repo"]) == lf.MAX_VALUES_PER_DIM
    assert all(len(v) <= lf.MAX_VALUE_LEN for v in state.selected["repo"])
    assert len(state.q) == lf.MAX_QUERY_LEN
    assert state.sort == "default"  # oversized garbage never becomes a sort


def test_parse_without_search_ignores_q():
    spec = ListSpec(path="/x", dimensions=SPEC.dimensions, sorts=SPEC.sorts,
                    search=None)
    state = lf.parse(spec, {"q": "hello"})
    assert state.q == ""


# --------------------------------------------------------------------------- #
# apply — combination semantics, search, counts, honesty
# --------------------------------------------------------------------------- #


def test_apply_no_state_is_identity():
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {}))
    assert out["items"] == ITEMS  # same order, nothing dropped
    assert out["active"] is False
    assert (out["shown"], out["total"]) == (3, 3)


def test_apply_or_within_dim_and_and_across_dims():
    # OR within: both repos selected -> everything
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"repo": ["alpha", "beta"]}))
    assert out["shown"] == 3
    # AND across: repo=beta AND kind=ask -> only the pay item
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"repo": "beta", "kind": "ask"}))
    assert [it["name"] for it in out["items"]] == ["pay the bill"]
    assert out["active"] is True


def test_apply_search_is_case_insensitive_substring():
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"q": "MINT"}))
    assert [it["name"] for it in out["items"]] == ["Mint the PAT"]
    # search combines (AND) with filters
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"q": "MINT", "repo": "beta"}))
    assert out["shown"] == 0 and out["active"] is True


def test_apply_counts_are_against_the_other_filters():
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"repo": "beta"}))
    kind = next(d for d in out["dims"] if d["key"] == "kind")
    counts = {o["value"]: o["count"] for o in kind["options"]}
    # kind counts respect repo=beta (the OTHER dim)…
    assert counts == {"ask": 1, "note": 1, "money": 1, "other": 0}
    # …repo counts ignore repo's own selection (still reachable to widen)
    repo = next(d for d in out["dims"] if d["key"] == "repo")
    assert {o["value"]: o["count"] for o in repo["options"]} == {
        "alpha": 1, "beta": 2}
    sel = {o["value"]: o["selected"] for o in repo["options"]}
    assert sel == {"alpha": False, "beta": True}


def test_apply_unknown_value_is_kept_and_flagged_not_dropped():
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"repo": "nope"}))
    assert out["shown"] == 0 and out["active"] is True  # honestly empty
    repo = next(d for d in out["dims"] if d["key"] == "repo")
    assert [u["value"] for u in repo["unknown"]] == ["nope"]
    # its removal URL toggles it off entirely
    assert repo["unknown"][0]["url"] == "/list"
    # and it appears among the chips like any active filter
    assert any(c["value_label"] == "nope" for c in out["chips"])


def test_apply_every_sort():
    # default: input order kept (sort_key=None never re-sorts)
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {}))
    assert [it["age"] for it in out["items"]] == [3, 30, 200]
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"sort": "oldest"}))
    assert [it["age"] for it in out["items"]] == [200, 30, 3]
    out = lf.apply(SPEC, ITEMS, lf.parse(SPEC, {"sort": "az"}))
    assert [it["name"] for it in out["items"]] == [
        "decide window", "Mint the PAT", "pay the bill"]
    # sort alone is not an "active filter" (nothing is hidden)
    assert out["active"] is False and out["shown"] == 3


def test_apply_chips_and_clear_url():
    out = lf.apply(SPEC, ITEMS, lf.parse(
        SPEC, {"repo": "beta", "kind": "ask", "q": "pay", "refresh": "1"}))
    labels = {(c["dim_label"], c["value_label"]) for c in out["chips"]}
    assert labels == {("repo", "beta"), ("kind", "ask"), ("search", "pay")}
    # chip URL removes exactly its own value, keeping the rest
    kind_chip = next(c for c in out["chips"] if c["dim_label"] == "kind")
    assert "kind=" not in kind_chip["url"]
    assert "repo=beta" in kind_chip["url"] and "q=pay" in kind_chip["url"]
    # clear-all drops filters + search but preserves the extra param
    assert out["clear_url"] == "/list?refresh=1"


# --------------------------------------------------------------------------- #
# URL helpers — toggle/clear, encoding, relative-only
# --------------------------------------------------------------------------- #


def test_toggle_url_on_off_and_encoding():
    state = lf.parse(SPEC, {"repo": "beta"})
    assert lf.toggle_url(SPEC, state, "repo", "alpha") == (
        "/list?repo=beta&repo=alpha")
    assert lf.toggle_url(SPEC, state, "repo", "beta") == "/list"
    # values are urlencoded, never emitted raw
    url = lf.toggle_url(SPEC, state, "kind", "a b&c/d")
    assert "a+b%26c%2Fd" in url and " " not in url and url.startswith("/list?")


def test_clear_dim_and_sort_urls_preserve_the_rest():
    state = lf.parse(SPEC, {"repo": "beta", "kind": "ask", "q": "x",
                            "sort": "az", "refresh": "1"})
    url = lf.clear_dim_url(SPEC, state, "repo")
    assert "repo=" not in url
    for part in ("kind=ask", "q=x", "sort=az", "refresh=1"):
        assert part in url
    # selecting the default sort emits NO sort param (canonical URLs)
    assert "sort=" not in lf.sort_url(SPEC, state, "default")
    assert "sort=oldest" in lf.sort_url(SPEC, state, "oldest")
    # drop_q removes only the search text
    assert "q=" not in lf.drop_q_url(SPEC, state)
    assert "kind=ask" in lf.drop_q_url(SPEC, state)


def test_form_fields_carry_everything_except_q():
    out = lf.apply(SPEC, ITEMS, lf.parse(
        SPEC, {"repo": "beta", "q": "x", "sort": "az", "refresh": "1"}))
    fields = out["form_fields"]
    assert ("repo", "beta") in fields and ("sort", "az") in fields
    assert ("refresh", "1") in fields
    assert not any(name == "q" for name, _ in fields)


def test_apply_handles_a_bad_item_without_raising():
    spec = ListSpec(
        path="/x",
        dimensions=(Dimension("repo", "repo", get=lambda it: [it["repo"]]),),
        sorts=(SortOption("default", "default"),),
    )
    items = [{"repo": "ok"}, {"not_repo": "boom"}]  # second raises KeyError
    out = lf.apply(spec, items, lf.parse(spec, {"repo": "ok"}))
    assert [it.get("repo") for it in out["items"]] == ["ok"]
