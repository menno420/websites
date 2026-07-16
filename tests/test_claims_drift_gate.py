"""Claims-drift gate — no `control/claims/*.md` may outlive its merged branch.

The claim convention (``control/claims/README.md``) says a claim is a
whiteboard note deleted at session close; the durable record is the PR. The
2026-07-13 fleet cleanup audit (``docs/audits/2026-07-13-fleet-cleanup-audit.md``,
finding 1 + suggestion 2) caught the drift class this pin now automates:
``control/claims/2026-07-13-railway-placeholders.md`` outlived its own merged
PR #275, and only a hand audit noticed. This gate fails ``quality`` when a
claim file references a branch that is already TERMINAL on main.

Terminality is decided with pure git plumbing — zero network:

1. **true merge / fast-forward** — ``git merge-base --is-ancestor <branch>
   <main>`` (the branch tip is in main's history).
2. **squash merge** (this repo's normal landing path) — the branch tip is
   NOT an ancestor, so compare patch-ids instead: the branch's combined diff
   vs its merge-base gets one ``git patch-id --stable``, and each commit on
   ``<merge-base>..<main>`` (newest first, capped) is checked for the same
   patch-id. A hit is the squash commit — the work landed.
3. **pruned-ref fallback via an optional ``PR #N`` bullet token**
   (2026-07-16, closes a 2026-07-14 backlog idea) — lane 2 needs the
   branch ref to diff against; a repo that prunes branches on merge (or
   any claim whose branch was simply never pushed) makes the ref resolve
   to nothing, which the gate has always treated as indeterminate-live.
   If the claim bullet carries a trailing `` · PR #N `` token (appended by
   hand once the PR opens — no kit/grammar change, pure free text this
   gate alone reads), a pruned/unresolvable ref falls back to
   ``git log <main> --grep='(#N)' --fixed-strings`` — a hit is this
   repo's squash-merge subject convention (``<title> (#N)``), so the work
   landed even though the branch itself is gone. No token, no fallback —
   ref-less stays exactly as fail-safe-live as before.

Everything else is deliberately treated as LIVE (fail-safe, never flag):
an unparseable bullet or a scope-only token (``check_claims``'s
``claims-format`` territory), a branch that resolves to no ref AND
carries no PR token (never pushed, or pruned with nothing to fall back
on), a squash whose patch-id drifted (merge conflicts resolved in the PR,
or the scan cap exceeded). A live claim for an open branch must always
pass — the gate exists to catch orphans, not to nag in-flight work.

The committed-tree pin runs first; the synthetic-repo tests prove the
detector itself (squash / true-merge / live / pruned-ref-with-PR /
unknown) so the pin never silently rots into pass-everything.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAIMS_DIR = REPO_ROOT / "control" / "claims"

# Commits scanned (newest first) on <merge-base>..<main> for the squash
# patch-id. Claims expire at ~72h (README) and this repo merges tens of PRs
# a day at peak, so 500 is generous headroom; past the cap the claim is
# treated as live (fail-safe), never flagged.
SQUASH_SCAN_CAP = 500

# The claim bullet's leading backticked token (the branch-or-scope slot):
#   - `claude/railway-placeholders` · **scope** — detail · area · 2026-07-13
_CLAIM_TOKEN = re.compile(r"^-\s+`([^`\s]+)`")

# The optional trailing PR-number token (anywhere on the bullet line, not
# grammar-anchored like the leading token — free text this gate alone
# reads, no kit/grammar coupling):
#   - `claude/foo` · **scope** — detail · area · 2026-07-16 · PR #123
_CLAIM_PR = re.compile(r"PR\s+#(\d+)\b")


# --------------------------------------------------------------------------- #
# git plumbing helpers
# --------------------------------------------------------------------------- #
def _git(args: list[str], cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, input=input_text
    )


def _rev(cwd: Path, ref: str) -> str | None:
    res = _git(["rev-parse", "--verify", "--quiet", ref], cwd)
    out = res.stdout.strip()
    return out if res.returncode == 0 and out else None


def parse_claim_branch(text: str) -> str | None:
    """First backticked token of the claim bullet, or None (unparseable)."""
    for line in text.splitlines():
        m = _CLAIM_TOKEN.match(line.strip())
        if m:
            return m.group(1)
    return None


def parse_claim_pr(text: str) -> str | None:
    """The bullet's `` PR #N `` token (digits only), or None if absent."""
    for line in text.splitlines():
        if _CLAIM_TOKEN.match(line.strip()):
            m = _CLAIM_PR.search(line)
            if m:
                return m.group(1)
    return None


