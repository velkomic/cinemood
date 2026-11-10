import hashlib
import os
import re
import secrets
from urllib.parse import urlsplit

import psycopg
from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import JSONResponse, Response

from cinemood.catalog import connect
from cinemood.config import Settings


def collection_router(settings: Settings) -> APIRouter:
    origin = os.getenv("COLLECTION_ORIGIN", "https://localhost")
    parsed = urlsplit(origin)
    secure = parsed.scheme == "https"
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or (not secure and os.getenv("COLLECTION_ALLOW_HTTP") != "true")
    ):
        raise ValueError(
            "COLLECTION_ORIGIN must be an exact HTTPS origin; "
            "local HTTP requires COLLECTION_ALLOW_HTTP=true."
        )
    cookie_name = "__Host-cinemood_collection" if secure else "cinemood_collection_dev"
    router = APIRouter()

    def operate(request: Request, movie_id: int | None = None) -> Response:
        # Strict cookies are withheld on cross-site navigation. Never overwrite
        # an existing browser identity just because that request omitted it.
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Open My collection from this site.")
        if request.method != "GET" and request.headers.get("origin") != origin:
            raise HTTPException(
                403, "Collection changes require the configured origin."
            )
        token = request.cookies.get(cookie_name, "")
        valid_token = re.fullmatch(r"[A-Za-z0-9_-]{43}", token) is not None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            with connect(settings) as conn:
                known = (
                    valid_token
                    and conn.execute(
                        "SELECT 1 FROM collections WHERE token_hash = %s", (token_hash,)
                    ).fetchone()
                )
                if not known:
                    token = secrets.token_urlsafe(32)
                    token_hash = hashlib.sha256(token.encode()).hexdigest()
                    conn.execute(
                        "INSERT INTO collections (token_hash) VALUES (%s)",
                        (token_hash,),
                    )
                if request.method == "PUT":
                    # Lock against catalog deletion until the FK-backed save commits.
                    # The composite primary key also handles concurrent saves.
                    if not conn.execute(
                        "SELECT 1 FROM movies WHERE id = %s FOR KEY SHARE", (movie_id,)
                    ).fetchone():
                        raise HTTPException(404, "Movie not found in the catalog.")
                    conn.execute(
                        """INSERT INTO collection_items (collection_hash, movie_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (token_hash, movie_id),
                    )
                elif request.method == "DELETE":
                    conn.execute(
                        """DELETE FROM collection_items
                           WHERE collection_hash = %s AND movie_id = %s""",
                        (token_hash, movie_id),
                    )
                else:
                    movies = conn.execute(
                        """SELECT m.id, m.source_id, m.title, m.release_year,
                                  m.runtime_minutes, m.overview,
                                  COALESCE((SELECT array_agg(g.name ORDER BY g.name)
                                    FROM movie_genres mg
                                    JOIN genres g ON g.id = mg.genre_id
                                    WHERE mg.movie_id = m.id),
                                    ARRAY[]::text[]) AS genres
                           FROM collection_items ci JOIN movies m ON m.id = ci.movie_id
                           WHERE ci.collection_hash = %s
                           ORDER BY ci.saved_at DESC, m.id""",
                        (token_hash,),
                    ).fetchall()
            response = (
                JSONResponse({"movies": movies})
                if request.method == "GET"
                else Response(status_code=204)
            )
            response.headers["Cache-Control"] = "no-store"
            if not known:
                response.set_cookie(
                    cookie_name,
                    token,
                    max_age=365 * 24 * 60 * 60,
                    httponly=True,
                    secure=secure,
                    samesite="strict",
                    path="/",
                )
            return response
        except psycopg.Error as exc:
            raise HTTPException(
                503, "Collection unavailable. Please try again."
            ) from exc

    @router.get("/api/collection")
    def list_movies(request: Request) -> Response:
        return operate(request)

    @router.put("/api/collection/{movie_id}", status_code=204)
    def save_movie(
        request: Request, movie_id: int = Path(gt=0, le=9223372036854775807)
    ) -> Response:
        return operate(request, movie_id)

    @router.delete("/api/collection/{movie_id}", status_code=204)
    def remove_movie(
        request: Request, movie_id: int = Path(gt=0, le=9223372036854775807)
    ) -> Response:
        return operate(request, movie_id)

    return router
