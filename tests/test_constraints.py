"""Constraint behavior through REST with real SQL and external HTTP fixtures."""

import psycopg
import pytest
from provider_stub import OpenAIHandler


def test_runtime_boundary_and_interpretation(loaded_client):
    response = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort under 92 minutes"}
    )
    assert response.status_code == 200
    data = response.json()
    assert [m["source_id"] for m in data["movies"]] == ["fixture:river"]
    assert data["interpretation"]["runtime_operator"] == "lt"
    assert data["interpretation"]["runtime_minutes"] == 92
    assert data["original_request"] == "quiet comfort under 92 minutes"


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        (
            {"runtime_minutes": 92, "runtime_operator": "lte"},
            ["fixture:lantern", "fixture:river"],
        ),
        ({"year_min": 2020, "year_max": 2021}, ["fixture:lantern", "fixture:orbital"]),
        ({"original_language": "fr"}, ["fixture:garden"]),
        ({"included_genres": ["Drama", "Adventure"]}, ["fixture:river"]),
        (
            {"included_genres": ["Drama"], "excluded_genres": ["Comedy"]},
            ["fixture:garden", "fixture:river"],
        ),
        ({"excluded_genres": ["Drama"]}, ["fixture:orbital"]),
    ],
)
def test_sql_filters_before_ranking(loaded_client, extraction, changes, expected):
    extraction["quiet comfort"] = changes
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert [m["source_id"] for m in data["movies"]] == expected
    for field, value in changes.items():
        assert data["interpretation"][field] == value


@pytest.mark.parametrize(
    "changes",
    [
        {"included_genres": ["Drama"], "excluded_genres": ["Drama"]},
        {"year_min": 2024, "year_max": 2020},
        {"runtime_minutes": 90},
        {"runtime_minutes": True, "runtime_operator": "lte"},
        {"runtime_minutes": 90, "runtime_operator": "gt"},
        {"included_genres": ["Drama'; DROP TABLE movies; --"]},
        {"original_language": "zz"},
        {"_omit": "excluded_genres"},
        {"_refusal": "Cannot interpret this request."},
        {"_content": "{broken"},
        {"_finish_reason": "length", "_content": "{truncated"},
        {"_finish_reason": "length"},
        {"_finish_reason": "content_filter"},
        {"clarification": ["Which decade do you mean?"]},
    ],
)
def test_invalid_or_ambiguous_requirements_stop_before_retrieval(
    loaded_client, extraction, changes
):
    extraction["uncertain request"] = changes
    data = loaded_client.post(
        "/api/recommendations", json={"request": "uncertain request"}
    ).json()
    assert data["status"] == "clarification"
    assert data["movies"] == []
    assert "edit" in data["message"].lower() or "clarif" in data["message"].lower()
    assert not any(p.endswith("embeddings") for p in OpenAIHandler.calls)


def test_no_match_offers_only_catalog_backed_single_changes(loaded_client, extraction):
    original = {
        "runtime_minutes": 90,
        "runtime_operator": "lt",
        "included_genres": ["Drama"],
        "excluded_genres": ["Adventure"],
        "original_language": "en",
        "unsupported_requirements": ["Current Netflix availability"],
    }
    extraction["gentle short drama"] = original
    data = loaded_client.post(
        "/api/recommendations", json={"request": "gentle short drama"}
    ).json()
    assert data["movies"] == []
    assert data["interpretation"]["runtime_minutes"] == 90
    assert 1 <= len(data["suggestions"]) <= 3
    assert not any(p.endswith("embeddings") for p in OpenAIHandler.calls)
    assert sum(p.endswith("chat/completions") for p in OpenAIHandler.calls) == 1
    for suggestion in data["suggestions"]:
        assert suggestion["candidate_count"] > 0
        revised = suggestion["interpretation"]
        changed = [
            key
            for key in data["interpretation"]
            if data["interpretation"][key] != revised[key]
        ]
        assert changed == [suggestion["field"]]
        assert revised["excluded_genres"] == ["Adventure"]
        selected = loaded_client.post(
            "/api/recommendations",
            json={
                "request": "gentle short drama",
                "selection": suggestion["selection"],
            },
        ).json()
        assert selected["original_request"] == "gentle short drama"
        assert selected["interpretation"] == revised
        assert selected["movies"]
        assert "not checked" in selected["message"].lower()
        assert selected["interpretation"]["unsupported_requirements"] == [
            "Current Netflix availability"
        ]
        assert all("Adventure" not in m["genres"] for m in selected["movies"])
    # Selection uses the server's prior interpretation, never re-extraction.
    assert sum(p.endswith("chat/completions") for p in OpenAIHandler.calls) == 1


