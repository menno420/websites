"""listfilter — the centralized, server-rendered list filter/sort/search core.

ORDER 019: the owner queue was one long unfilterable list, and the owner asked
for multi-dimensional filters "implemented as a centralized feature". This
module is that feature's core. Each list surface declares a ``ListSpec``
(dimensions + sorts + a searchable-text getter), and the route does::

    state = listfilter.parse(SPEC, request.query_params)
    view  = listfilter.apply(SPEC, items, state)

``view`` is a plain dict the shared Jinja partial (``_listfilter.html``)
renders: filter pills with reachable-result counts, sort links, a zero-JS GET
search form, active-filter chips with remove links, a clear-all link, and an
"N of M" count. First consumers: /queue and /orders.

Design contract:

- **stdlib-only, service-free** — imports nothing from this service (no
  routes, no templates, no config, no client layer), so it can be VENDORED
  byte-identically into the sibling services later (the repo's established
  sharing pattern: ``static/ds/``, ``static/app.js``, ``_icons.html`` are all
  shared as verbatim copies; cross-service imports are forbidden).
- **zero-JS, GET-only** — every interaction is a link or a GET form; the whole
  state lives in the query string. Progressive enhancement may decorate this,
  but the no-JS path IS the feature.
- **untrusted input** — ``parse`` whitelists param KEYS against the spec,
  whitelists the sort value, caps every value length and count, and builds
  URLs exclusively through ``urllib.parse.urlencode`` (templates rely on
  Jinja autoescape for text; nothing here emits markup).
- **honest filtering** — an unknown filter VALUE stays active and is flagged
  (the /ideas ``?state=`` precedent): it visibly matches nothing instead of
  being silently dropped. Option counts are computed against the OTHER active
  filters (+ search), so every pill shows the result count actually reachable
  by clicking it. Combination semantics: OR within a dimension, AND across
  dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.parse import urlencode

# Query-param names owned by every spec (in addition to its dimension keys).
Q_PARAM = "q"
SORT_PARAM = "sort"

# Input caps — query strings are untrusted; nothing here should let a crafted
# URL balloon the work or the page.
MAX_VALUE_LEN = 80
MAX_VALUES_PER_DIM = 20
MAX_QUERY_LEN = 120
MAX_EXTRA_PARAMS = 10


@dataclass(frozen=True)
class Dimension:
    """One filter dimension (multi-select).

    ``get(item)`` returns the item's value(s) for this dimension (one item may
    carry several — selecting any of them matches). ``values`` optionally
    fixes the option universe and order (e.g. lifecycle states, age buckets);
    when None the universe derives from the items themselves. ``labels`` maps
    values to display labels. ``derived=True`` marks a dimension computed from
    item content rather than a stored field — the partial labels it honestly.
    """

    key: str
    label: str
    get: Callable[[Any], Sequence[str]]
    values: Optional[Sequence[str]] = None
    labels: Optional[Mapping[str, str]] = None
    derived: bool = False


@dataclass(frozen=True)
class SortOption:
    """One sort order. ``sort_key=None`` keeps the caller's incoming order
    (for surfaces whose domain layer already sorts — the honest default)."""

    key: str
    label: str
    sort_key: Optional[Callable[[Any], Any]] = None
    reverse: bool = False


@dataclass(frozen=True)
class ListSpec:
    """One surface's whole filter/sort/search declaration. ``path`` is the
    surface's own route (URLs are always emitted relative to it — never
    echoed from the request). The FIRST sort option is the default."""

    path: str
    dimensions: Sequence[Dimension] = ()
    sorts: Sequence[SortOption] = ()
    search: Optional[Callable[[Any], str]] = None

    @property
    def default_sort(self) -> str:
        return self.sorts[0].key if self.sorts else ""


@dataclass
class ListState:
    """Validated query state. ``selected`` keeps unknown values on purpose
    (flagged later by ``apply`` — honesty over silent dropping); ``extra``
    is the pass-through tail of non-owned params (e.g. ``refresh=1``)."""

    selected: dict[str, list[str]] = field(default_factory=dict)
    sort: str = ""
    q: str = ""
    extra: list[tuple[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# parsing (whitelist keys, cap lengths — never trust the query string)
# --------------------------------------------------------------------------- #


def _getlist(params: Any, key: str) -> list[str]:
    """All values for ``key`` from a Starlette QueryParams-like (``getlist``)
    or a plain mapping (str or list values)."""
    if hasattr(params, "getlist"):
        return [str(v) for v in params.getlist(key)]
    value = params.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _multi_items(params: Any) -> list[tuple[str, str]]:
    if hasattr(params, "multi_items"):
        return [(str(k), str(v)) for k, v in params.multi_items()]
    out: list[tuple[str, str]] = []
    for k, v in params.items():
        if isinstance(v, str):
            out.append((str(k), v))
        else:
            out.extend((str(k), str(x)) for x in v)
    return out


def parse(spec: ListSpec, params: Any) -> ListState:
    """Query params → validated ``ListState``.

    Keys not owned by the spec are preserved verbatim (capped) as ``extra``
    so links keep working params like ``refresh=1``. The sort value is
    whitelisted against the spec (unknown → default). Filter VALUES are
    capped and deduplicated but deliberately NOT dropped when unknown —
    ``apply`` flags them instead.
    """
    selected: dict[str, list[str]] = {}
    for dim in spec.dimensions:
        vals: list[str] = []
        for raw in _getlist(params, dim.key):
            v = raw.strip()[:MAX_VALUE_LEN]
            if v and v not in vals:
                vals.append(v)
            if len(vals) >= MAX_VALUES_PER_DIM:
                break
        if vals:
            selected[dim.key] = vals

    raw_sort = (_getlist(params, SORT_PARAM) or [""])[0].strip()[:MAX_VALUE_LEN]
    sort = raw_sort if raw_sort in {s.key for s in spec.sorts} else spec.default_sort

    q = ""
    if spec.search is not None:
        q = (_getlist(params, Q_PARAM) or [""])[0].strip()[:MAX_QUERY_LEN]

    owned = {d.key for d in spec.dimensions} | {Q_PARAM, SORT_PARAM}
    extra: list[tuple[str, str]] = []
    for k, v in _multi_items(params):
        if k in owned:
            continue
        if len(extra) >= MAX_EXTRA_PARAMS:
            break
        extra.append((k[:MAX_VALUE_LEN], v[:MAX_VALUE_LEN]))

    return ListState(selected=selected, sort=sort, q=q, extra=extra)


# --------------------------------------------------------------------------- #
# URL builders (relative, urlencoded — the only way URLs leave this module)
# --------------------------------------------------------------------------- #


def _pairs(
    spec: ListSpec,
    state: ListState,
    *,
    selected: Optional[dict[str, list[str]]] = None,
    sort: Optional[str] = None,
    q: Optional[str] = None,
) -> list[tuple[str, str]]:
    selected = state.selected if selected is None else selected
    sort = state.sort if sort is None else sort
    q = state.q if q is None else q
    pairs = list(state.extra)
    for dim in spec.dimensions:
        pairs.extend((dim.key, v) for v in selected.get(dim.key, []))
    if q:
        pairs.append((Q_PARAM, q))
    if sort and sort != spec.default_sort:
        pairs.append((SORT_PARAM, sort))
    return pairs


def _url(spec: ListSpec, pairs: list[tuple[str, str]]) -> str:
    qs = urlencode(pairs)
    return f"{spec.path}?{qs}" if qs else spec.path


def toggle_url(spec: ListSpec, state: ListState, dim_key: str, value: str) -> str:
    """URL with ``value`` toggled on/off in ``dim_key`` (multi-select links)."""
    selected = {k: list(v) for k, v in state.selected.items()}
    vals = selected.setdefault(dim_key, [])
    if value in vals:
        vals.remove(value)
    else:
        vals.append(value)
    if not vals:
        del selected[dim_key]
    return _url(spec, _pairs(spec, state, selected=selected))


def clear_dim_url(spec: ListSpec, state: ListState, dim_key: str) -> str:
    """URL with one dimension's whole selection removed."""
    selected = {k: list(v) for k, v in state.selected.items() if k != dim_key}
    return _url(spec, _pairs(spec, state, selected=selected))


