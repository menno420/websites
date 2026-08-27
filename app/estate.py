"""Stable domain models for the owner-facing repository estate.

The estate reader may change from Markdown today to a generated digest later;
routes and templates should not need to know.  This module is therefore pure
domain code: no FastAPI, templates, configuration, or network access.  It owns
the normalized lifecycle vocabulary, provenance/freshness semantics, and the
centralized ``/repos`` list declaration.

Two clocks are deliberately separate throughout:

``retrieved_at``
    when this service obtained a source; and
``fact_as_of``
    when the source says the displayed fact was true.

A freshly downloaded old ledger is consequently still measured/verified (or
stale), never silently promoted to live.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from typing import Iterable, Optional, Sequence
from urllib.parse import quote

from . import clock, listfilter

UTC = timezone.utc
STALE_AFTER = timedelta(days=14)
RECENT_ACTIVITY_WINDOW = timedelta(days=14)
NEXT_THREAD_UNKNOWN = "Current next step not confidently established."


class RepositoryStatus(str, Enum):
    """The deliberately small lifecycle vocabulary used by the UI."""

    ACTIVE = "active"
    PAUSED = "paused"
    FROZEN = "frozen"
    INFRASTRUCTURE = "infrastructure"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return {
            self.ACTIVE: "Active",
            self.PAUSED: "Paused",
            self.FROZEN: "Frozen",
            self.INFRASTRUCTURE: "Infrastructure",
            self.ARCHIVED: "Archived",
            self.UNKNOWN: "Unknown",
        }[self]

    @property
    def css_class(self) -> str:
        return f"state-{self.value}"


class FreshnessState(str, Enum):
    LIVE = "live"
    MEASURED = "measured"
    LAST_VERIFIED = "last-verified"
    STALE = "stale"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


def _utc_datetime(value: datetime | date) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return datetime.combine(value, time.min, tzinfo=UTC)


def _now(value: Optional[datetime] = None) -> datetime:
    return _utc_datetime(value or clock.now())


def _plural(amount: int, unit: str) -> str:
    return f"{amount} {unit}{'' if amount == 1 else 's'}"


@dataclass(frozen=True)
class Freshness:
    """How current one fact is, with retrieval and fact time kept separate."""

    state: FreshnessState
    retrieved_at: Optional[datetime] = None
    fact_as_of: Optional[datetime] = None
    evaluated_at: datetime = field(default_factory=clock.now)
    method: str = ""
    fact_precision: str = "datetime"
    reason: str = ""

    def __post_init__(self) -> None:
        state = self.state
        if not isinstance(state, FreshnessState):
            state = FreshnessState(str(state))
            object.__setattr__(self, "state", state)
        object.__setattr__(self, "evaluated_at", _utc_datetime(self.evaluated_at))
        if self.retrieved_at is not None:
            object.__setattr__(
                self, "retrieved_at", _utc_datetime(self.retrieved_at)
            )
        if self.fact_as_of is not None:
            object.__setattr__(self, "fact_as_of", _utc_datetime(self.fact_as_of))

    @classmethod
    def live(
        cls,
        retrieved_at: Optional[datetime] = None,
        *,
        fact_as_of: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> "Freshness":
        checked = _utc_datetime(retrieved_at) if retrieved_at else _now(now)
        return cls(
            FreshnessState.LIVE,
            retrieved_at=checked,
            fact_as_of=_utc_datetime(fact_as_of) if fact_as_of else checked,
            evaluated_at=_now(now) if now else checked,
            method="live",
        )

    @classmethod
    def measured(
        cls,
        fact_as_of: datetime | date,
        *,
        retrieved_at: Optional[datetime] = None,
        now: Optional[datetime] = None,
        stale_after: timedelta = STALE_AFTER,
    ) -> "Freshness":
        evaluated = _now(now)
        fact = _utc_datetime(fact_as_of)
        state = (
            FreshnessState.STALE
            if evaluated - fact > stale_after
            else FreshnessState.MEASURED
        )
        return cls(
            state,
            retrieved_at=retrieved_at,
            fact_as_of=fact,
            evaluated_at=evaluated,
            method="measured",
            fact_precision=(
                "date"
                if isinstance(fact_as_of, date)
                and not isinstance(fact_as_of, datetime)
                else "datetime"
            ),
        )

    @classmethod
    def last_verified(
        cls,
        fact_as_of: datetime | date,
        *,
        retrieved_at: Optional[datetime] = None,
        now: Optional[datetime] = None,
        stale_after: timedelta = STALE_AFTER,
    ) -> "Freshness":
        evaluated = _now(now)
        fact = _utc_datetime(fact_as_of)
        state = (
            FreshnessState.STALE
            if evaluated - fact > stale_after
            else FreshnessState.LAST_VERIFIED
        )
        return cls(
            state,
            retrieved_at=retrieved_at,
            fact_as_of=fact,
            evaluated_at=evaluated,
            method="last-verified",
            fact_precision=(
                "date"
                if isinstance(fact_as_of, date)
                and not isinstance(fact_as_of, datetime)
                else "datetime"
            ),
        )

    @classmethod
    def unknown(
        cls,
        *,
        retrieved_at: Optional[datetime] = None,
        reason: str = "",
        now: Optional[datetime] = None,
    ) -> "Freshness":
        return cls(
            FreshnessState.UNKNOWN,
            retrieved_at=retrieved_at,
            evaluated_at=_now(now),
            method="unknown",
            reason=reason,
        )

    @classmethod
    def unavailable(
        cls,
        *,
        retrieved_at: Optional[datetime] = None,
        reason: str = "",
        now: Optional[datetime] = None,
    ) -> "Freshness":
        return cls(
            FreshnessState.UNAVAILABLE,
            retrieved_at=retrieved_at,
            evaluated_at=_now(now),
            method="unavailable",
            reason=reason,
        )

    @property
    def kind(self) -> str:
        """String alias convenient in templates and serialized views."""
        return self.state.value

    @property
    def css_class(self) -> str:
        return f"freshness-{self.state.value}"

    @property
    def is_live(self) -> bool:
        return self.state is FreshnessState.LIVE

    @property
    def is_stale(self) -> bool:
        return self.state is FreshnessState.STALE

    @property
    def is_available(self) -> bool:
        return self.state is not FreshnessState.UNAVAILABLE

    @property
    def age(self) -> Optional[timedelta]:
        if self.fact_as_of is None:
            return None
        return max(self.evaluated_at - self.fact_as_of, timedelta(0))

    @property
    def age_hours(self) -> Optional[float]:
        return self.age.total_seconds() / 3600 if self.age is not None else None

    @property
    def age_label(self) -> str:
        age = self.age
        if age is None:
            return "age unknown"
        seconds = int(age.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{_plural(minutes, 'minute')} ago"
        hours = seconds // 3600
        if hours < 48:
            return f"{_plural(hours, 'hour')} ago"
        days = seconds // 86400
        return f"{_plural(days, 'day')} ago"

    @property
    def fact_as_of_label(self) -> str:
        if self.fact_as_of is None:
            return "Fact date unknown"
        if self.fact_precision == "date":
            return self.fact_as_of.date().isoformat()
        return self.fact_as_of.strftime("%Y-%m-%d %H:%M UTC")

    @property
    def retrieval_label(self) -> str:
        if self.retrieved_at is None:
            return "Retrieval time unknown"
        return f"Retrieved {self.retrieved_at.strftime('%Y-%m-%d %H:%M UTC')}"

    @property
    def label(self) -> str:
        if self.state is FreshnessState.LIVE:
            return "Live"
        if self.state is FreshnessState.MEASURED:
            return f"Measured {self.age_label}"
        if self.state is FreshnessState.LAST_VERIFIED:
            return f"Last verified {self.fact_as_of_label}"
        if self.state is FreshnessState.STALE:
            return "Stale"
        if self.state is FreshnessState.UNAVAILABLE:
            return "Unavailable"
        return "Unknown"

    @property
    def detail(self) -> str:
        if self.state is FreshnessState.STALE:
            if self.method == "last-verified":
                return f"Last verified {self.fact_as_of_label}"
            return f"Measured {self.age_label}"
        if self.state in {FreshnessState.UNKNOWN, FreshnessState.UNAVAILABLE}:
            return self.reason or self.label
        return self.label


@dataclass(frozen=True)
class SourceReference:
    """A pointer to evidence; source content stays in its owning repository."""

    label: str
    url: str
    repository: str = ""
    path: str = ""
    authority: str = "supporting"
    freshness: Freshness = field(default_factory=Freshness.unknown)
    available: Optional[bool] = True

    @property
    def repo(self) -> str:
        return self.repository

    @property
    def display_label(self) -> str:
        return self.label or self.path or self.repository or "Source"

    @property
    def location(self) -> str:
        if self.repository and self.path:
            return f"{self.repository}/{self.path}"
        return self.path or self.repository

    @property
    def availability_label(self) -> str:
        if self.available is True:
            return "Available"
        if self.available is False:
            return "Unavailable"
        return "Unknown"

    @property
    def is_authoritative(self) -> bool:
        return self.authority == "authoritative"


@dataclass(frozen=True)
class Activity:
    summary: str
    occurred_at: Optional[datetime] = None
    kind: str = "activity"
    source: Optional[SourceReference] = None
    freshness: Freshness = field(default_factory=Freshness.unknown)

    def __post_init__(self) -> None:
        if self.occurred_at is not None:
            object.__setattr__(self, "occurred_at", _utc_datetime(self.occurred_at))

    def is_recent(
        self,
        *,
        now: Optional[datetime] = None,
        within: timedelta = RECENT_ACTIVITY_WINDOW,
    ) -> bool:
        if self.occurred_at is None:
            return False
        evaluated = _now(now) if now else self.freshness.evaluated_at
        age = evaluated - self.occurred_at
        return timedelta(0) <= age <= within

    @property
    def timestamp_label(self) -> str:
        if self.occurred_at is None:
            return "Time unknown"
        return self.occurred_at.strftime("%Y-%m-%d %H:%M UTC")


@dataclass(frozen=True)
class OwnerCommentSummary:
    """Tri-state comment counts: ``None`` is unknown, distinct from zero."""

    unconsumed_count: Optional[int] = None
    consumed_count: Optional[int] = None
    freshness: Freshness = field(default_factory=Freshness.unknown)
    source: Optional[SourceReference] = None

    def __post_init__(self) -> None:
        for name in ("unconsumed_count", "consumed_count"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")

    @property
    def open_count(self) -> Optional[int]:
        return self.unconsumed_count

    @property
    def is_known(self) -> bool:
        return self.unconsumed_count is not None and self.consumed_count is not None

    @property
    def total_count(self) -> Optional[int]:
        if not self.is_known:
            return None
        return (self.unconsumed_count or 0) + (self.consumed_count or 0)

    @property
    def has_unconsumed(self) -> Optional[bool]:
        if self.unconsumed_count is None:
            return None
        return self.unconsumed_count > 0

    @property
    def has_comments(self) -> Optional[bool]:
        known_counts = [
            count
            for count in (self.unconsumed_count, self.consumed_count)
            if count is not None
        ]
        if any(count > 0 for count in known_counts):
            return True
        if self.is_known:
            return False
        return None

    @property
    def label(self) -> str:
        if self.freshness.state is FreshnessState.UNAVAILABLE:
            return "Comments unavailable"
        if self.unconsumed_count is None:
            return "Comments unknown"
        if self.unconsumed_count:
            return (
                f"{self.unconsumed_count} owner "
                f"comment{'' if self.unconsumed_count == 1 else 's'} awaiting action"
            )
        if self.is_known and self.total_count == 0:
            return "No owner comments"
        if self.consumed_count:
            return (
                f"{self.consumed_count} owner "
                f"comment{'' if self.consumed_count == 1 else 's'} consumed"
            )
        return "No unconsumed comments · history unknown"


@dataclass(frozen=True)
class StatusResolution:
    status: RepositoryStatus
    raw_status: str
    warnings: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        return self.status.label

    @property
    def css_class(self) -> str:
        return self.status.css_class


_STATUS_PATTERNS: tuple[tuple[RepositoryStatus, re.Pattern[str]], ...] = (
    (
        RepositoryStatus.ARCHIVED,
        re.compile(r"^(?:📦\s*)?archiv(?:e|ed)\b", re.I),
    ),
    (RepositoryStatus.FROZEN, re.compile(r"\bfrozen\b", re.I)),
    (
        RepositoryStatus.INFRASTRUCTURE,
        re.compile(r"\binfrastructure\b", re.I),
    ),
    (
        RepositoryStatus.PAUSED,
        re.compile(
            r"\b(?:paused|parked|on[- ]demand|at rest|dormant|owner[- ]gated|waiting)\b",
            re.I,
        ),
    ),
    (RepositoryStatus.ACTIVE, re.compile(r"\bactive\b", re.I)),
)


def _leading_state_phrase(text: str) -> str:
    """Return the lifecycle assertion, excluding later explanatory prose.

    Fleet Manager state cells often explain future archive gates after an em
    dash.  Those mentions are context, not the repository's current state.
    Only the leading assertion (or a leading explicit archive marker) may
    drive normalization when live GitHub metadata is unavailable.
    """

    value = re.sub(r"[`*_~]", "", str(text or "")).strip()
    value = re.split(r"\s+[—–]\s+|[\r\n]+", value, maxsplit=1)[0]
    return value[:160].strip()


def _status_from_text(text: str, *, allow_archived: bool = True) -> RepositoryStatus:
    text = _leading_state_phrase(text)
    for status, pattern in _STATUS_PATTERNS:
        if status is RepositoryStatus.ARCHIVED and not allow_archived:
            continue
        if pattern.search(text or ""):
            return status
    return RepositoryStatus.UNKNOWN


def _status_from_section(section: str) -> RepositoryStatus:
    value = (section or "").casefold()
    if "frozen" in value or "experiment" in value or "exemplar" in value:
        return RepositoryStatus.FROZEN
    if "paused" in value or "owner-gated" in value:
        return RepositoryStatus.PAUSED
    if "active" in value:
        return RepositoryStatus.ACTIVE
    if "archive" in value:
        return RepositoryStatus.ARCHIVED
    return RepositoryStatus.UNKNOWN


def _section_compatible(section_status: RepositoryStatus, status: RepositoryStatus) -> bool:
    if section_status is RepositoryStatus.UNKNOWN or status is RepositoryStatus.UNKNOWN:
        return True
    compatible = {
        RepositoryStatus.ACTIVE: {
            RepositoryStatus.ACTIVE,
            RepositoryStatus.INFRASTRUCTURE,
        },
        RepositoryStatus.PAUSED: {
            RepositoryStatus.PAUSED,
            RepositoryStatus.FROZEN,
            RepositoryStatus.ARCHIVED,
        },
        RepositoryStatus.FROZEN: {
            RepositoryStatus.FROZEN,
            RepositoryStatus.PAUSED,
            RepositoryStatus.ARCHIVED,
        },
        RepositoryStatus.ARCHIVED: {RepositoryStatus.ARCHIVED},
    }
    return status in compatible.get(section_status, {section_status})


def normalize_repository_status(
    raw_status: str,
    *,
    section: str = "",
    live_archived: Optional[bool] = None,
    additional_raw_statuses: Sequence[str] = (),
) -> StatusResolution:
    """Normalize a ledger phrase without losing it or hiding conflicts.

    Explicit raw wording beats a broad table section (so ``superbot`` remains
    frozen even though its row lives under Active).  A live GitHub archived
    boolean, when supplied, beats both.  Conflicts stay visible as warnings.
    """

    raw = (raw_status or "").strip()
    warnings: list[str] = []
    section_status = _status_from_section(section)
    raw_status_value = _status_from_text(
        raw, allow_archived=live_archived is not False
    )

    if live_archived is True:
        status = RepositoryStatus.ARCHIVED
        non_archive = _status_from_text(raw, allow_archived=False)
        if non_archive is not RepositoryStatus.UNKNOWN:
            warnings.append(
                "Live GitHub state is archived; Fleet Manager wording says "
                f"{non_archive.value}."
            )
    elif live_archived is False:
        status = raw_status_value
        if _status_from_text(raw) is RepositoryStatus.ARCHIVED:
            warnings.append(
                "Fleet Manager says archived, but live GitHub state is not archived."
            )
        if status is RepositoryStatus.UNKNOWN:
            status = section_status
    else:
        status = raw_status_value

    if status is RepositoryStatus.UNKNOWN:
        status = section_status

    if not _section_compatible(section_status, status):
        warnings.append(
            f"Fleet Manager section suggests {section_status.value}, while the "
            f"raw state says {status.value}."
        )

    for other in additional_raw_statuses:
        other_status = _status_from_text(other)
        if (
            other_status is not RepositoryStatus.UNKNOWN
            and other_status is not status
            and not (
                status is RepositoryStatus.INFRASTRUCTURE
                and other_status is RepositoryStatus.ACTIVE
            )
        ):
            warnings.append(
                f"Another source says {other_status.value}: {(other or '').strip()}"
            )

    # Preserve order while collapsing duplicate warnings from repeated sources.
    return StatusResolution(status, raw, tuple(dict.fromkeys(warnings)))


# Short alias for callers that already sit in an estate context.
normalize_status = normalize_repository_status


@dataclass(frozen=True)
class RepositorySummary:
    name: str
    purpose: str = ""
    status: RepositoryStatus = RepositoryStatus.UNKNOWN
    raw_status: str = ""
    status_freshness: Freshness = field(default_factory=Freshness.unknown)
    status_source: Optional[SourceReference] = None
    freshness: Freshness = field(default_factory=Freshness.unknown)
    sources: tuple[SourceReference, ...] = ()
    activities: tuple[Activity, ...] = ()
    owner_comments: OwnerCommentSummary = field(default_factory=OwnerCommentSummary)
    warnings: tuple[str, ...] = ()
    indexed_by_fleet_manager: bool = True
    github_present: Optional[bool] = None
    visibility: str = "unknown"

    def __post_init__(self) -> None:
        if not isinstance(self.status, RepositoryStatus):
            try:
                status = RepositoryStatus(str(self.status))
            except ValueError:
                status = RepositoryStatus.UNKNOWN
            object.__setattr__(self, "status", status)
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "activities", tuple(self.activities))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    @property
    def url(self) -> str:
        return f"/repos/{quote(self.name, safe='')}"

    @property
    def status_label(self) -> str:
        return self.status.label

    @property
    def status_class(self) -> str:
        return self.status.css_class

    @property
    def purpose_text(self) -> str:
        return self.purpose or "Purpose not confidently established."

    @property
    def last_activity(self) -> Optional[Activity]:
        dated = [a for a in self.activities if a.occurred_at is not None]
        if dated:
            return max(dated, key=lambda activity: activity.occurred_at)
        return self.activities[0] if self.activities else None

    @property
    def last_activity_at(self) -> Optional[datetime]:
        return self.last_activity.occurred_at if self.last_activity else None

    @property
    def meaningful_activity(self) -> Optional[Activity]:
        routed = [
            activity
            for activity in self.activities
            if activity.kind != "github-push"
        ]
        in_flight = [
            activity for activity in routed if activity.kind == "in_flight"
        ]
        if in_flight:
            return in_flight[0]
        dated = [activity for activity in routed if activity.occurred_at]
        if dated:
            return max(dated, key=lambda activity: activity.occurred_at)
        return routed[0] if routed else None

    @property
    def displayed_activity(self) -> Optional[Activity]:
        return self.meaningful_activity or self.last_activity

    @property
    def displayed_activity_label(self) -> str:
        return (
            "last meaningful activity"
            if self.meaningful_activity is not None
            else "latest observed activity"
        )

    def is_recently_active(
        self,
        *,
        now: Optional[datetime] = None,
        within: timedelta = RECENT_ACTIVITY_WINDOW,
    ) -> bool:
        activity = self.last_activity
        if activity is None:
            return False
        return activity.is_recent(
            now=now or self.freshness.evaluated_at,
            within=within,
        )

    @property
    def recently_active(self) -> bool:
        return self.is_recently_active()

    @property
    def attention_reasons(self) -> tuple[str, ...]:
        reasons = list(self.warnings)
        if not self.indexed_by_fleet_manager:
            reasons.append("Present in GitHub; not yet indexed by Fleet Manager.")
        if self.github_present is False:
            reasons.append(
                "Not present in the anonymous public GitHub listing."
            )
        if self.status is RepositoryStatus.UNKNOWN:
            reasons.append("Repository state is unknown.")
        if self.freshness.state is FreshnessState.STALE:
            reasons.append("Repository summary is stale.")
        elif self.freshness.state is FreshnessState.UNAVAILABLE:
            reasons.append("Repository summary is unavailable.")
        elif self.freshness.state is FreshnessState.UNKNOWN:
            reasons.append("Repository summary freshness is unknown.")
        if self.owner_comments.has_unconsumed is True:
            reasons.append(self.owner_comments.label)
        return tuple(dict.fromkeys(reasons))

    @property
    def needs_attention(self) -> bool:
        return bool(self.attention_reasons)

    @property
    def signal_values(self) -> tuple[str, ...]:
        signals: list[str] = []
        if self.recently_active:
            signals.append("recently-active")
        if self.needs_attention:
            signals.append("needs-attention")
        if self.owner_comments.has_comments is True:
            signals.append("has-owner-comments")
        return tuple(signals)

    @property
    def search_text(self) -> str:
        return " ".join(
            part
            for part in (
                self.name,
                self.purpose,
                self.raw_status,
                " ".join(self.warnings),
            )
            if part
        )


@dataclass(frozen=True)
class RepositoryDetail:
    summary: RepositorySummary
    current_situation: str = ""
    current_situation_source: Optional[SourceReference] = None
    why_it_exists: str = ""
    recent_activity: tuple[Activity, ...] = ()
    important_sources: tuple[SourceReference, ...] = ()
    current_next_thread: Optional[str] = None
    current_next_thread_source: Optional[SourceReference] = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "recent_activity", tuple(self.recent_activity))
        object.__setattr__(self, "important_sources", tuple(self.important_sources))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    @property
    def name(self) -> str:
        return self.summary.name

    @property
    def current_next_thread_text(self) -> str:
        return (self.current_next_thread or "").strip() or NEXT_THREAD_UNKNOWN

    @property
    def all_sources(self) -> tuple[SourceReference, ...]:
        sources: list[SourceReference] = []
        seen: set[tuple[str, str]] = set()
        for source in (*self.summary.sources, *self.important_sources):
            key = (source.url, source.path)
            if key not in seen:
                sources.append(source)
                seen.add(key)
        return tuple(sources)


@dataclass(frozen=True)
class EstateOverview:
    repositories: tuple[RepositorySummary, ...] = ()
    sources: tuple[SourceReference, ...] = ()
    freshness: Freshness = field(default_factory=Freshness.unknown)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "repositories", tuple(self.repositories))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    @property
    def counts_by_status(self) -> dict[str, int]:
        counts = {status.value: 0 for status in RepositoryStatus}
        for repository in self.repositories:
            counts[repository.status.value] += 1
        return counts

    @property
    def attention_count(self) -> int:
        return sum(repository.needs_attention for repository in self.repositories)

    @property
    def recently_active_count(self) -> int:
        return sum(repository.recently_active for repository in self.repositories)

    def repository(self, name: str) -> Optional[RepositorySummary]:
        needle = name.casefold()
        return next(
            (repo for repo in self.repositories if repo.name.casefold() == needle),
            None,
        )


def _activity_timestamp(repository: RepositorySummary) -> float:
    value = repository.last_activity_at
    return value.timestamp() if value is not None else float("-inf")


def _attention_sort(repository: RepositorySummary) -> tuple[object, ...]:
    return (
        not repository.needs_attention,
        -_activity_timestamp(repository),
        repository.name.casefold(),
    )


def _recent_sort(repository: RepositorySummary) -> tuple[object, ...]:
    value = repository.last_activity_at
    return (
        value is None,
        -(value.timestamp() if value is not None else 0),
        repository.name.casefold(),
    )


_STATUS_SORT_ORDER = {
    RepositoryStatus.ACTIVE: 0,
    RepositoryStatus.INFRASTRUCTURE: 1,
    RepositoryStatus.PAUSED: 2,
    RepositoryStatus.FROZEN: 3,
    RepositoryStatus.ARCHIVED: 4,
    RepositoryStatus.UNKNOWN: 5,
}


REPOS_LIST_SPEC = listfilter.ListSpec(
    path="/repos",
    dimensions=(
        listfilter.Dimension(
            key="state",
            label="state",
            values=tuple(status.value for status in RepositoryStatus),
            labels={status.value: status.label for status in RepositoryStatus},
            get=lambda repository: [repository.status.value],
        ),
        listfilter.Dimension(
            key="signal",
            label="signal",
            values=(
                "recently-active",
                "needs-attention",
                "has-owner-comments",
            ),
            labels={
                "recently-active": "recently active",
                "needs-attention": "needs attention",
                "has-owner-comments": "has owner comments",
            },
            derived=True,
            get=lambda repository: repository.signal_values,
        ),
    ),
    sorts=(
        listfilter.SortOption(
            "attention", "needs attention", sort_key=_attention_sort
        ),
        listfilter.SortOption("recent", "recent activity", sort_key=_recent_sort),
        listfilter.SortOption(
            "az", "A-Z", sort_key=lambda repository: repository.name.casefold()
        ),
        listfilter.SortOption(
            "state",
            "state",
            sort_key=lambda repository: (
                _STATUS_SORT_ORDER[repository.status],
                repository.name.casefold(),
            ),
        ),
    ),
    search=lambda repository: repository.search_text,
)

# Explicit long name for discoverability; both names are the same object.
REPOSITORY_LIST_SPEC = REPOS_LIST_SPEC


def statuses(items: Iterable[RepositorySummary]) -> tuple[str, ...]:
    """Small serialization helper used by tests/readers without exposing Enum."""
    return tuple(item.status.value for item in items)