@pytest.mark.parametrize(
    ("changes", "field", "count", "expected"),
    [
        (
            {"year_min": 2030, "year_max": 2040},
            "year_min",
            1,
            ["fixture:river"],
        ),
        (
            {"year_min": 1800, "year_max": 2010},
            "year_max",
            1,
            ["fixture:garden"],
        ),
        (
            {"original_language": "de"},
            "original_language",
            4,
            ["fixture:lantern", "fixture:garden", "fixture:river"],
        ),
        (
            {"included_genres": ["Horror", "Drama"]},
            "included_genres",
            3,
            ["fixture:lantern", "fixture:garden", "fixture:river"],
        ),
    ],
)
def test_each_relaxation_is_catalog_backed(
    loaded_client, extraction, changes, field, count, expected
):
    extraction["quiet comfort"] = changes
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert data["movies"] == []
    assert len(data["suggestions"]) == 1
    suggestion = data["suggestions"][0]
    assert suggestion["field"] == field
    assert suggestion["candidate_count"] == count
    selected = loaded_client.post(
        "/api/recommendations",
        json={"request": "quiet comfort", "selection": suggestion["selection"]},
    ).json()
    assert [m["source_id"] for m in selected["movies"]] == expected


def test_no_single_change_has_a_useful_empty_state(loaded_client, extraction):
    extraction["very short"] = {
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "year_max": 1900,
        "unsupported_requirements": ["Current Netflix availability"],
    }
    data = loaded_client.post(
        "/api/recommendations", json={"request": "very short"}
    ).json()
    assert data["movies"] == []
    assert data["suggestions"] == []
    assert data["interpretation"]["unsupported_requirements"] == [
        "Current Netflix availability"
    ]
    assert "edit" in data["message"].lower()
    assert len(OpenAIHandler.calls) == 1


def test_unknown_genres_do_not_satisfy_exclusions(
    loaded_client, extraction, database_url
):
    # Arrange incomplete metadata; all assertions remain at the REST boundary.
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "DELETE FROM movie_genres WHERE movie_id = "
            "(SELECT id FROM movies WHERE source_id = 'fixture:river')"
        )
    extraction["quiet comfort"] = {"excluded_genres": ["Comedy", "Romance"]}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert [m["source_id"] for m in data["movies"]] == ["fixture:orbital"]


@pytest.mark.parametrize("tamper", ["signature", "payload", "request", "unicode"])
def test_selection_cannot_apply_forged_or_unshown_changes(
    loaded_client, extraction, tamper
):
    extraction["quiet comfort"] = {"original_language": "de"}
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    token = data["suggestions"][0]["selection"]
    request = "quiet comfort"
    if tamper == "signature":
        token += "0"
    elif tamper == "payload":
        token = "A" + token[1:]
    elif tamper == "request":
        request = "a different request"
    else:
        token = token.rsplit(".", 1)[0] + ".é"
    response = loaded_client.post(
        "/api/recommendations", json={"request": request, "selection": token}
    )
    assert response.status_code == 400
    assert sum(p.endswith("chat/completions") for p in OpenAIHandler.calls) == 1
    assert not any(p.endswith("embeddings") for p in OpenAIHandler.calls)