def resolve_branch_ref(cwd: Path, token: str) -> str | None:
    """The token's ref if it exists (remote-tracking first), else None."""
    for candidate in (f"refs/remotes/origin/{token}", f"refs/heads/{token}"):
        if _rev(cwd, candidate):
            return candidate
    return None


def resolve_via_pr_grep(cwd: Path, main_ref: str, pr_number: str) -> bool:
    """True when a commit on ``main_ref`` carries this repo's squash-merge
    subject convention ``... (#<pr_number>)`` — the pruned-ref fallback.

    ``--fixed-strings`` so the number is matched literally (never a regex),
    and the search string wraps the digits in parens exactly like the
    convention (``(#N)``) so ``#12`` can never false-match a commit naming
    ``#123``."""
    res = _git(
        [
            "log",
            main_ref,
            "--fixed-strings",
            f"--grep=(#{pr_number})",
            "--format=%H",
            "-1",
        ],
        cwd,
    )
    return res.returncode == 0 and bool(res.stdout.strip())


def _combined_patch_id(cwd: Path, base: str, tip: str) -> str | None:
    diff = _git(["diff", base, tip], cwd).stdout
    if not diff.strip():
        return None
    fields = _git(["patch-id", "--stable"], cwd, input_text=diff).stdout.split()
    return fields[0] if fields else None


def branch_is_terminal(cwd: Path, branch_ref: str, main_ref: str) -> bool:
    """True when the branch's work verifiably landed on main (see module doc)."""
    # Lane 1: true merge / fast-forward — tip is in main's history.
    if _git(["merge-base", "--is-ancestor", branch_ref, main_ref], cwd).returncode == 0:
        return True
    # Lane 2: squash merge — combined-diff patch-id appears on main.
    mb = _git(["merge-base", main_ref, branch_ref], cwd).stdout.strip()
    if not mb:
        return False  # unrelated histories — indeterminate, treat live
    want = _combined_patch_id(cwd, mb, branch_ref)
    if want is None:
        return False  # empty diff yet not an ancestor — indeterminate
    commits = _git(
        ["rev-list", "--max-count", str(SQUASH_SCAN_CAP), f"{mb}..{main_ref}"], cwd
    ).stdout.split()
    for commit in commits:
        # Diff vs first parent; a root commit's `^` fails -> empty -> skipped.
        if _combined_patch_id(cwd, f"{commit}^", commit) == want:
            return True
    return False


def stale_claims(
    repo_root: Path, claims_dir: Path, main_ref: str
) -> list[tuple[Path, str]]:
    """(claim file, branch token) pairs whose branch is terminal on main."""
    found: list[tuple[Path, str]] = []
    for path in sorted(claims_dir.glob("*.md")):
        if path.name == "README.md":  # the convention doc, never a claim
            continue
        text = path.read_text(encoding="utf-8")
        token = parse_claim_branch(text)
        if not token or "/" not in token:
            continue  # unparseable or scope-only — claims-format territory, live
        ref = resolve_branch_ref(repo_root, token)
        if ref is None:
            # Never pushed, or pruned after merge — indeterminate from the
            # ref alone. A bullet-carried `PR #N` token gives one more
            # shot before falling back to fail-safe-live.
            pr_number = parse_claim_pr(text)
            if pr_number and resolve_via_pr_grep(repo_root, main_ref, pr_number):
                found.append((path, token))
            continue
        if branch_is_terminal(repo_root, ref, main_ref):
            found.append((path, token))
    return found


def _main_ref(cwd: Path) -> str | None:
    for candidate in ("refs/remotes/origin/main", "refs/heads/main"):
        if _rev(cwd, candidate):
            return candidate
    return None


