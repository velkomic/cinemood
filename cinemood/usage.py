"""Per-request provider accounting; no prompts or credentials are retained."""

from contextvars import ContextVar
from typing import Any

import httpx

provider_usage: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "provider_usage", default=None
)


def record(stage: str, model: str, usage: dict[str, Any] | None) -> None:
    calls = provider_usage.get()
    if calls is not None:
        calls.append({"stage": stage, "model": model, "tokens": usage})


def embedding_response(response: httpx.Response) -> None:
    if provider_usage.get() is None or response.status_code != 200:
        return
    response.read()
    body = response.json()
    raw = body.get("usage")
    record(
        "query_embedding",
        body.get("model", "text-embedding-3-small"),
        {
            "input_tokens": raw["prompt_tokens"],
            "output_tokens": 0,
            "total_tokens": raw["total_tokens"],
        }
        if raw
        else None,
    )
