"""Catalog-derived alternatives through the REST boundary, with real SQL."""

import psycopg
import pytest
from fastapi.testclient import TestClient

from cinemood.app import create_app


def test_runtime_suggestion_finds_the_nearest_catalog_boundary(
    loaded_client, extraction
):
    request = "A movie under 1 minute"
    extraction[request] = {"runtime_minutes": 1, "runtime_operator": "lt"}
    data = loaded_client.post("/api/recommendations", json={"request": request}).json()
    assert data["status"] == "no_match"
    assert data["movies"] == []
    assert len(data["suggestions"]) == 1
    suggestion = data["suggestions"][0]
    assert suggestion["field"] == "runtime_minutes"
    assert suggestion["interpretation"]["runtime_minutes"] == 89
    assert suggestion["interpretation"]["runtime_operator"] == "lt"
    assert suggestion["candidate_count"] == 1
    assert "under 1" in suggestion["label"]
    assert "under 89" in suggestion["label"]
    assert "88" in suggestion["label"]
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": request, "selection": suggestion["selection"]},
    ).json()
    assert [m["source_id"] for m in selected["movies"]] == ["fixture:river"]
    assert selected["original_interpretation"]["runtime_minutes"] == 1


@pytest.mark.parametrize(
    ("constraints", "field", "boundary", "expected"),
    [
        (
            {"runtime_minutes": 1, "runtime_operator": "lte"},
            "runtime_minutes",
            88,
            "fixture:river",
        ),
        (
            {
                "runtime_minutes": 1,
                "runtime_operator": "lt",
                "excluded_genres": ["Adventure"],
            },
            "runtime_minutes",
            93,
            "fixture:lantern",
        ),
        ({"year_min": 2100, "year_max": 2200}, "year_min", 2023, "fixture:river"),
        ({"year_min": 1800, "year_max": 1900}, "year_max", 2019, "fixture:garden"),
    ],
)
def test_nearest_boundary_keeps_other_restrictions(
    loaded_client, extraction, constraints, field, boundary, expected
):
    extraction["quiet comfort"] = constraints
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert len(data["suggestions"]) == 1
    option = data["suggestions"][0]
    assert option["field"] == field
    assert option["interpretation"][field] == boundary
    assert option["candidate_count"] == 1
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": "quiet comfort", "selection": option["selection"]},
    ).json()
    assert [m["source_id"] for m in selected["movies"]] == [expected]
    assert selected["interpretation"]["excluded_genres"] == constraints.get(
        "excluded_genres", []
    )


def test_independent_blockers_cannot_be_relaxed_together(loaded_client, extraction):
    extraction["quiet comfort"] = {
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "year_max": 1900,
    }
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert data["movies"] == []
    assert data["suggestions"] == []
    assert "single" in data["message"].lower()
    assert "edit" in data["message"].lower()


def test_selection_keeps_displayed_boundary_when_catalog_changes(
    loaded_client, extraction, database_url
):
    extraction["quiet comfort"] = {"runtime_minutes": 1, "runtime_operator": "lt"}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    option = data["suggestions"][0]
    assert option["interpretation"]["runtime_minutes"] == 89
    # A new shortest runtime would produce a different suggestion on a fresh search.
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "UPDATE movies SET runtime_minutes = 70 WHERE source_id = 'fixture:lantern'"
        )
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": "quiet comfort", "selection": option["selection"]},
    ).json()
    assert selected["interpretation"]["runtime_minutes"] == 89
    assert [m["source_id"] for m in selected["movies"]] == [
        "fixture:lantern",
        "fixture:river",
    ]


def test_stale_numeric_suggestion_does_not_substitute_a_new_boundary(
    loaded_client, extraction, database_url
):
    extraction["quiet comfort"] = {"runtime_minutes": 1, "runtime_operator": "lt"}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "UPDATE movies SET runtime_minutes = 120 WHERE source_id = 'fixture:river'"
        )
    selected = loaded_client.post(
        "/api/recommendations",
        json={
            "request": "quiet comfort",
            "selection": data["suggestions"][0]["selection"],
        },
    ).json()
    assert selected["movies"] == []
    assert selected["interpretation"]["runtime_minutes"] == 89
    assert selected["suggestions"] == []
    assert "no longer available" in selected["message"].lower()
    assert "search" in selected["message"].lower()


def test_options_are_distinct_stably_ordered_and_capped_at_three(
    loaded_client, extraction, database_url
):
    # Each movie violates exactly one different restriction.
    with psycopg.connect(database_url) as conn:
        conn.execute("UPDATE movies SET original_language = 'fr'")
        conn.execute("UPDATE movies SET runtime_minutes = 80")
        conn.execute(
            "UPDATE movies SET runtime_minutes = 100 "
            "WHERE source_id = 'fixture:lantern'"
        )
        conn.execute(
            "UPDATE movies SET release_year = 2021, original_language = 'en' "
            "WHERE source_id = 'fixture:orbital'"
        )
        conn.execute(
            "INSERT INTO movie_genres (movie_id, genre_id) "
            "SELECT m.id, g.id FROM movies m CROSS JOIN genres g "
            "WHERE m.source_id = 'fixture:orbital' AND g.name = 'Drama'"
        )
    extraction["quiet comfort"] = {
        "runtime_minutes": 90,
        "runtime_operator": "lte",
        "year_min": 2020,
        "year_max": 2022,
        "original_language": "fr",
        "included_genres": ["Drama"],
    }
    options = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()["suggestions"]
    assert [o["field"] for o in options] == ["runtime_minutes", "year_min", "year_max"]
    assert [o["interpretation"][o["field"]] for o in options] == [100, 2019, 2023]
    assert [o["candidate_count"] for o in options] == [1, 1, 1]
    results = []
    for option in options:
        selected = loaded_client.post(
            "/api/recommendations",
            json={"request": "quiet comfort", "selection": option["selection"]},
        ).json()
        results.append([m["source_id"] for m in selected["movies"]])
    assert results == [["fixture:lantern"], ["fixture:garden"], ["fixture:river"]]
    again = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()["suggestions"]
    assert [o["label"] for o in again] == [o["label"] for o in options]


def test_genre_alternatives_have_stable_order_and_distinct_candidate_sets(
    loaded_client, extraction
):
    labels = []
    for genres in (["Drama", "Comedy", "Adventure"], ["Adventure", "Drama", "Comedy"]):
        extraction["quiet comfort"] = {"included_genres": genres}
        options = loaded_client.post(
            "/api/recommendations", json={"request": "quiet comfort"}
        ).json()["suggestions"]
        assert len(options) == 2
        labels.append([o["label"] for o in options])
        assert options[0]["interpretation"]["included_genres"] == [
            g for g in genres if g != "Adventure"
        ]
        assert options[1]["interpretation"]["included_genres"] == [
            g for g in genres if g != "Comedy"
        ]
        matches = []
        for option in options:
            data = loaded_client.post(
                "/api/recommendations",
                json={"request": "quiet comfort", "selection": option["selection"]},
            ).json()
            matches.append([m["source_id"] for m in data["movies"]])
        assert matches == [["fixture:lantern"], ["fixture:river"]]
    assert labels[0] == labels[1]


@pytest.mark.parametrize("unusable", ["embedding", "genres"])
def test_unusable_metadata_or_embeddings_cannot_support_nearest_suggestions(
    loaded_client, extraction, database_url, unusable
):
    with psycopg.connect(database_url) as conn:
        if unusable == "embedding":
            conn.execute(
                "UPDATE movie_embeddings SET provider_fingerprint = 'incompatible' "
                "WHERE movie_id = (SELECT id FROM movies "
                "WHERE source_id = 'fixture:river')"
            )
        else:
            conn.execute(
                "DELETE FROM movie_genres WHERE movie_id = "
                "(SELECT id FROM movies WHERE source_id = 'fixture:river')"
            )
    extraction["quiet comfort"] = {
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "excluded_genres": ["Romance"],
    }
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert data["suggestions"][0]["interpretation"]["runtime_minutes"] == 93
    assert data["suggestions"][0]["candidate_count"] == 1


@pytest.mark.parametrize(("operator", "count"), [("lt", 0), ("lte", 1)])
def test_suggestions_respect_the_validated_runtime_domain(
    loaded_client, extraction, database_url, operator, count
):
    with psycopg.connect(database_url) as conn:
        conn.execute("UPDATE movies SET runtime_minutes = 1440")
    extraction["quiet comfort"] = {"runtime_minutes": 1, "runtime_operator": operator}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert len(data["suggestions"]) == count
    if count:
        assert data["suggestions"][0]["interpretation"]["runtime_minutes"] == 1440
        assert data["suggestions"][0]["candidate_count"] == 4


