import secrets
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, StringConstraints

from cinemood.catalog import ROOT, connect, count_candidates, has_catalog, retrieve
from cinemood.config import Settings
from cinemood.constraints import InterpretationInvalid, interpret
from cinemood.embeddings import ProviderUnavailable, embed
from cinemood.http import RequestSizeLimit
from cinemood.relaxation import SelectionInvalid, select, suggestions


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
    selection_key = secrets.token_bytes(32)
    app.add_middleware(RequestSizeLimit)

    app.mount(
        "/static", StaticFiles(directory=ROOT / "cinemood" / "static"), name="static"
    )

    @app.get("/")
    def discover_page() -> FileResponse:
        return FileResponse(ROOT / "cinemood" / "static" / "index.html")

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

    @app.post("/api/recommendations")
    def discover(body: DiscoverRequest) -> dict[str, object]:
        try:
            if not has_catalog(settings):
                return {
                    "movies": [],
                    "message": "The catalog is empty. Load the movie catalog first.",
                }
            applied_change = None
            if body.selection is not None:
                original, interpretation, applied_change = select(
                    body.selection, body.request, selection_key
                )
            else:
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
            if not count_candidates(settings, interpretation):
                offered = (
                    suggestions(body.request, original, settings, selection_key)
                    if body.selection is None
                    else []
                )
                return {
                    **common,
                    "movies": [],
                    "status": "no_match",
                    "suggestions": offered,
                    "message": (
                        "No movies meet these restrictions. Select an optional "
                        "change; counts show filter eligibility, not relevance."
                        if offered
                        else "No movies meet these restrictions and no bounded change "
                        "helps. Please edit your request."
                    ),
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

    return app


app = create_app()