# --------------------------------------------------------------------------- #
# The pin — the committed claims dir carries no orphaned claim
# --------------------------------------------------------------------------- #
def test_no_claim_outlives_its_merged_branch():
    """Every `control/claims/*.md` must reference LIVE work. A claim whose
    branch already landed on main is an orphan the session forgot to delete
    at close (claims README step 4) — delete the claim file to go green."""
    main_ref = _main_ref(REPO_ROOT)
    if main_ref is None:
        pytest.skip("no main ref in this checkout — cannot grade claims")
    orphans = stale_claims(REPO_ROOT, CLAIMS_DIR, main_ref)
    assert not orphans, (
        "Orphaned claim(s) — the referenced branch already merged into main; "
        "the session that owned each claim should have deleted it at close "
        "(control/claims/README.md step 4). Delete the file(s): "
        + ", ".join(f"{p.relative_to(REPO_ROOT)} (branch `{t}`)" for p, t in orphans)
    )


# --------------------------------------------------------------------------- #
# Detector proofs — a synthetic repo with known-terminal / known-live branches
# --------------------------------------------------------------------------- #
def _commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    assert _git(["add", name], repo).returncode == 0
    assert _git(["commit", "-q", "-m", message], repo).returncode == 0


@pytest.fixture()
def synth_repo(tmp_path: Path) -> Path:
    """main + three branches: squash-merged (2 commits, with main drifting
    over a branch-touched file AFTER the squash — the railway-placeholders
    shape), fast-forward-merged (tip is an ancestor), and live (unmerged)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(["init", "-q", "-b", "main"], repo).returncode == 0
    for k, v in (("user.email", "t@example.invalid"), ("user.name", "t")):
        assert _git(["config", k, v], repo).returncode == 0
    _commit_file(repo, "base.txt", "base\n", "base")

    # Squash-merged branch: two commits, squashed onto main as one.
    assert _git(["checkout", "-q", "-b", "claude/squashed"], repo).returncode == 0
    _commit_file(repo, "feature.txt", "one\n", "feature part 1")
    _commit_file(repo, "shared.txt", "branch text\n", "feature part 2")
    assert _git(["checkout", "-q", "main"], repo).returncode == 0
    assert _git(["merge", "--squash", "-q", "claude/squashed"], repo).returncode == 0
    assert _git(["commit", "-q", "-m", "feature (#1)"], repo).returncode == 0
    # Main drifts AFTER the squash, over a file the branch touched.
    _commit_file(repo, "shared.txt", "branch text\nmain drift\n", "later main edit")

    # Ancestor branch: points at a commit already inside main's history.
    assert (
        _git(["branch", "claude/ancestor", "main~1"], repo).returncode == 0
    )

    # Live branch: forked from main, unmerged work.
    assert _git(["checkout", "-q", "-b", "claude/live"], repo).returncode == 0
    _commit_file(repo, "wip.txt", "wip\n", "in-flight work")
    assert _git(["checkout", "-q", "main"], repo).returncode == 0

    # Pruned-ref branch: squash-merged (subject carries "(#99)", this
    # repo's convention) then its local ref DELETED — resolve_branch_ref
    # must return None, exercising the PR-grep fallback lane.
    assert _git(["checkout", "-q", "-b", "claude/pruned"], repo).returncode == 0
    _commit_file(repo, "pruned.txt", "pruned\n", "pruned feature")
    assert _git(["checkout", "-q", "main"], repo).returncode == 0
    assert _git(["merge", "--squash", "-q", "claude/pruned"], repo).returncode == 0
    assert _git(["commit", "-q", "-m", "pruned feature (#99)"], repo).returncode == 0
    assert _git(["branch", "-D", "claude/pruned"], repo).returncode == 0

    return repo


def test_squash_merged_branch_is_terminal(synth_repo: Path):
    """The repo's normal landing path: tip NOT an ancestor of main, but the
    combined-diff patch-id matches the squash commit — terminal even after
    main later edits a branch-touched file."""
    ref = resolve_branch_ref(synth_repo, "claude/squashed")
    assert ref == "refs/heads/claude/squashed"
    assert (
        _git(["merge-base", "--is-ancestor", ref, "main"], synth_repo).returncode != 0
    ), "fixture must exercise the squash lane, not the ancestor lane"
    assert branch_is_terminal(synth_repo, ref, "main")


def test_ancestor_branch_is_terminal(synth_repo: Path):
    ref = resolve_branch_ref(synth_repo, "claude/ancestor")
    assert ref and branch_is_terminal(synth_repo, ref, "main")


def test_live_branch_is_live(synth_repo: Path):
    """An open branch with unmerged work must NEVER be flagged."""
    ref = resolve_branch_ref(synth_repo, "claude/live")
    assert ref and not branch_is_terminal(synth_repo, ref, "main")


def test_pruned_ref_resolves_to_none(synth_repo: Path):
    """Fixture sanity: the pruned branch's ref is genuinely gone."""
    assert resolve_branch_ref(synth_repo, "claude/pruned") is None


