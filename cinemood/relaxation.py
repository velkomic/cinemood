"""Bounded catalog probes and authenticated, explicit single-change selection."""

import secrets
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import psycopg
from pydantic import BaseModel, ConfigDict

from cinemood.catalog import candidate_summary, connect
from cinemood.config import Settings
from cinemood.constraints import Interpretation


class SelectionInvalid(Exception):
    pass


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request: str
    original: Interpretation
    field: str
    value: int | list[str] | None
    expires: int


class SelectionCapacityExceeded(Exception):
    pass


class SelectionStore:
    """Bounded per-app state; tokens reveal no request or interpretation text."""

    def __init__(self) -> None:
        self._pending: dict[str, Selection] = {}
        self._lock = threading.Lock()

    def _prune(self) -> None:
        now = time.time()
        self._pending = {
            token: item for token, item in self._pending.items() if item.expires > now
        }

    def issue(self, selections: list[Selection]) -> list[str]:
        with self._lock:
            self._prune()
            # Reserve the complete response atomically. Never evict a live option.
            if len(self._pending) + len(selections) > 128:
                raise SelectionCapacityExceeded
            tokens: list[str] = []
            for item in selections:
                token = secrets.token_urlsafe(32)
                while token in self._pending:
                    token = secrets.token_urlsafe(32)
                self._pending[token] = item.model_copy(deep=True)
                tokens.append(token)
            return tokens

    def get(self, token: str, request: str) -> Selection:
        with self._lock:
            self._prune()
            selection = self._pending.get(token)
            if selection is None or selection.request != request:
                raise SelectionInvalid
            return selection.model_copy(deep=True)


@dataclass(frozen=True)
class ConstraintChange:
    field: str
    value: int | list[str] | None


def changes(
    original: Interpretation,
    conn: psycopg.Connection[dict[str, Any]],
    settings: Settings,
) -> Iterator[ConstraintChange]:
    if original.runtime_minutes is not None:
        without_runtime = original.model_copy(
            update={"runtime_minutes": None, "runtime_operator": None}
        )
        shortest = candidate_summary(conn, settings, without_runtime).shortest_runtime
        if shortest is not None:
            limit = shortest + int(original.runtime_operator == "lt")
            if original.runtime_minutes < limit <= 1440:
                yield ConstraintChange("runtime_minutes", limit)
    if original.year_min is not None:
        without_min = original.model_copy(update={"year_min": None})
        year = candidate_summary(conn, settings, without_min).latest_year
        if year is not None and 1800 <= year < original.year_min:
            yield ConstraintChange("year_min", year)
    if original.year_max is not None:
        without_max = original.model_copy(update={"year_max": None})
        year = candidate_summary(conn, settings, without_max).earliest_year
        if year is not None and original.year_max < year <= 2200:
            yield ConstraintChange("year_max", year)
    if original.original_language is not None:
        yield ConstraintChange("original_language", None)
    for genre in sorted(original.included_genres):
        remaining = [g for g in original.included_genres if g != genre]
        yield ConstraintChange("included_genres", remaining)


def apply(original: Interpretation, change: ConstraintChange) -> Interpretation:
    return Interpretation.model_validate(
        {**original.model_dump(), change.field: change.value}
    )


def suggestions(
    request: str,
    original: Interpretation,
    settings: Settings,
    selections: SelectionStore,
) -> list[dict[str, object]]:
    offered: list[dict[str, object]] = []
    pending: list[Selection] = []
    seen: set[tuple[int, ...]] = set()
    with connect(settings) as conn:
        # Every boundary and count describes the same catalog snapshot.
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        for change in changes(original, conn, settings):
            revised = apply(original, change)
            candidates = candidate_summary(conn, settings, revised).movie_ids
            if not candidates or candidates in seen:
                continue
            seen.add(candidates)
            pending.append(
                Selection(
                    request=request,
                    original=original,
                    field=change.field,
                    value=change.value,
                    expires=int(time.time()) + 900,
                )
            )
            offered.append(
                {
                    "field": change.field,
                    "label": validate_and_describe_change(original, revised),
                    "candidate_count": len(candidates),
                    "interpretation": revised.model_dump(),
                }
            )
            if len(offered) == 3:
                break
    for option, token in zip(offered, selections.issue(pending), strict=True):
        option["selection"] = token
    return offered


def validate_and_describe_change(
    original: Interpretation, revised: Interpretation
) -> str:
    before, after = original.model_dump(), revised.model_dump()
    changed = [field for field in before if before[field] != after[field]]
    if len(changed) != 1:
        raise SelectionInvalid
    field = changed[0]
    # Validate a single broadening change; every other fact (including exclusions,
    # query and unchecked requirements) must remain identical.
    if field == "runtime_minutes":
        old, new = original.runtime_minutes, revised.runtime_minutes
        if old is None or new is None or new <= old:
            raise SelectionInvalid
        comparison = "under" if original.runtime_operator == "lt" else "at most"
        old_unit = "minute" if old == 1 else "minutes"
        new_unit = "minute" if new == 1 else "minutes"
        delta_unit = "minute" if new - old == 1 else "minutes"
        label = (
            f"Change runtime from {comparison} {old} {old_unit} "
            f"to {comparison} {new} {new_unit} (+{new - old} {delta_unit})"
        )
    elif field == "year_min":
        old, new = original.year_min, revised.year_min
        if old is None or new is None or new >= old:
            raise SelectionInvalid
        label = f"Change earliest year from {old} to {new} ({old - new} years earlier)"
    elif field == "year_max":
        old, new = original.year_max, revised.year_max
        if old is None or new is None or new <= old:
            raise SelectionInvalid
        label = f"Change latest year from {old} to {new} ({new - old} years later)"
    elif field == "original_language":
        if original.original_language is None or revised.original_language is not None:
            raise SelectionInvalid
        label = f"Change original language from {original.original_language} to any"
    elif field == "included_genres":
        removed = set(original.included_genres) - set(revised.included_genres)
        if len(removed) != 1 or revised.included_genres != [
            g for g in original.included_genres if g not in removed
        ]:
            raise SelectionInvalid
        label = (
            "Change required genres from "
            f"{', '.join(sorted(original.included_genres))} "
            f"to {', '.join(sorted(revised.included_genres)) or 'any'} "
            f"(remove {next(iter(removed))})"
        )
    else:
        raise SelectionInvalid
    return label


def select(
    token: str, request: str, selections: SelectionStore
) -> tuple[Interpretation, Interpretation, str]:
    selection = selections.get(token, request)
    revised = apply(
        selection.original, ConstraintChange(selection.field, selection.value)
    )
    label = validate_and_describe_change(selection.original, revised)
    return selection.original, revised, label
