"""Bounded initial TMDB acquisition, shared by manual commands and cron."""

import hashlib
import json
import os
import re
import time
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import psycopg
from langdetect import DetectorFactory, LangDetectException, detect_langs  # type: ignore[import-untyped]
from psycopg.types.json import Jsonb

from cinemood.catalog import connect
from cinemood.config import DIMENSIONS, DOCUMENT_VERSION, MODEL, Settings
from cinemood.embeddings import embed, vector_literal
from cinemood.snapshots import LocalSnapshotStore, SnapshotStore

DetectorFactory.seed = 0
CHECKPOINT = "tmdb-initial-v1"
LOCK = 74619302  # Shared with the fixture loader.


class IngestionError(Exception):
    pass


class BudgetReached(Exception):
    pass


class TMDB:
    def __init__(self, store: SnapshotStore, max_requests: int):
        self.base_url = os.getenv(
            "TMDB_BASE_URL", "https://api.themoviedb.org/3"
        ).rstrip("/")
        parsed = urlsplit(self.base_url)
        if (
            parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not parsed.hostname
            or (
                parsed.scheme != "https"
                and not (
                    parsed.scheme == "http"
                    and parsed.hostname in {"127.0.0.1", "localhost"}
                )
            )
        ):
            raise IngestionError(
                "Use HTTPS for TMDB (HTTP is allowed only on localhost)."
            )
        self.token = os.getenv("TMDB_READ_TOKEN", "")
        self.store = store
        self.max_requests = max_requests
        self.requests = 0
        self.last_request = 0.0

    def fetch(self, path: str, **params: Any) -> dict[str, Any]:
        if not self.token:
            raise IngestionError("TMDB_READ_TOKEN is not configured.")
        for attempt in range(3):
            if self.requests >= self.max_requests:
                raise BudgetReached
            time.sleep(max(0, 0.25 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.requests += 1
            try:
                response = httpx.get(
                    self.base_url + path,
                    params={"language": "en-US", **params},
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=15,
                    follow_redirects=False,
                )
            except httpx.RequestError:
                if attempt == 2:
                    raise IngestionError(
                        "TMDB connection failed; rerun to resume."
                    ) from None
                time.sleep(2**attempt)
                continue
            if response.status_code == 429 or response.status_code in {
                500,
                502,
                503,
                504,
            }:
                if attempt == 2:
                    raise IngestionError("TMDB retry limit reached; rerun to resume.")
                delay = float(2**attempt)
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        try:
                            delay = max(
                                delay,
                                (
                                    parsedate_to_datetime(retry_after)
                                    - datetime.now(UTC)
                                ).total_seconds(),
                            )
                        except (ValueError, TypeError, OverflowError):
                            raise IngestionError(
                                "TMDB sent invalid Retry-After."
                            ) from None
                if not 0 <= delay <= 30:
                    raise IngestionError(
                        "TMDB requests a long retry delay; resume later."
                    )
                time.sleep(delay)
                continue
            if response.status_code == 404 and path.startswith("/movie/"):
                body: Any = {"id": None, "missing": True}
            elif response.status_code != 200:
                raise IngestionError(f"TMDB returned HTTP {response.status_code}.")
            else:
                try:
                    body = response.json()
                except ValueError:
                    raise IngestionError("TMDB returned malformed JSON.") from None
            if not isinstance(body, dict):
                raise IngestionError("TMDB returned an invalid response.")
            snapshot = {
                "version": 1,
                "provider": "tmdb",
                "endpoint": path,
                "parameters": {"language": "en-US", **params},
                "origin": self.base_url,
                "fetched_at": datetime.now(UTC).isoformat(),
                "http_status": response.status_code,
                "response": body,
            }
            key = self.store.put(snapshot)
            return {
                "body": body,
                "snapshot_key": key,
                "fetched_at": snapshot["fetched_at"],
            }
        raise AssertionError("Retry loop exhausted")


def normalize(body: dict[str, Any], identity: int) -> dict[str, Any] | None:
    """Conservative usability rule; localization alone does not prove English."""
    try:
        if body["id"] != identity or body["adult"] is not False:
            return None
        title, overview = body["title"], body["overview"]
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 500:
            return None
        if not isinstance(overview, str) or not 40 <= len(overview.strip()) <= 10000:
            return None
        languages = detect_langs(overview)
        if languages[0].lang != "en" or languages[0].prob < 0.8:
            return None
        released = date.fromisoformat(body["release_date"])
        runtime, votes, language = (
            body["runtime"],
            body["vote_count"],
            body["original_language"],
        )
        if not 1800 <= released.year <= 2200:
            return None
        if type(runtime) is not int or runtime <= 0 or runtime > 1440:
            return None
        if type(votes) is not int or not 0 <= votes <= 2147483647:
            return None
        if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2}", language):
            return None
        genres = body["genres"]
        if not isinstance(genres, list) or not 1 <= len(genres) <= 30:
            return None
        if any(
            not isinstance(g, dict)
            or not isinstance(g.get("name"), str)
            or not 1 <= len(g["name"].strip()) <= 100
            for g in genres
        ):
            return None
        return {
            "source_id": f"tmdb:{identity}",
            "title": title.strip(),
            "overview": overview.strip(),
            "release_year": released.year,
            "release_date": released.isoformat(),
            "runtime_minutes": runtime,
            "original_language": language,
            "vote_count": votes,
            "genres": sorted({g["name"].strip() for g in genres}),
        }
    except (KeyError, ValueError, TypeError, LangDetectException):
        return None


def save_movie(
    conn: psycopg.Connection[dict[str, Any]],
    settings: Settings,
    movie: dict[str, Any],
    detail: dict[str, Any],
    origin: str,
) -> bool:
    # Acquisition counters and fetch times do not change the searchable document.
    document = json.dumps(
        {k: v for k, v in movie.items() if k not in {"vote_count", "release_date"}},
        sort_keys=True,
        ensure_ascii=False,
    )
    content_hash = hashlib.sha256(document.encode()).hexdigest()
    previous = conn.execute(
        """SELECT 1 FROM movies m JOIN movie_embeddings e ON e.movie_id = m.id
        WHERE m.source_id = %s AND e.content_hash = %s AND e.model = %s
        AND e.dimensions = %s AND e.document_version = %s
        AND e.provider_fingerprint = %s""",
        (
            movie["source_id"],
            content_hash,
            MODEL,
            DIMENSIONS,
            DOCUMENT_VERSION,
            settings.provider_fingerprint,
        ),
    ).fetchone()
    vector = None if previous else embed([document], settings)[0]
    row = conn.execute(
        """INSERT INTO movies (source_id, title, overview, release_year,
            original_language, runtime_minutes, provenance, release_date,
            vote_count, snapshot_key, fetched_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (source_id)
        DO UPDATE SET title = EXCLUDED.title, overview = EXCLUDED.overview,
            release_year = EXCLUDED.release_year,
            original_language = EXCLUDED.original_language,
            runtime_minutes = EXCLUDED.runtime_minutes,
            provenance = EXCLUDED.provenance,
            release_date = EXCLUDED.release_date, vote_count = EXCLUDED.vote_count,
            snapshot_key = EXCLUDED.snapshot_key, fetched_at = EXCLUDED.fetched_at
        RETURNING id""",
        (
            movie["source_id"],
            movie["title"],
            movie["overview"],
            movie["release_year"],
            movie["original_language"],
            movie["runtime_minutes"],
            origin,
            movie["release_date"],
            movie["vote_count"],
            detail["snapshot_key"],
            detail["fetched_at"],
        ),
    ).fetchone()
    assert row is not None
    movie_id = row["id"]
    conn.execute("DELETE FROM movie_genres WHERE movie_id = %s", (movie_id,))
    for genre in movie["genres"]:
        conn.execute(
            "INSERT INTO genres (name) VALUES (%s) ON CONFLICT DO NOTHING", (genre,)
        )
        conn.execute(
            """INSERT INTO movie_genres (movie_id, genre_id)
                        SELECT %s, id FROM genres WHERE name = %s""",
            (movie_id, genre),
        )
    if vector is not None:
        conn.execute(
            """INSERT INTO movie_embeddings
                (movie_id, model, dimensions, document_version,
                content_hash, embedding, provider_fingerprint)
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s) ON CONFLICT (movie_id)
            DO UPDATE SET model = EXCLUDED.model, dimensions = EXCLUDED.dimensions,
                document_version = EXCLUDED.document_version,
                content_hash = EXCLUDED.content_hash,
                embedding = EXCLUDED.embedding,
                provider_fingerprint = EXCLUDED.provider_fingerprint""",
            (
                movie_id,
                MODEL,
                DIMENSIONS,
                DOCUMENT_VERSION,
                content_hash,
                vector_literal(vector),
                settings.provider_fingerprint,
            ),
        )
    return vector is not None


def checkpoint(conn: psycopg.Connection[dict[str, Any]], state: dict[str, Any]) -> None:
    conn.execute(
        """INSERT INTO ingestion_checkpoints (name, state) VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET state = EXCLUDED.state, updated_at = now()""",
        (CHECKPOINT, Jsonb(state)),
    )


def ingest(
    settings: Settings, target: int, max_requests: int, max_pages: int
) -> dict[str, Any]:
    store = LocalSnapshotStore(Path(os.getenv("TMDB_SNAPSHOT_DIR", "var/snapshots")))
    source = TMDB(store, max_requests)
    report: dict[str, Any] = {
        "status": "incomplete",
        "accepted": 0,
        "skipped": 0,
        "embedded": 0,
        "duplicates": 0,
        "requests": 0,
        "pages": 0,
    }
    with connect(settings) as conn:
        conn.autocommit = True
        locked = conn.execute(
            "SELECT pg_try_advisory_lock(%s) AS locked", (LOCK,)
        ).fetchone()
        assert locked is not None
        if not locked["locked"]:
            raise IngestionError("Another catalog load is active; try again later.")
        row = conn.execute(
            "SELECT state FROM ingestion_checkpoints WHERE name = %s", (CHECKPOINT,)
        ).fetchone()
        state: dict[str, Any] = (
            row["state"] if row else {"page": 1, "index": 0, "origin": source.base_url}
        )
        if state["origin"] != source.base_url:
            raise IngestionError("TMDB origin differs from the saved checkpoint.")
        count_row = conn.execute(
            "SELECT count(*) AS total FROM movies WHERE source_id LIKE 'tmdb:%'"
        ).fetchone()
        assert count_row is not None
        total = count_row["total"]
        try:
            while total < target:
                if "batch" not in state:
                    if state.get("exhausted") or state["page"] > 500:
                        report["reason"] = "source_exhausted"
                        break
                    if report["pages"] >= max_pages:
                        report["reason"] = "page_budget"
                        break
                    fetched = source.fetch(
                        "/discover/movie",
                        page=state["page"],
                        sort_by="vote_count.desc",
                        include_adult="false",
                    )
                    body = fetched["body"]
                    if (
                        body.get("page") != state["page"]
                        or type(body.get("total_pages")) is not int
                        or not 0 <= body["total_pages"]
                        or not isinstance(body.get("results"), list)
                        or len(body["results"]) > 20
                    ):
                        raise IngestionError("TMDB returned an invalid discovery page.")
                    state.update(batch=body, index=0)
                    checkpoint(conn, state)
                    report["pages"] += 1
                batch = state["batch"]
                if state["index"] >= len(batch["results"]):
                    state["exhausted"] = (
                        state["page"] >= batch["total_pages"] or not batch["results"]
                    )
                    state["page"] += 1
                    state["index"] = 0
                    del state["batch"]
                    checkpoint(conn, state)
                    continue
                item = batch["results"][state["index"]]
                identity = item.get("id") if isinstance(item, dict) else None
                if type(identity) is not int or identity <= 0:
                    report["skipped"] += 1
                else:
                    if "detail" not in state:
                        state["detail"] = source.fetch(f"/movie/{identity}")
                        checkpoint(conn, state)
                    detail = state["detail"]
                    movie = normalize(detail["body"], identity)
                    if movie is None:
                        report["skipped"] += 1
                    else:
                        with conn.transaction():
                            existing = conn.execute(
                                "SELECT id FROM movies WHERE source_id = %s",
                                (movie["source_id"],),
                            ).fetchone()
                            embedded = save_movie(
                                conn, settings, movie, detail, source.base_url
                            )
                            state.pop("detail")
                            state["index"] += 1
                            checkpoint(conn, state)
                        report["embedded"] += int(embedded)
                        report["duplicates" if existing else "accepted"] += 1
                        total += int(not existing)
                        continue
                state.pop("detail", None)
                state["index"] += 1
                checkpoint(conn, state)
            if total >= target:
                report["status"] = "complete"
        except BudgetReached:
            report["reason"] = "request_budget"
        report.update(total=total, target=target, requests=source.requests)
        return report
