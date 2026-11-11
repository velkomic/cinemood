import hashlib
import json

import psycopg
from fastapi.testclient import TestClient

from cinemood.app import create_app


def test_retained_poster_and_safe_fallback(
    loaded_client, database_url, monkeypatch, tmp_path
):
    monkeypatch.setenv("TMDB_SNAPSHOT_DIR", str(tmp_path))
    preview = loaded_client.get("/api/catalog-preview").json()["movies"]
    assert len(preview) == 4
    movie_id = preview[0]["id"]
    snapshot = {
        "provider": "tmdb",
        "endpoint": "/movie/42",
        "response": {"id": 42, "poster_path": "/RealPoster42.jpg"},
    }
    raw = json.dumps(snapshot).encode()
    key = f"tmdb/v1/{hashlib.sha256(raw).hexdigest()}.json"
    path = tmp_path / key
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "UPDATE movies SET source_id = 'tmdb:42', snapshot_key = %s WHERE id = %s",
            (key, movie_id),
        )
    with TestClient(create_app()) as client:
        response = client.get(f"/api/movies/{movie_id}/poster", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == (
            "https://image.tmdb.org/t/p/w500/RealPoster42.jpg"
        )
        assert (
            client.get(
                f"/api/movies/{movie_id}/poster?size=w342", follow_redirects=False
            )
            .headers["location"]
            .endswith("/w342/RealPoster42.jpg")
        )
        assert (
            client.get(f"/api/movies/{movie_id}/poster?size=original").status_code
            == 422
        )
        assert client.get("/api/movies/999999/poster").status_code == 404
        for bad in [
            {**snapshot, "response": {"id": 99, "poster_path": "/RealPoster42.jpg"}},
            {**snapshot, "response": {"id": 42, "poster_path": "//evil.test/file.jpg"}},
            {**snapshot, "response": {"id": 42, "poster_path": "/../file.jpg"}},
            {**snapshot, "response": []},
            [],
        ]:
            path.write_text(json.dumps(bad))
            assert client.get(f"/api/movies/{movie_id}/poster").status_code == 404
        path.write_text("{")
        assert client.get(f"/api/movies/{movie_id}/poster").status_code == 404
        path.unlink()
        assert client.get(f"/api/movies/{movie_id}/poster").status_code == 404
        with psycopg.connect(database_url) as conn:
            conn.execute(
                "UPDATE movies SET snapshot_key = '../../outside.json' WHERE id = %s",
                (movie_id,),
            )
        assert client.get(f"/api/movies/{movie_id}/poster").status_code == 404


def test_preview_is_bounded_catalog_data(client, database_url):
    with psycopg.connect(database_url) as conn:
        conn.execute(
            """INSERT INTO movies (source_id, title, overview, provenance,
                                   release_year, original_language, runtime_minutes)
               SELECT 'fixture:preview-' || n, 'Movie ' || n, 'Catalog overview',
                      'CC0 test', 2020, 'en', 90 FROM generate_series(1, 20) n"""
        )
    response = client.get("/api/catalog-preview")
    assert response.status_code == 200
    movies = response.json()["movies"]
    assert len(movies) == 5
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["has_more"] is True
    ids = [movie["id"] for movie in movies]
    refreshed = client.get(
        "/api/catalog-preview", params=[("exclude", id) for id in ids]
    )
    assert len(refreshed.json()["movies"]) == 5
    assert not set(ids) & {movie["id"] for movie in refreshed.json()["movies"]}
    assert (
        client.get("/api/catalog-preview", params=[("exclude", 1)] * 6).status_code
        == 422
    )
    assert client.get("/api/catalog-preview?exclude=-1").status_code == 422
    assert all(movie["genres"] == [] for movie in movies)
    assert all(movie["overview"] == "Catalog overview" for movie in movies)


def test_small_and_empty_spotlights(client, loaded_client):
    movies = loaded_client.get("/api/catalog-preview").json()["movies"]
    ids = [movie["id"] for movie in movies]
    again = loaded_client.get(
        "/api/catalog-preview", params=[("exclude", id) for id in ids]
    )
    assert {movie["id"] for movie in again.json()["movies"]} == set(ids)
    assert again.json()["has_more"] is False


def test_empty_spotlight(client):
    response = client.get("/api/catalog-preview")
    assert response.json() == {"movies": [], "has_more": False}
