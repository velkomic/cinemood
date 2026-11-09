"""Bounded catalog probes and authenticated, explicit single-change selection."""

import base64
import binascii
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cinemood.catalog import count_candidates
from cinemood.config import Settings
from cinemood.constraints import Interpretation


class SelectionInvalid(Exception):
    pass


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request: str
    original: Interpretation
    change_index: Annotated[int, Field(ge=0, le=23)]
    expires: int


@dataclass(frozen=True)
class ConstraintChange:
    field: str
    value: object
    label: str


def changes(original: Interpretation) -> list[ConstraintChange]:
    options: list[ConstraintChange] = []
    if original.runtime_minutes is not None:
        comparison = "under" if original.runtime_operator == "lt" else "at most"
        for increment in (15, 30):
            revised = min(original.runtime_minutes + increment, 1440)
            if revised > original.runtime_minutes:
                option = ConstraintChange(
                    "runtime_minutes",
                    revised,
                    f"Allow {comparison} {revised} minutes",
                )
                if option not in options:
                    options.append(option)
    if original.year_min is not None and original.year_min > 1800:
        year = max(1800, original.year_min - 10)
        options.append(
            ConstraintChange("year_min", year, f"Include release years from {year}")
        )
    if original.year_max is not None and original.year_max < 2200:
        year = min(2200, original.year_max + 10)
        options.append(
            ConstraintChange("year_max", year, f"Include release years through {year}")
        )
    if original.original_language is not None:
        options.append(
            ConstraintChange("original_language", None, "Allow any original language")
        )
    for genre in original.included_genres:
        remaining = [g for g in original.included_genres if g != genre]
        options.append(
            ConstraintChange(
                "included_genres", remaining, f"Stop requiring the genre {genre}"
            )
        )
    return options


def apply(original: Interpretation, change: ConstraintChange) -> Interpretation:
    return Interpretation.model_validate(
        {**original.model_dump(), change.field: change.value}
    )


def suggestions(
    request: str, original: Interpretation, settings: Settings, key: bytes
) -> list[dict[str, object]]:
    offered: list[dict[str, object]] = []
    # At most 24 fixed probes (19 genres + two runtime + two years + language).
    for index, change in enumerate(changes(original)):
        revised = apply(original, change)
        count = count_candidates(settings, revised)
        if not count:
            continue
        payload = (
            Selection(
                request=request,
                original=original,
                change_index=index,
                expires=int(time.time()) + 900,
            )
            .model_dump_json()
            .encode()
        )
        encoded = base64.urlsafe_b64encode(payload).decode()
        signature = hmac.new(key, encoded.encode(), hashlib.sha256).hexdigest()
        offered.append(
            {
                "field": change.field,
                "label": change.label,
                "candidate_count": count,
                "interpretation": revised.model_dump(),
                "selection": f"{encoded}.{signature}",
            }
        )
        if len(offered) == 3:
            break
    return offered


def select(
    token: str, request: str, key: bytes
) -> tuple[Interpretation, Interpretation, str]:
    try:
        encoded, signature = token.split(".")
        expected = hmac.new(key, encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature.encode(), expected.encode()):
            raise SelectionInvalid
        payload = base64.b64decode(encoded, altchars=b"-_", validate=True)
        selection = Selection.model_validate(json.loads(payload))
        if selection.request != request or selection.expires <= time.time():
            raise SelectionInvalid
        change = changes(selection.original)[selection.change_index]
        return selection.original, apply(selection.original, change), change.label
    except (ValueError, ValidationError, binascii.Error, IndexError) as exc:
        raise SelectionInvalid from exc
