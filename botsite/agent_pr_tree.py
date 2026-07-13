"""Agent-PR diagnostic tree — loader for the committed ``data/agent_pr_tree.json``.

The /agent-pr-check page walks a visitor through the fleet's proven agent
merge-wall lore: why an AI agent cannot open — or cannot merge — its own
pull request, and what actually fixes each wall (ORDER 022 item 4, venture
WEBSITE-IDEA batch-2 intake). This module is a **read-only slice**: the
whole decision tree lives in a JSON file committed in this repo, curated by
hand from this fleet's verified findings (``docs/CAPABILITIES.md``,
``docs/owner/OWNER-ACTIONS.md``, the ``.github/workflows/`` landing
machinery, and the fleet-manager / substrate-kit findings docs) — cross-repo
data arrives only as committed JSON (never a live fetch in the request
path). Read from disk at request time: **no network, no secrets, stdlib
only**.

Honesty rules (the "never fake data" doctrine):

- A missing or corrupt file degrades to ``available: False`` with the exact
  reason — the page shows its honest empty state, never a crash and never an
  invented tree.
- Every leaf must carry a verdict, a concrete fix, and at least one source
  citation (``file@sha`` or a findings-doc URL) — an uncited leaf makes the
  whole tree unavailable rather than rendering unverifiable lore.
- Every option target must resolve to a real node and the tree must be
  acyclic — a dangling or circular reference degrades the page instead of
  crashing (or infinitely recursing) the template.
- Error strings in leaves are VERBATIM production errors, stored exactly as
  captured; nothing here is invented or paraphrased into fiction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
TREE_JSON_PATH = BASE_DIR / "data" / "agent_pr_tree.json"

_REQUIRED_META = ("title", "as_of", "sources")
_POLARITIES = ("ok", "danger")


def _unavailable(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_question(name: str, node: dict[str, Any], nodes: dict[str, Any]) -> str | None:
    """Return a reason string when a question node is misshapen, else None."""
    nid = node["id"]
    if not _is_nonempty_str(node.get("question")):
        return f"{name} node '{nid}' carries no question text"
    if "context" in node and not isinstance(node["context"], str):
        return f"{name} node '{nid}' carries a non-string context"
    options = node.get("options")
    if not isinstance(options, list) or not options:
        return f"{name} node '{nid}' carries no options list"
    for opt in options:
        if not isinstance(opt, dict) or not _is_nonempty_str(opt.get("label")):
            return f"{name} node '{nid}' carries an option without a label"
        target = opt.get("next")
        if not _is_nonempty_str(target):
            return f"{name} node '{nid}' carries an option without a 'next' target"
        if target not in nodes:
            return f"{name} node '{nid}' option targets unknown node '{target}'"
    return None


def _validate_leaf(name: str, node: dict[str, Any]) -> str | None:
    """Return a reason string when a leaf node is misshapen, else None."""
    nid = node["id"]
    for field in ("verdict", "fix"):
        if not _is_nonempty_str(node.get(field)):
            return f"{name} leaf '{nid}' is missing its '{field}'"
    sources = node.get("sources")
    if not isinstance(sources, list) or not sources or not all(_is_nonempty_str(s) for s in sources):
        return f"{name} leaf '{nid}' carries no source citations — uncited lore never renders"
    if "error" in node and not _is_nonempty_str(node["error"]):
        return f"{name} leaf '{nid}' carries an empty 'error' string"
    if node.get("polarity", "danger") not in _POLARITIES:
        return f"{name} leaf '{nid}' carries an unknown polarity"
    return None


def _find_cycle(root: str, nodes: dict[str, Any]) -> str | None:
    """Return a node id on a cycle reachable from root, else None (DFS)."""
    done: set[str] = set()

    def visit(nid: str, path: frozenset[str]) -> str | None:
        if nid in path:
            return nid
        if nid in done:
            return None
        for opt in nodes[nid].get("options", []):
            hit = visit(opt["next"], path | {nid})
            if hit is not None:
                return hit
        done.add(nid)
        return None

    return visit(root, frozenset())


def load_tree(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the diagnostic tree from disk.

    Returns ``{"available": True, "meta": ..., "root": ..., "nodes": {id:
    node}, "question_count": ..., "leaf_count": ...}`` or ``{"available":
    False, "reason": ...}`` on a missing/corrupt/misshapen file — the
    template renders the honest empty state from the reason.
    """
    src = path or TREE_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except OSError:
        return _unavailable(f"{src.name} is missing — the committed diagnostic tree is not on disk")
    except ValueError:
        return _unavailable(f"{src.name} is not valid JSON — the committed tree is corrupt")

    if not isinstance(raw, dict):
        return _unavailable(f"{src.name} is not a JSON object — the committed tree is misshapen")
    meta = raw.get("meta")
    if not isinstance(meta, dict) or any(field not in meta for field in _REQUIRED_META):
        return _unavailable(f"{src.name} is missing its 'meta' block (title / as_of / sources)")
    if not _is_nonempty_str(meta.get("title")) or not _is_nonempty_str(meta.get("as_of")):
        return _unavailable(f"{src.name} carries an empty meta title or as_of")
    meta_sources = meta.get("sources")
    if not isinstance(meta_sources, list) or not meta_sources or not all(_is_nonempty_str(s) for s in meta_sources):
        return _unavailable(f"{src.name} carries a misshapen meta 'sources' list")

    root = raw.get("root")
    if not _is_nonempty_str(root):
        return _unavailable(f"{src.name} declares no 'root' node id")
    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, list) or not nodes_raw:
        return _unavailable(f"{src.name} carries no 'nodes' list")

    nodes: dict[str, dict[str, Any]] = {}
    for node in nodes_raw:
        if not isinstance(node, dict) or not _is_nonempty_str(node.get("id")):
            return _unavailable(f"{src.name} carries a node without a string 'id'")
        if node["id"] in nodes:
            return _unavailable(f"{src.name} carries duplicate node id '{node['id']}'")
        nodes[node["id"]] = node
    if root not in nodes:
        return _unavailable(f"{src.name} root '{root}' does not resolve to a node")

    question_count = 0
    leaf_count = 0
    for node in nodes.values():
        if "question" in node or "options" in node:
            reason = _validate_question(src.name, node, nodes)
            question_count += 1
        else:
            reason = _validate_leaf(src.name, node)
            leaf_count += 1
        if reason is not None:
            return _unavailable(reason)

    cyclic = _find_cycle(root, nodes)
    if cyclic is not None:
        return _unavailable(f"{src.name} carries a cycle through node '{cyclic}' — the tree must be acyclic")

    return {
        "available": True,
        "reason": "",
        "meta": meta,
        "root": root,
        "nodes": nodes,
        "question_count": question_count,
        "leaf_count": leaf_count,
    }
