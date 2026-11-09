import json

from conftest import command


def test_bounded_load_and_repeat_preserve_catalog_identities(client):
    first = command("load-fixtures", "--limit", "1")
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)["embedded"] == 1
    cards = client.post("/api/recommendations", json={"request": "comfort"}).json()[
        "movies"
    ]
    assert [m["source_id"] for m in cards] == ["fixture:lantern"]
    again = command("load-fixtures", "--limit", "1")
    assert again.returncode == 0, again.stderr
    assert json.loads(again.stdout)["embedded"] == 0
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        == cards
    )
    expanded = command("load-fixtures", "--limit", "4")
    assert expanded.returncode == 0, expanded.stderr
    assert json.loads(expanded.stdout)["embedded"] == 3
    assert (
        len(
            client.post("/api/recommendations", json={"request": "space"}).json()[
                "movies"
            ]
        )
        == 3
    )


def test_unchanged_catalog_does_not_need_provider(loaded_client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    result = command("load-fixtures")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["embedded"] == 0


def test_failed_load_leaves_empty_catalog_and_can_retry(client, monkeypatch):
    with monkeypatch.context() as env:
        env.delenv("OPENAI_API_KEY")
        result = command("load-fixtures")
    assert result.returncode == 1
    assert "not configured" in result.stderr
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        == []
    )
    retry = command("load-fixtures")
    assert retry.returncode == 0, retry.stderr
    assert (
        len(
            client.post("/api/recommendations", json={"request": "comfort"}).json()[
                "movies"
            ]
        )
        == 3
    )


def test_provider_connection_failure_is_a_command_error(client, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:1/v1")
    result = command("load-fixtures")
    assert result.returncode == 1
    assert "unavailable" in result.stderr
    assert "Traceback" not in result.stderr


def test_repeat_migration_preserves_discoverable_catalog(loaded_client):
    result = command("migrate")
    assert result.returncode == 0, result.stderr
    assert (
        len(
            loaded_client.post(
                "/api/recommendations", json={"request": "comfort"}
            ).json()["movies"]
        )
        == 3
    )


def test_fixture_load_rejects_unbounded_limit(client):
    result = command("load-fixtures", "--limit", "1000")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr
