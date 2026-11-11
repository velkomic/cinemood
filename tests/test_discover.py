import psycopg
import pytest
from fastapi.testclient import TestClient

from cinemood.app import create_app


def test_blank_request_is_rejected_before_provider_access():
    with TestClient(create_app()) as client:
        response = client.post("/api/recommendations", json={"request": "   "})
    assert response.status_code == 422
    assert "request" in response.text


def test_fixture_command_makes_catalog_cards_discoverable(loaded_client):
    response = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    )
    assert response.status_code == 200
    movies = response.json()["movies"]
    assert [movie["source_id"] for movie in movies] == [
        "fixture:lantern",
        "fixture:garden",
        "fixture:river",
        "fixture:orbital",
    ]
    assert movies[0] == {
        "id": movies[0]["id"],
        "source_id": "fixture:lantern",
        "title": "The Lantern Kitchen",
        "release_year": 2021,
        "genres": ["Comedy", "Drama"],
        "runtime_minutes": 92,
        "overview": (
            "A tired cook opens a tiny neighborhood kitchen. "
            "Shared meals and gentle humor help old friends reconnect."
        ),
    }
    assert isinstance(movies[0]["id"], int)


def test_large_http_body_is_rejected(client):
    response = client.post(
        "/api/recommendations",
        content=b" " * 20000,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


@pytest.mark.parametrize("prompt", ["", "\t\n", "x" * 2001, None, 42])
def test_invalid_requests_return_validation_errors(client, prompt):
    response = client.post("/api/recommendations", json={"request": prompt})
    assert response.status_code == 422


def test_empty_catalog_has_useful_outcome_without_provider(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with TestClient(create_app()) as fresh_client:
        response = fresh_client.post(
            "/api/recommendations", json={"request": "comfort"}
        )
    assert response.status_code == 200
    assert response.json()["movies"] == []
    assert "empty" in response.json()["message"]


def test_distinct_request_changes_vector_order(loaded_client):
    response = loaded_client.post(
        "/api/recommendations", json={"request": "space rescue"}
    )
    assert [m["source_id"] for m in response.json()["movies"]] == [
        "fixture:orbital",
        "fixture:river",
        "fixture:garden",
        "fixture:lantern",
    ]


@pytest.mark.parametrize(
    "prompt", ["provider failure", "invalid vector", "wrong dimensions"]
)
def test_provider_failures_never_claim_recommendations(loaded_client, prompt):
    response = loaded_client.post("/api/recommendations", json={"request": prompt})
    assert response.status_code == 503
    assert "provider" in response.json()["detail"].lower()
    assert "test-only" not in response.text
    assert "movies" not in response.json()


def test_unconfigured_provider_returns_useful_error(loaded_client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with TestClient(create_app()) as client:
        response = client.post("/api/recommendations", json={"request": "comfort"})
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_database_connection_failure_returns_safe_error(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid@127.0.0.1:1/missing")
    with TestClient(create_app()) as client:
        response = client.post("/api/recommendations", json={"request": "comfort"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Catalog unavailable. Try again later."}


def test_query_failure_returns_safe_error(loaded_client, database_url):
    with psycopg.connect(database_url) as conn:
        conn.execute("DROP TABLE movie_genres")
    response = loaded_client.post("/api/recommendations", json={"request": "comfort"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Catalog unavailable. Try again later."}


def test_sql_shaped_text_is_only_embedding_input(loaded_client):
    response = loaded_client.post(
        "/api/recommendations", json={"request": "'; DROP TABLE movies; --"}
    )
    assert response.status_code == 200
    again = loaded_client.post("/api/recommendations", json={"request": "comfort"})
    assert len(again.json()["movies"]) == 4


def test_equal_distances_use_stable_movie_ids(loaded_client):
    first = loaded_client.post(
        "/api/recommendations", json={"request": "equal distance"}
    ).json()
    second = loaded_client.post(
        "/api/recommendations", json={"request": "equal distance"}
    ).json()
    assert [m["source_id"] for m in first["movies"]] == [
        "fixture:lantern",
        "fixture:garden",
        "fixture:river",
        "fixture:orbital",
    ]
    assert second["movies"] == first["movies"]


def test_changed_provider_does_not_search_incompatible_vectors(
    loaded_client, monkeypatch, provider_url
):
    monkeypatch.setenv("OPENAI_BASE_URL", provider_url + "/alternate")
    with TestClient(create_app()) as client:
        response = client.post("/api/recommendations", json={"request": "comfort"})
    assert response.status_code == 200
    assert response.json()["movies"] == []


def test_five_recommendations_are_bounded_stable_and_streamed(
    loaded_client, database_url
):
    from test_streaming import events

    with psycopg.connect(database_url) as conn:
        for index in range(2):
            movie_id = conn.execute(
                """INSERT INTO movies (source_id, title, overview, release_year,
                    original_language, runtime_minutes, provenance)
                   SELECT %s, title, overview, release_year, original_language,
                          runtime_minutes, provenance FROM movies
                   ORDER BY id LIMIT 1 RETURNING id""",
                (f"fixture:extra-{index}",),
            ).fetchone()[0]
            conn.execute(
                """INSERT INTO movie_embeddings
                   (movie_id, model, provider_fingerprint, dimensions,
                    document_version, content_hash, embedding)
                   SELECT %s, model, provider_fingerprint, dimensions,
                          document_version, content_hash, embedding
                   FROM movie_embeddings ORDER BY movie_id LIMIT 1""",
                (movie_id,),
            )
    response = loaded_client.post(
        "/api/recommendations", json={"request": "equal distance"}
    )
    movies = response.json()["movies"]
    assert len(movies) == 5
    ids = [movie["id"] for movie in movies]
    assert len(set(ids)) == 5
    assert ids == sorted(ids)
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "equal distance"}
        )
    )
    assert [data["movies"] for name, data in stream if name == "result"] == [movies]
    assert [
        data["movie_id"] for name, data in stream if name == "explanation_complete"
    ] == ids
    assert not any(name == "explanation_error" for name, _ in stream)
    assert stream[-1][0] == "complete"