def clear_all_url(spec: ListSpec, state: ListState) -> str:
    """URL with every filter and the search dropped (sort + extras kept)."""
    return _url(spec, _pairs(spec, state, selected={}, q=""))


def drop_q_url(spec: ListSpec, state: ListState) -> str:
    """URL with only the search text removed."""
    return _url(spec, _pairs(spec, state, q=""))


def sort_url(spec: ListSpec, state: ListState, sort_key: str) -> str:
    """URL selecting a sort (the default sort is emitted param-free)."""
    return _url(spec, _pairs(spec, state, sort=sort_key))


# --------------------------------------------------------------------------- #
# applying (filter + count + sort → the partial's view model)
# --------------------------------------------------------------------------- #


def _item_values(dim: Dimension, item: Any) -> list[str]:
    try:
        raw = dim.get(item) or []
    except Exception:  # a bad item never 500s the page — it just doesn't match
        raw = []
    return [str(v) for v in raw if str(v)]


def _display(dim: Dimension, value: str) -> str:
    if dim.labels:
        return dim.labels.get(value, value)
    return value


def apply(spec: ListSpec, items: Sequence[Any], state: ListState) -> dict[str, Any]:
    """Filter + sort ``items`` per ``state`` → the partial's view model dict.

    Keys: ``items`` (filtered+sorted), ``shown``/``total``, ``active``,
    ``dims`` (options with reachable counts + selected flags + toggle URLs,
    unknown selected values flagged), ``sorts``, ``chips`` (active filters,
    each with a remove URL), ``clear_url``, ``form_fields`` (hidden inputs
    that keep the GET search form lossless), ``q``/``sort``/``selected``.
    """
    items = list(items)
    n = len(items)

    values_by_dim = {
        d.key: [_item_values(d, it) for it in items] for d in spec.dimensions
    }

    q_lower = state.q.lower()
    if q_lower and spec.search is not None:
        q_ok = [q_lower in (spec.search(it) or "").lower() for it in items]
    else:
        q_ok = [True] * n

    dim_ok: dict[str, list[bool]] = {}
    for d in spec.dimensions:
        sel = set(state.selected.get(d.key, []))
        if not sel:
            dim_ok[d.key] = [True] * n
        else:
            dim_ok[d.key] = [
                bool(sel.intersection(vs)) for vs in values_by_dim[d.key]
            ]

    passing = [
        q_ok[i] and all(dim_ok[d.key][i] for d in spec.dimensions)
        for i in range(n)
    ]
    filtered = [it for it, ok in zip(items, passing) if ok]

    sort_opt = next((s for s in spec.sorts if s.key == state.sort), None)
    if sort_opt is not None and sort_opt.sort_key is not None:
        filtered = sorted(filtered, key=sort_opt.sort_key, reverse=sort_opt.reverse)

    active = bool(state.q or state.selected)

    dims_view: list[dict[str, Any]] = []
    chips: list[dict[str, str]] = []
    for d in spec.dimensions:
        # Reachable counts: every OTHER active filter (+ search) applies,
        # this dimension's own selection does not — a pill's number is what
        # clicking it (alone within its row) would show.
        other_ok = [
            q_ok[i]
            and all(dim_ok[e.key][i] for e in spec.dimensions if e.key != d.key)
            for i in range(n)
        ]
        if d.values is not None:
            universe = list(d.values)
        else:
            universe = sorted(
                {v for vs in values_by_dim[d.key] for v in vs}, key=str.casefold
            )
        universe_set = set(universe)
        sel = state.selected.get(d.key, [])
        options = [
            {
                "value": v,
                "label": _display(d, v),
                "count": sum(
                    1
                    for i in range(n)
                    if other_ok[i] and v in values_by_dim[d.key][i]
                ),
                "selected": v in sel,
                "url": toggle_url(spec, state, d.key, v),
            }
            for v in universe
        ]
        unknown = [
            {"value": v, "url": toggle_url(spec, state, d.key, v)}
            for v in sel
            if v not in universe_set
        ]
        dims_view.append(
            {
                "key": d.key,
                "label": d.label,
                "derived": d.derived,
                "options": options,
                "unknown": unknown,
                "clear_url": clear_dim_url(spec, state, d.key),
            }
        )
        chips.extend(
            {
                "dim_label": d.label,
                "value_label": _display(d, v),
                "url": toggle_url(spec, state, d.key, v),
            }
            for v in sel
        )
    if state.q:
        chips.append(
            {"dim_label": "search", "value_label": state.q,
             "url": drop_q_url(spec, state)}
        )

    sorts_view = [
        {
            "key": s.key,
            "label": s.label,
            "selected": s.key == state.sort,
            "url": sort_url(spec, state, s.key),
        }
        for s in spec.sorts
    ]

    return {
        "path": spec.path,
        "q": state.q,
        "q_param": Q_PARAM,
        "has_search": spec.search is not None,
        "sort": state.sort,
        "selected": state.selected,
        "active": active,
        "total": n,
        "shown": len(filtered),
        "items": filtered,
        "dims": dims_view,
        "sorts": sorts_view,
        "chips": chips,
        "clear_url": clear_all_url(spec, state),
        # Hidden inputs so the GET search form re-submits the full state
        # (everything except q, which the visible input owns).
        "form_fields": _pairs(spec, state, q=""),
    }
