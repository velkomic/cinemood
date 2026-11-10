from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest
from fastapi.testclient import TestClient

from cinemood.app import create_app


def test_save_list_remove_is_isolated_and_idempotent(loaded_client, monkeypatch):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    movies = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()["movies"]
    movie = movies[0]
    path = f"/api/collection/{movie['id']}"
    headers = {"Origin": "http://testserver"}
    with TestClient(create_app()) as first, TestClient(create_app()) as second:
        assert first.get("/api/collection").json() == {"movies": []}
        assert second.get("/api/collection").json() == {"movies": []}
        assert first.put(path, headers=headers).status_code == 204
        assert first.put(path, headers=headers).status_code == 204
        assert first.get("/api/collection").json() == {"movies": [movie]}
        assert second.get("/api/collection").json() == {"movies": []}
        assert second.delete(path, headers=headers).status_code == 204
        assert first.get("/api/collection").json() == {"movies": [movie]}
        assert second.put(path, headers=headers).status_code == 204
        assert first.delete(path, headers=headers).status_code == 204
        assert first.get("/api/collection").json() == {"movies": []}
        assert second.get("/api/collection").json() == {"movies": [movie]}


def test_return_visit_after_app_restart_and_cookie_loss(loaded_client, monkeypatch):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    movie = loaded_client.post(
        "/api/recommendations", json={"request": "space rescue"}
    ).json()["movies"][0]
    with TestClient(create_app()) as visitor:
        assert (
            visitor.put(
                f"/api/collection/{movie['id']}",
                headers={"Origin": "http://testserver"},
            ).status_code
            == 204
        )
        cookies = dict(visitor.cookies)
    with TestClient(create_app()) as returning:
        returning.cookies.update(cookies)
        assert returning.get("/api/collection").json() == {"movies": [movie]}
        returning.cookies.clear()
        assert returning.get("/api/collection").json() == {"movies": []}


@pytest.mark.parametrize("method", ["put", "delete"])
@pytest.mark.parametrize(
    "origin", [None, "null", "https://evil.example", "http://testserver.evil"]
)
def test_mutations_require_exact_origin(client, monkeypatch, method, origin):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    with TestClient(create_app()) as visitor:
        headers = {} if origin is None else {"Origin": origin}
        response = getattr(visitor, method)("/api/collection/1", headers=headers)
        assert response.status_code == 403
        assert not visitor.cookies


@pytest.mark.parametrize(
    "movie_id", ["0", "-1", "9223372036854775808", "1;DROP TABLE movies", "unknown"]
)
def test_invalid_movie_ids_are_rejected(client, monkeypatch, movie_id):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    with TestClient(create_app()) as visitor:
        for method in [visitor.put, visitor.delete]:
            assert (
                method(
                    f"/api/collection/{movie_id}",
                    headers={"Origin": "http://testserver"},
                ).status_code
                == 422
            )


def test_unknown_movie_cannot_be_saved_or_create_catalog_data(client, monkeypatch):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    with TestClient(create_app()) as visitor:
        assert (
            visitor.put(
                "/api/collection/123456789", headers={"Origin": "http://testserver"}
            ).status_code
            == 404
        )
        assert visitor.get("/api/collection").json() == {"movies": []}
        assert (
            visitor.post("/api/recommendations", json={"request": "comfort"}).json()[
                "movies"
            ]
            == []
        )


def test_https_cookie_is_persistent_private_host_only_and_unforgeable(
    client, monkeypatch
):
    monkeypatch.setenv("COLLECTION_ORIGIN", "https://testserver")
    with TestClient(create_app(), base_url="https://testserver") as visitor:
        response = visitor.get("/api/collection")
        cookie = response.headers["set-cookie"]
        token = visitor.cookies["__Host-cinemood_collection"]
        assert len(token) == 43
        assert "HttpOnly" in cookie and "Secure" in cookie
        assert "SameSite=strict" in cookie and "Path=/" in cookie
        assert "Max-Age=31536000" in cookie and "Domain=" not in cookie
        assert response.headers["cache-control"] == "no-store"
        assert "set-cookie" not in visitor.get("/api/collection").headers
        assert visitor.cookies.get("__Host-cinemood_collection") == token
        visitor.cookies.clear()
        visitor.cookies.set(
            "__Host-cinemood_collection", "A" * 43, domain="testserver.local", path="/"
        )
        assert visitor.get("/api/collection").status_code == 200
        assert visitor.cookies["__Host-cinemood_collection"] != "A" * 43


def test_collection_database_error_is_safe(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid@127.0.0.1:1/missing")
    with TestClient(create_app()) as visitor:
        response = visitor.get("/api/collection")
        assert response.status_code == 503
        assert response.json() == {
            "detail": "Collection unavailable. Please try again."
        }
        assert not visitor.cookies


def test_cross_site_navigation_cannot_replace_collection_cookie(client):
    response = client.get("/api/collection", headers={"Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 403
    assert "set-cookie" not in response.headers


def test_concurrent_saves_converge_on_one_item(loaded_client, monkeypatch):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    movie = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()["movies"][0]
    app = create_app()
    with TestClient(app) as visitor:
        visitor.get("/api/collection")
        cookies = dict(visitor.cookies)

        def save(_):
            with TestClient(app) as parallel:
                parallel.cookies.update(cookies)
                return parallel.put(
                    f"/api/collection/{movie['id']}",
                    headers={"Origin": "http://testserver"},
                ).status_code

        with ThreadPoolExecutor(max_workers=4) as executor:
            assert list(executor.map(save, range(8))) == [204] * 8
        assert visitor.get("/api/collection").json() == {"movies": [movie]}


def test_catalog_removal_drops_saved_reference(
    loaded_client, database_url, monkeypatch
):
    monkeypatch.setenv("COLLECTION_ORIGIN", "http://testserver")
    monkeypatch.setenv("COLLECTION_ALLOW_HTTP", "true")
    movie = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()["movies"][0]
    with TestClient(create_app()) as visitor:
        assert (
            visitor.put(
                f"/api/collection/{movie['id']}",
                headers={"Origin": "http://testserver"},
            ).status_code
            == 204
        )
        # Arrange external catalog deletion; observe the FK cascade through REST.
        with psycopg.connect(database_url) as conn:
            conn.execute("DELETE FROM movies WHERE id = %s", (movie["id"],))
        assert visitor.get("/api/collection").json() == {"movies": []}
        assert (
            visitor.put(
                f"/api/collection/{movie['id']}",
                headers={"Origin": "http://testserver"},
            ).status_code
            == 404
        )
