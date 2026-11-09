import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from cinemood.config import DIMENSIONS, DOCUMENT_VERSION, MODEL, Settings
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


def retrieve(settings: Settings, vector: list[float]) -> list[dict[str, Any]]:
    with connect(settings) as conn:
        rows = conn.execute(
            """
            WITH selected AS (
                SELECT m.id, m.source_id, m.title, m.release_year,
                       m.runtime_minutes, m.overview,
                       e.embedding <=> %s::vector AS distance
                FROM movies m JOIN movie_embeddings e ON e.movie_id = m.id
                WHERE e.model = %s AND e.dimensions = %s AND e.document_version = %s
                  AND e.provider_fingerprint = %s
                ORDER BY distance, m.id LIMIT 3
            )
            SELECT s.id, s.source_id, s.title, s.release_year,
                   s.runtime_minutes, s.overview,
                   COALESCE((SELECT array_agg(g.name ORDER BY g.name)
                             FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
                             WHERE mg.movie_id = s.id), ARRAY[]::text[]) AS genres
            FROM selected s ORDER BY s.distance, s.id
            """,
            (
                vector_literal(vector),
                MODEL,
                DIMENSIONS,
                DOCUMENT_VERSION,
                settings.provider_fingerprint,
            ),
        ).fetchall()
        return list(rows)