def test_extraction_outage_is_safe_and_does_not_search(loaded_client, extraction):
    extraction["quiet comfort"] = {"_http_status": 503}
    response = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    )
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Interpretation provider is unavailable. Try again later."
    }
    assert len(OpenAIHandler.calls) == 1


def test_catalog_change_after_suggestion_returns_empty_without_broadening(
    loaded_client, extraction, database_url
):
    extraction["quiet comfort"] = {
        "included_genres": ["Horror", "Drama"],
        "excluded_genres": ["Adventure"],
    }
    data = loaded_client.post(
        "/api/recommendations", json={"request": "quiet comfort"}
    ).json()
    assert data["suggestions"][0]["candidate_count"] == 2
    # Previously eligible movies lose their genre metadata before selection.
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "DELETE FROM movie_genres WHERE movie_id IN "
            "(SELECT id FROM movies WHERE source_id IN "
            "('fixture:lantern', 'fixture:garden'))"
        )
    response = loaded_client.post(
        "/api/recommendations",
        json={
            "request": "quiet comfort",
            "selection": data["suggestions"][0]["selection"],
        },
    ).json()
    assert response["original_interpretation"]["included_genres"] == ["Horror", "Drama"]
    assert response["interpretation"]["included_genres"] == ["Drama"]
    assert response["interpretation"]["excluded_genres"] == ["Adventure"]
    assert response["movies"] == []
    assert response["suggestions"] == []
    assert sum(p.endswith("chat/completions") for p in OpenAIHandler.calls) == 1
    assert not any(p.endswith("embeddings") for p in OpenAIHandler.calls)


def test_unsupported_requirements_warn_without_dropping_supported_filters(
    loaded_client, extraction
):
    request = "A gentle movie on Netflix, in English, at most 90 minutes, no Comedy"
    extraction[request] = {
        "semantic_query": "quiet comfort",
        "original_language": "en",
        "runtime_minutes": 90,
        "runtime_operator": "lte",
        "excluded_genres": ["Comedy"],
        "unsupported_requirements": ["Current Netflix availability"],
    }
    response = loaded_client.post("/api/recommendations", json={"request": request})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "matches"
    assert [m["source_id"] for m in data["movies"]] == ["fixture:river"]
    assert data["interpretation"]["unsupported_requirements"] == [
        "Current Netflix availability"
    ]
    assert data["interpretation"]["clarification"] == []
    assert data["original_request"] == request
    assert "not checked" in data["message"].lower()
    assert sum(p.endswith("chat/completions") for p in OpenAIHandler.calls) == 1
    assert sum(p.endswith("embeddings") for p in OpenAIHandler.calls) == 1


def test_unsupported_only_request_returns_semantic_matches_with_warning(
    loaded_client, extraction
):
    request = "A tense orbital rescue currently available on Netflix"
    extraction[request] = {
        "semantic_query": "space rescue",
        "unsupported_requirements": ["Current Netflix availability"],
    }
    data = loaded_client.post("/api/recommendations", json={"request": request}).json()
    assert data["status"] == "matches"
    assert [m["source_id"] for m in data["movies"]] == [
        "fixture:orbital",
        "fixture:river",
        "fixture:garden",
    ]
    assert data["interpretation"]["unsupported_requirements"] == [
        "Current Netflix availability"
    ]
    assert "not checked" in data["message"].lower()


def test_unsupported_warning_does_not_bypass_supported_ambiguity(
    loaded_client, extraction
):
    request = "A short movie on Netflix, from that decade"
    extraction[request] = {
        "unsupported_requirements": ["Current Netflix availability"],
        "clarification": ["Which decade do you mean?"],
    }
    data = loaded_client.post("/api/recommendations", json={"request": request}).json()
    assert data["status"] == "clarification"
    assert data["movies"] == []
    assert data["interpretation"]["clarification"] == ["Which decade do you mean?"]
    assert data["interpretation"]["unsupported_requirements"] == [
        "Current Netflix availability"
    ]
    assert len(OpenAIHandler.calls) == 1
