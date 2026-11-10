from collections.abc import Callable
from threading import BoundedSemaphore
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, StringConstraints

from cinemood.catalog import ROOT, connect, count_candidates, has_catalog, retrieve
from cinemood.collections import collection_router
from cinemood.config import Settings
from cinemood.constraints import InterpretationInvalid, interpret
from cinemood.embeddings import ProviderUnavailable, embed
from cinemood.http import RequestSizeLimit
from cinemood.relaxation import (
    SelectionCapacityExceeded,
    SelectionInvalid,
    SelectionStore,
    select,
    suggestions,
)
from cinemood.streaming import RecommendationResponse, recommendation_stream


class DiscoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selection: (
        Annotated[str, StringConstraints(min_length=1, max_length=12000)] | None
    ) = None

    request: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


def create_app() -> FastAPI:
    app = FastAPI(title="CineMood")
    settings = Settings.from_env()
    selections = SelectionStore()
    capacity = BoundedSemaphore(4)
    app.add_middleware(RequestSizeLimit)
    app.include_router(collection_router(settings))

    app.mount(
        "/static", StaticFiles(directory=ROOT / "cinemood" / "static"), name="static"
    )

    @app.get("/")
    def discover_page() -> FileResponse:
        return FileResponse(ROOT / "cinemood" / "static" / "index.html")

    @app.get("/collection")
    def collection_page() -> FileResponse:
        return FileResponse(ROOT / "cinemood" / "static" / "collection.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        try:
            with connect(settings) as conn:
                conn.execute("SELECT 1")
            return {"status": "ok"}
        except psycopg.Error as exc:
            raise HTTPException(
                status_code=503, detail="Database unavailable."
            ) from exc

    def search_catalog(
        body: DiscoverRequest, progress: Callable[[str], None]
    ) -> dict[str, object]:
        try:
            progress("interpretation")
            applied_change = None
            if body.selection is not None:
                original, interpretation, applied_change = select(
                    body.selection, body.request, selections
                )
            else:
                if not has_catalog(settings):
                    return {
                        "movies": [],
                        "message": (
                            "The catalog is empty. Load the movie catalog first."
                        ),
                    }
                interpretation = interpret(body.request, settings)
                original = interpretation
            if interpretation.clarification:
                return {
                    "movies": [],
                    "original_request": body.request,
                    "interpretation": interpretation.model_dump(),
                    "status": "clarification",
                    "message": "Please clarify or edit your request before searching.",
                }
            common = {
                "original_request": body.request,
                "original_interpretation": original.model_dump(),
                "interpretation": interpretation.model_dump(),
                "applied_change": applied_change,
            }
            progress("retrieval")
            if not count_candidates(settings, interpretation):
                offered = (
                    suggestions(body.request, original, settings, selections)
                    if body.selection is None
                    else []
                )
                if body.selection is not None:
                    message = (
                        "This displayed option is no longer available in the catalog. "
                        "Please search again."
                    )
                elif offered:
                    message = (
                        "No movies meet these restrictions. Select an optional "
                        "change; counts show filter eligibility, not relevance."
                    )
                else:
                    message = (
                        "No single-constraint change produces catalog matches. "
                        "Please edit your request."
                    )
                return {
                    **common,
                    "movies": [],
                    "status": "no_match",
                    "suggestions": offered,
                    "message": message,
                }
            vector = embed([interpretation.semantic_query], settings)[0]
            return {
                **common,
                "status": "matches",
                "suggestions": [],
                "movies": retrieve(settings, vector, interpretation),
                "message": (
                    "Movies match your supported restrictions. Some requirements were "
                    "not checked; see the warnings below."
                    if interpretation.unsupported_requirements
                    else "Semantic matches from the local movie catalog. "
                    "Supported constraints were checked."
                ),
            }
        except SelectionCapacityExceeded as exc:
            raise HTTPException(
                status_code=503,
                detail="Too many pending suggestions. Please try again later.",
            ) from exc
        except SelectionInvalid as exc:
            raise HTTPException(
                status_code=400,
                detail="This selection is invalid or expired. Search again.",
            ) from exc
        except InterpretationInvalid:
            return {
                "movies": [],
                "original_request": body.request,
                "message": (
                    "Please clarify or edit your request; "
                    "interpretation was incomplete or invalid."
                ),
                "status": "clarification",
            }
        except ProviderUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except psycopg.Error as exc:
            raise HTTPException(
                status_code=503, detail="Catalog unavailable. Try again later."
            ) from exc

    @app.post("/api/recommendations")
    def discover(body: DiscoverRequest) -> dict[str, object]:
        if not capacity.acquire(blocking=False):
            raise HTTPException(429, "Too many active searches. Try again later.")
        try:
            return search_catalog(body, lambda stage: None)
        finally:
            capacity.release()

    @app.post("/api/recommendations/stream")
    async def stream(body: DiscoverRequest) -> RecommendationResponse:
        if not capacity.acquire(blocking=False):
            raise HTTPException(429, "Too many active searches. Try again later.")
        return RecommendationResponse(
            recommendation_stream(
                lambda progress: search_catalog(body, progress), settings
            ),
            capacity,
        )

    return app


app = create_app()
