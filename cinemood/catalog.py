import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from cinemood.config import DIMENSIONS, DOCUMENT_VERSION, MODEL, Settings
from cinemood.constraints import Interpretation
from cinemood.embeddings import embed, vector_literal

ROOT = Path(__file__).resolve().parent.parent


def connect(settings: Settings) -> psycopg.Connection[dict[str, Any]]:
    return psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
        connect_timeout=3,
        options="-c statement_timeout=5000 -c lock_timeout=5000",
    )


def migrate(settings: Settings) -> None:
    with connect(settings) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(74619301)")
        conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version text PRIMARY KEY, checksum text NOT NULL)""")
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            script = path.read_text()
            checksum = hashlib.sha256(script.encode()).hexdigest()
            previous = conn.execute(
                "SELECT checksum FROM schema_migrations WHERE version = %s",
                (path.name,),
            ).fetchone()
            if previous:
                if previous["checksum"] != checksum:
                    raise ValueError("Applied migration was modified")
                continue
            conn.execute(script)
            conn.execute(
                "INSERT INTO schema_migrations VALUES (%s, %s)", (path.name, checksum)
            )


def load_fixtures(settings: Settings, limit: int) -> int:
    movies = json.loads((ROOT / "fixtures" / "movies.json").read_text())[:limit]
    with connect(settings) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(74619302)")
        pending = []
        for movie in movies:
            document = json.dumps(movie, sort_keys=True, ensure_ascii=False)
            content_hash = hashlib.sha256(document.encode()).hexdigest()
            previous = conn.execute(
                """
                SELECT 1 FROM movies m JOIN movie_embeddings e ON e.movie_id = m.id
                WHERE m.source_id = %s AND e.content_hash = %s AND e.model = %s
                  AND e.dimensions = %s AND e.document_version = %s
                  AND e.provider_fingerprint = %s
                """,
                (
                    movie["source_id"],
                    content_hash,
                    MODEL,
                    DIMENSIONS,
                    DOCUMENT_VERSION,
                    settings.provider_fingerprint,
                ),
            ).fetchone()
            if not previous:
                pending.append((movie, document, content_hash))
        if not pending:
            return 0
        vectors = embed([entry[1] for entry in pending], settings)
        for (movie, _, content_hash), vector in zip(pending, vectors, strict=True):
            row = conn.execute(
                """
                INSERT INTO movies (source_id, title, overview, release_year,
                    original_language, runtime_minutes, provenance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO UPDATE SET title = EXCLUDED.title,
                    overview = EXCLUDED.overview, release_year = EXCLUDED.release_year,
                    original_language = EXCLUDED.original_language,
                    runtime_minutes = EXCLUDED.runtime_minutes,
                    provenance = EXCLUDED.provenance, fetched_at = now()
                RETURNING id
                """,
                (
                    movie["source_id"],
                    movie["title"],
                    movie["overview"],
                    movie["release_year"],
                    movie["original_language"],
                    movie["runtime_minutes"],
                    "original-cc0-fixture-v1",
                ),
            ).fetchone()
            assert row is not None
            movie_id = row["id"]
            conn.execute("DELETE FROM movie_genres WHERE movie_id = %s", (movie_id,))
            for genre in movie["genres"]:
                conn.execute(
                    "INSERT INTO genres (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (genre,),
                )
                conn.execute(
                    """INSERT INTO movie_genres (movie_id, genre_id)
                    SELECT %s, id FROM genres WHERE name = %s""",
                    (movie_id, genre),
                )
            conn.execute(
                """
                INSERT INTO movie_embeddings
                    (movie_id, model, dimensions, document_version, content_hash,
                     embedding, provider_fingerprint)
                VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
                ON CONFLICT (movie_id) DO UPDATE SET model = EXCLUDED.model,
                    dimensions = EXCLUDED.dimensions,
                    provider_fingerprint = EXCLUDED.provider_fingerprint,
                    document_version = EXCLUDED.document_version,
                    content_hash = EXCLUDED.content_hash, embedding = EXCLUDED.embedding
                """,
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
        return len(pending)


def has_catalog(settings: Settings) -> bool:
    with connect(settings) as conn:
        return (
            conn.execute(
                """SELECT 1 FROM movie_embeddings
            WHERE model = %s AND dimensions = %s AND document_version = %s
              AND provider_fingerprint = %s LIMIT 1""",
                (MODEL, DIMENSIONS, DOCUMENT_VERSION, settings.provider_fingerprint),
            ).fetchone()
            is not None
        )


def eligible_filter(
    settings: Settings, constraints: Interpretation
) -> tuple[str, tuple[object, ...]]:
    # Only this fixed operator is interpolated; every visitor/model value is bound.
    runtime_operator = "<" if constraints.runtime_operator == "lt" else "<="
    predicate = f"""
        e.model = %s AND e.dimensions = %s AND e.document_version = %s
        AND e.provider_fingerprint = %s
        AND (%s::integer IS NULL OR m.runtime_minutes {runtime_operator} %s)
        AND (%s::integer IS NULL OR m.release_year >= %s)
        AND (%s::integer IS NULL OR m.release_year <= %s)
        AND (cardinality(%s::text[]) = 0 OR m.original_language = ANY(%s::text[]))
        AND NOT EXISTS (
            SELECT 1 FROM unnest(%s::text[]) wanted(name)
            WHERE NOT EXISTS (
                SELECT 1 FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
                WHERE mg.movie_id = m.id AND g.name = wanted.name))
        AND NOT EXISTS (
            SELECT 1 FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
            WHERE mg.movie_id = m.id AND g.name = ANY(%s::text[]))
        AND (%s::boolean = false OR EXISTS (
            SELECT 1 FROM movie_genres mg WHERE mg.movie_id = m.id))
    """
    return predicate, (
        MODEL,
        DIMENSIONS,
        DOCUMENT_VERSION,
        settings.provider_fingerprint,
        constraints.runtime_minutes,
        constraints.runtime_minutes,
        constraints.year_min,
        constraints.year_min,
        constraints.year_max,
        constraints.year_max,
        constraints.original_languages,
        constraints.original_languages,
        constraints.included_genres,
        constraints.excluded_genres,
        bool(constraints.included_genres or constraints.excluded_genres),
    )


def retrieve(
    settings: Settings, vector: list[float], constraints: Interpretation
) -> list[dict[str, Any]]:
    predicate, params = eligible_filter(settings, constraints)
    with connect(settings) as conn:
        rows = conn.execute(
            f"""
            WITH selected AS (
                SELECT m.id, m.source_id, m.title, m.release_year,
                       m.runtime_minutes, m.overview,
                       e.embedding <=> %s::vector AS distance
                FROM movies m JOIN movie_embeddings e ON e.movie_id = m.id
                WHERE {predicate}
                ORDER BY distance, m.id LIMIT 5
            )
            SELECT s.id, s.source_id, s.title, s.release_year,
                   s.runtime_minutes, s.overview,
                   COALESCE((SELECT array_agg(g.name ORDER BY g.name)
                             FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
                             WHERE mg.movie_id = s.id), ARRAY[]::text[]) AS genres
            FROM selected s ORDER BY s.distance, s.id
            """,
            (vector_literal(vector), *params),
        ).fetchall()
        return list(rows)


def count_candidates(settings: Settings, constraints: Interpretation) -> int:
    predicate, params = eligible_filter(settings, constraints)
    with connect(settings) as conn:
        row = conn.execute(
            f"""SELECT count(*) AS total FROM movies m
                JOIN movie_embeddings e ON e.movie_id = m.id WHERE {predicate}""",
            params,
        ).fetchone()
        assert row is not None
        return int(row["total"])


@dataclass(frozen=True)
class CandidateSummary:
    movie_ids: tuple[int, ...]
    shortest_runtime: int | None
    earliest_year: int | None
    latest_year: int | None


def candidate_summary(
    conn: psycopg.Connection[dict[str, Any]],
    settings: Settings,
    constraints: Interpretation,
) -> CandidateSummary:
    predicate, params = eligible_filter(settings, constraints)
    row = conn.execute(
        f"""SELECT COALESCE(array_agg(m.id ORDER BY m.id), ARRAY[]::bigint[]) AS ids,
                   min(m.runtime_minutes) AS shortest_runtime,
                   min(m.release_year) AS earliest_year,
                   max(m.release_year) AS latest_year
            FROM movies m JOIN movie_embeddings e ON e.movie_id = m.id
            WHERE {predicate}""",
        params,
    ).fetchone()
    assert row is not None
    return CandidateSummary(
        tuple(row["ids"]),
        row["shortest_runtime"],
        row["earliest_year"],
        row["latest_year"],
    )