def test_pr_grep_fallback_finds_the_landed_squash(synth_repo: Path):
    assert resolve_via_pr_grep(synth_repo, "main", "99")


def test_pr_grep_fallback_misses_an_unlanded_pr(synth_repo: Path):
    """A PR number that never landed must never false-positive."""
    assert not resolve_via_pr_grep(synth_repo, "main", "424242")


def test_pr_grep_fallback_is_a_literal_match_not_a_prefix(synth_repo: Path):
    """`#9` must not match a commit naming `#99` (fixed-string, parens-wrapped)."""
    assert not resolve_via_pr_grep(synth_repo, "main", "9")


def test_stale_claims_flags_only_the_orphans(synth_repo: Path):
    """End-to-end over a claims dir: orphan flagged; live claim, README,
    never-pushed branch, and a scope-only token all pass."""
    claims = synth_repo / "control" / "claims"
    claims.mkdir(parents=True)
    (claims / "README.md").write_text("# convention doc\n", encoding="utf-8")
    (claims / "orphan.md").write_text(
        "# Claim\n\n- `claude/squashed` · **feature** — landed · files · 2026-07-14\n",
        encoding="utf-8",
    )
    (claims / "live.md").write_text(
        "# Claim\n\n- `claude/live` · **wip** — in flight · files · 2026-07-14\n",
        encoding="utf-8",
    )
    (claims / "unpushed.md").write_text(
        "# Claim\n\n- `claude/not-yet-pushed` · **wip** — no ref yet · files · 2026-07-14\n",
        encoding="utf-8",
    )
    (claims / "scope-only.md").write_text(
        "# Claim\n\n- `docs-sweep` · **scope token** — no branch · files · 2026-07-14\n",
        encoding="utf-8",
    )
    (claims / "pruned-landed.md").write_text(
        "# Claim\n\n- `claude/pruned` · **feature** — landed, ref pruned · "
        "files · 2026-07-14 · PR #99\n",
        encoding="utf-8",
    )
    (claims / "pruned-unlanded.md").write_text(
        "# Claim\n\n- `claude/never-opened` · **wip** — PR opened, not merged · "
        "files · 2026-07-14 · PR #424242\n",
        encoding="utf-8",
    )
    orphans = stale_claims(synth_repo, claims, "main")
    assert sorted((p.name, t) for p, t in orphans) == [
        ("orphan.md", "claude/squashed"),
        ("pruned-landed.md", "claude/pruned"),
    ]


def test_parse_claim_branch_grammar():
    assert (
        parse_claim_branch(
            "# Claim — X\n\n- `claude/railway-placeholders` · **scope** — d · a · 2026-07-13\n"
        )
        == "claude/railway-placeholders"
    )
    assert parse_claim_branch("# heading only\nprose, no bullet\n") is None


def test_parse_claim_pr_grammar():
    assert (
        parse_claim_pr(
            "# Claim\n\n- `claude/foo` · **scope** — d · a · 2026-07-16 · PR #123\n"
        )
        == "123"
    )
    # No PR token at all — the common case, must not raise or invent one.
    assert (
        parse_claim_pr("# Claim\n\n- `claude/foo` · **scope** — d · a · 2026-07-16\n")
        is None
    )
    # A "PR #N" mention in prose ABOVE the bullet line must not leak in —
    # only the bullet line itself is scanned.
    assert (
        parse_claim_pr(
            "# Claim\n\nSee PR #999 for context.\n\n"
            "- `claude/foo` · **scope** — d · a · 2026-07-16\n"
        )
        is None
    )
