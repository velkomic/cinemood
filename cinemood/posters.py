"""Display metadata from retained snapshots; no ingestion or model work."""

import json
import os
import re
from pathlib import Path
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi import Path as MovieId
from fastapi.responses import RedirectResponse

from cinemood.catalog import connect
from cinemood.config import Settings


def poster_router(settings: Settings) -> APIRouter:
    router = APIRouter()
    snapshots = Path(os.getenv("TMDB_SNAPSHOT_DIR", "var/snapshots")).resolve()

    @router.get("/api/catalog-preview")
    def preview(
        response: Response,
        exclude: Annotated[list[int] | None, Query(max_length=5)] = None,
    ) -> dict[str, object]:
        exclude = exclude or []
        if any(identity <= 0 or identity > 9223372036854775807 for identity in exclude):
            raise HTTPException(422, "Invalid catalog identity.")
        response.headers["Cache-Control"] = "no-store"
        try:
            with connect(settings) as conn:
                movies = conn.execute(
                    """SELECT m.id, m.source_id, m.title, m.release_year,
                              m.runtime_minutes, m.overview,
                              count(*) OVER() AS catalog_size,
                              COALESCE((SELECT array_agg(g.name ORDER BY g.name)
                                FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
                                WHERE mg.movie_id = m.id), ARRAY[]::text[]) AS genres
                       FROM movies m
                       ORDER BY (m.id = ANY(%s::bigint[])), random() LIMIT 5""",
                    (exclude,),
                ).fetchall()
            total = movies[0]["catalog_size"] if movies else 0
            for movie in movies:
                del movie["catalog_size"]
            return {"movies": movies, "has_more": total > 5}
        except psycopg.Error as exc:
            raise HTTPException(503, "Catalog preview unavailable.") from exc

    @router.get("/api/movies/{movie_id}/poster")
    def poster(
        movie_id: int = MovieId(gt=0, le=9223372036854775807),
        size: Literal["w342", "w500"] = "w500",
    ) -> RedirectResponse:
        try:
            with connect(settings) as conn:
                movie = conn.execute(
                    "SELECT source_id, snapshot_key FROM movies WHERE id = %s",
                    (movie_id,),
                ).fetchone()
        except psycopg.Error as exc:
            raise HTTPException(503, "Poster unavailable.") from exc
        if not movie or not re.fullmatch(
            r"tmdb/v1/[a-f0-9]{64}\.json", movie["snapshot_key"] or ""
        ):
            raise HTTPException(404, "No poster available.")
        try:
            path = (snapshots / movie["snapshot_key"]).resolve()
            if not path.is_relative_to(snapshots):
                raise ValueError("Invalid snapshot path")
            with path.open("rb") as stream:
                raw = stream.read(512_001)
            if len(raw) > 512_000:
                raise ValueError("Oversized snapshot")
            snapshot = json.loads(raw)
            if not isinstance(snapshot, dict):
                raise ValueError("Invalid snapshot")
            body = snapshot["response"]
            if not isinstance(body, dict):
                raise ValueError("Invalid movie details")
            if (
                snapshot["provider"] != "tmdb"
                or movie["source_id"] != f"tmdb:{body['id']}"
                or snapshot["endpoint"] != f"/movie/{body['id']}"
            ):
                raise ValueError("Snapshot identity mismatch")
            poster_path = body.get("poster_path")
            if not isinstance(poster_path, str) or not re.fullmatch(
                r"/[A-Za-z0-9]{1,100}\.(?:jpg|png)", poster_path
            ):
                raise ValueError("Invalid image path")
        except (OSError, ValueError, KeyError, TypeError):
            raise HTTPException(404, "No poster available.") from None
        return RedirectResponse(
            f"https://image.tmdb.org/t/p/{size}{poster_path}",
            status_code=307,
            headers={"Cache-Control": "public, max-age=3600"},
        )

    return router