@pytest.mark.parametrize("catalog_change", ["empty", "incompatible"])
def test_selection_preserves_context_when_all_compatible_movies_disappear(
    loaded_client, extraction, database_url, catalog_change
):
    extraction["quiet comfort"] = {
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "excluded_genres": ["Romance"],
        "unsupported_requirements": ["Current Netflix availability"],
    }
    original = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    with psycopg.connect(database_url) as conn:
        if catalog_change == "empty":
            conn.execute("DELETE FROM movies")
        else:
            conn.execute(
                "UPDATE movie_embeddings SET provider_fingerprint = 'incompatible'"
            )
    selected = loaded_client.post(
        "/api/recommendations",
        json={
            "request": "quiet comfort",
            "selection": original["suggestions"][0]["selection"],
        },
    ).json()
    assert selected["status"] == "no_match"
    assert selected["movies"] == []
    assert selected["suggestions"] == []
    assert selected["original_request"] == "quiet comfort"
    assert selected["original_interpretation"] == original["interpretation"]
    assert selected["interpretation"]["runtime_minutes"] == 89
    assert selected["interpretation"]["excluded_genres"] == ["Romance"]
    assert selected["interpretation"]["unsupported_requirements"] == [
        "Current Netflix availability"
    ]
    assert "no longer available" in selected["message"].lower()
    assert "search again" in selected["message"].lower()


def test_displayed_alternative_remains_selectable_with_long_valid_interpretation(
    loaded_client, extraction
):
    request = "r" * 2000
    warnings = ["a" * 2000, "b" * 2000, "c" * 2000]
    extraction[request] = {
        "semantic_query": "s" * 2000,
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "unsupported_requirements": warnings,
    }
    original = loaded_client.post(
        "/api/recommendations", json={"request": request}
    ).json()
    option = original["suggestions"][0]
    response = loaded_client.post(
        "/api/recommendations",
        json={"request": request, "selection": option["selection"]},
    )
    assert response.status_code == 200
    selected = response.json()
    assert [m["source_id"] for m in selected["movies"]] == ["fixture:river"]
    assert selected["original_request"] == request
    assert selected["interpretation"]["unsupported_requirements"] == warnings
    assert selected["interpretation"]["runtime_minutes"] == 89


def test_selection_token_size_is_independent_of_unicode_request_and_warning_lengths(
    loaded_client, extraction
):
    request = "🎬" * 2000
    warnings = [f"Unknown fact {i}:".ljust(2000, "x") for i in range(10)]
    extraction[request] = {
        "semantic_query": "movie",
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "unsupported_requirements": warnings,
    }
    response = loaded_client.post("/api/recommendations", json={"request": request})
    assert response.status_code == 200
    option = response.json()["suggestions"][0]
    assert len(option["selection"]) == 43
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": request, "selection": option["selection"]},
    )
    assert selected.status_code == 200
    assert selected.json()["interpretation"]["unsupported_requirements"] == warnings
    assert [m["source_id"] for m in selected.json()["movies"]] == ["fixture:river"]


def test_pending_selection_capacity_is_atomic_and_preserves_displayed_options(
    loaded_client, extraction
):
    # The documented store limit is 128 pending displayed options for 15 minutes.
    extraction["quiet comfort"] = {"original_language": "de"}
    first_token = None
    for _ in range(127):
        response = loaded_client.post(
            "/api/recommendations", json={"request": "quiet comfort"}
        )
        assert response.status_code == 200
        if first_token is None:
            first_token = response.json()["suggestions"][0]["selection"]
    # Two genre alternatives need two slots; only one is available.
    extraction["both genres"] = {"included_genres": ["Drama", "Comedy", "Adventure"]}
    rejected = loaded_client.post(
        "/api/recommendations", json={"request": "both genres"}
    )
    assert rejected.status_code == 503
    assert "pending" in rejected.json()["detail"].lower()
    # Failed reservation did not consume the remaining slot.
    last = loaded_client.post("/api/recommendations", json={"request": "quiet comfort"})
    assert last.status_code == 200
    full = loaded_client.post("/api/recommendations", json={"request": "quiet comfort"})
    assert full.status_code == 503
    # Previously displayed alternatives are not evicted to make room.
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": "quiet comfort", "selection": first_token},
    )
    assert selected.status_code == 200
    assert len(selected.json()["movies"]) == 3


def test_selection_from_a_previous_app_instance_requires_a_new_search(
    loaded_client, extraction
):
    extraction["quiet comfort"] = {"original_language": "de"}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    with TestClient(create_app()) as restarted:
        response = restarted.post(
            "/api/recommendations",
            json={
                "request": "quiet comfort",
                "selection": data["suggestions"][0]["selection"],
            },
        )
    assert response.status_code == 400
    assert "search again" in response.json()["detail"].lower()
