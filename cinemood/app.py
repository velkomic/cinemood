from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StringConstraints

from cinemood.catalog import ROOT, connect, has_catalog, retrieve
from cinemood.config import Settings
from cinemood.embeddings import ProviderUnavailable, embed
from cinemood.http import RequestSizeLimit


class DiscoverRequest(BaseModel):
    request: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


def create_app() -> FastAPI:
    app = FastAPI(title="CineMood")
    settings = Settings.from_env()
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
            vector = embed([body.request], settings)[0]
            return {
                "movies": retrieve(settings, vector),
                "message": (
                    "Semantic matches from the local movie catalog. "
                    "Constraints are not checked yet."
                ),
            }
        except ProviderUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except psycopg.Error as exc:
            raise HTTPException(
                status_code=503, detail="Catalog unavailable. Try again later."
            ) from exc

    return app


app = create_app()
