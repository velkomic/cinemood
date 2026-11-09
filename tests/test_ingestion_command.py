"""Ingestion CLI + Discover, with fictional CC0 metadata over external HTTP."""

import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest
from conftest import command

OVERVIEW = (
    "A quiet cook opens a neighborhood kitchen where strangers become friends. "
    "Together they learn to share their hopes and build a welcoming home."
)


def movie(identity=101, **changes):
    return {
        "id": identity,
        "adult": False,
        "title": f"Test Kitchen {identity}",
        "overview": OVERVIEW,
        "release_date": "2020-02-29",
        "original_language": "fr",
        "runtime": 95,
        "vote_count": 400,
        "genres": [{"id": 35, "name": "Comedy"}],
        **changes,
    }


@pytest.fixture
def tmdb(monkeypatch, tmp_path):
    state = {
        "pages": {1: [101]},
        "details": {101: movie()},
        "calls": [],
        "errors": {},
        "blocked": threading.Event(),
        "release": threading.Event(),
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            state["calls"].append((url.path, query))
            if state.get("block") == url.path:
                state["blocked"].set()
                state["release"].wait(timeout=15)
            errors = state["errors"].get(url.path, [])
            if errors:
                code, retry_after = errors.pop(0)
                self.send_response(code)
                if retry_after is not None:
                    self.send_header("Retry-After", retry_after)
                self.end_headers()
                return
            if url.path.endswith("discover/movie"):
                page = int(query["page"][0])
                body = {
                    "page": page,
                    "total_pages": max(state["pages"]),
                    "results": [{"id": i} for i in state["pages"].get(page, [])],
                }
            else:
                identity = int(url.path.rsplit("/", 1)[1])
                body = state["details"][identity]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("TMDB_BASE_URL", f"http://127.0.0.1:{server.server_port}/3")
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-only")
    monkeypatch.setenv("TMDB_SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    state["snapshots"] = tmp_path / "snapshots"
    yield state
    state["release"].set()
    server.shutdown()
    server.server_close()
    thread.join()


def ingest(*args):
    return command("ingest-tmdb", "--target", "1", *args)


def test_import_is_searchable_bounded_and_keeps_raw_provenance(
    client, tmdb, monkeypatch
):
    result = ingest()
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "complete"
    assert report["accepted"] == 1
    assert report["embedded"] == 1
    cards = client.post("/api/recommendations", json={"request": "comfort"}).json()[
        "movies"
    ]
    assert [m["source_id"] for m in cards] == ["tmdb:101"]
    assert cards[0]["title"] == "Test Kitchen 101"
    assert cards[0]["genres"] == ["Comedy"]
    assert cards[0]["release_year"] == 2020
    assert cards[0]["runtime_minutes"] == 95
    path, query = tmdb["calls"][0]
    assert path == "/3/discover/movie"
    assert query == {
        "language": ["en-US"],
        "include_adult": ["false"],
        "sort_by": ["vote_count.desc"],
        "page": ["1"],
    }
    snapshots = [json.loads(p.read_text()) for p in tmdb["snapshots"].rglob("*.json")]
    assert len(snapshots) == 2
    assert any(s["response"] == movie() for s in snapshots)
    assert all(s["version"] == 1 and s["fetched_at"] for s in snapshots)
    assert "test-only" not in json.dumps(snapshots)
    tmdb["calls"].clear()
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.delenv("TMDB_READ_TOKEN")
    repeated = ingest()
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["requests"] == 0
    assert tmdb["calls"] == []


def test_interrupted_run_keeps_committed_movies_and_excludes_concurrent_run(
    client, tmdb
):
    tmdb["pages"] = {1: [101, 102]}
    tmdb["details"][102] = movie(102)
    tmdb["block"] = "/3/movie/102"
    process = subprocess.Popen(
        [sys.executable, "-m", "cinemood", "ingest-tmdb", "--target", "2"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert tmdb["blocked"].wait(10)
        cards = client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        assert [m["source_id"] for m in cards] == ["tmdb:101"]
        competing = ingest("--target", "2")
        assert competing.returncode == 1
        assert "active" in competing.stderr
        process.kill()
        process.communicate(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        tmdb["release"].set()
    tmdb["block"] = None
    # The remote first page changed during the interruption. Resume the saved page.
    tmdb["pages"] = {1: [999]}
    tmdb["calls"].clear()
    resumed = ingest("--target", "2")
    assert resumed.returncode == 0, resumed.stderr
    assert json.loads(resumed.stdout)["accepted"] == 1
    assert [p for p, _ in tmdb["calls"]] == ["/3/movie/102"]
    cards = client.post("/api/recommendations", json={"request": "comfort"}).json()[
        "movies"
    ]
    assert [m["source_id"] for m in cards] == ["tmdb:101", "tmdb:102"]


def test_invalid_records_and_reordered_duplicate_ids_do_not_fill_target(client, tmdb):
    tmdb["pages"] = {1: [101, 102, 101], 2: [102, 103, 104]}
    tmdb["details"].update(
        {102: movie(102, adult=True), 103: movie(103, overview=""), 104: movie(104)}
    )
    result = ingest("--target", "2")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert (
        report["accepted"],
        report["skipped"],
        report["duplicates"],
        report["embedded"],
    ) == (2, 3, 1, 2)
    cards = client.post("/api/recommendations", json={"request": "comfort"}).json()[
        "movies"
    ]
    assert [m["source_id"] for m in cards] == ["tmdb:101", "tmdb:104"]


@pytest.mark.parametrize(
    "changes",
    [
        {"runtime": None},
        {"runtime": True},
        {"release_date": "2020-02-30"},
        {"genres": []},
        {"genres": [None]},
        {"original_language": ""},
        {
            "overview": (
                "Une jeune femme ouvre une petite cuisine dans son quartier. "
                "Les voisins se rencontrent et partagent leurs histoires "
                "et leurs rêves dans cette maison chaleureuse."
            )
        },
        {"vote_count": -1},
        {"adult": "false"},
        {"id": 999},
    ],
)
def test_unusable_metadata_is_skipped_with_useful_incomplete_report(
    client, tmdb, changes
):
    tmdb["details"][101] = movie(**changes)
    result = ingest()
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "incomplete"
    assert report["reason"] == "source_exhausted"
    assert report["skipped"] == 1
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        == []
    )


@pytest.mark.parametrize("code", [429, 503])
def test_transient_errors_retry_without_skipping_movie(client, tmdb, code):
    tmdb["errors"]["/3/movie/101"] = [(code, "1")]
    started = time.monotonic()
    result = ingest()
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["requests"] == 3
    assert time.monotonic() - started >= 1
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ][0]["source_id"]
        == "tmdb:101"
    )


def test_request_budget_preserves_page_and_resumes_without_refetch(client, tmdb):
    result = ingest("--max-requests", "1")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["reason"] == "request_budget"
    tmdb["calls"].clear()
    result = ingest()
    assert result.returncode == 0, result.stderr
    assert [p for p, _ in tmdb["calls"]] == ["/3/movie/101"]


def test_page_budget_and_source_exhaustion_remain_bounded(client, tmdb):
    tmdb["pages"] = {1: [101], 2: [101, 102]}
    tmdb["details"][102] = movie(102)
    result = ingest("--target", "3", "--max-pages", "1")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["reason"] == "page_budget"
    result = ingest("--target", "3")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["total"] == 2
    assert report["reason"] == "source_exhausted"
    tmdb["calls"].clear()
    assert ingest("--target", "3").returncode == 0
    assert tmdb["calls"] == []


def test_duplicate_metadata_reuses_embedding_and_changed_content_keeps_identity(
    client, tmdb, monkeypatch
):
    tmdb["pages"] = {1: [101], 2: [101], 3: [101, 102]}
    tmdb["details"][102] = movie(102)
    first = ingest("--target", "2", "--max-pages", "1")
    assert first.returncode == 0, first.stderr
    original = client.post("/api/recommendations", json={"request": "comfort"}).json()[
        "movies"
    ][0]
    tmdb["details"][101]["vote_count"] = 500
    with monkeypatch.context() as env:
        env.delenv("OPENAI_API_KEY")
        unchanged = ingest("--target", "2", "--max-pages", "1")
    assert unchanged.returncode == 0, unchanged.stderr
    assert json.loads(unchanged.stdout)["embedded"] == 0
    assert json.loads(unchanged.stdout)["duplicates"] == 1
    tmdb["details"][101]["title"] = "Orbital Rescue"
    changed = ingest("--target", "2")
    assert changed.returncode == 0, changed.stderr
    assert json.loads(changed.stdout)["embedded"] == 2
    cards = client.post("/api/recommendations", json={"request": "space"}).json()[
        "movies"
    ]
    assert cards[0]["id"] == original["id"]
    assert cards[0]["title"] == "Orbital Rescue"
    assert [c["source_id"] for c in cards] == ["tmdb:101", "tmdb:102"]


def test_failed_embedding_resumes_saved_detail_without_additional_tmdb_fetch(
    client, tmdb, monkeypatch
):
    with monkeypatch.context() as env:
        env.delenv("OPENAI_API_KEY")
        failed = ingest()
    assert failed.returncode == 1
    assert "not configured" in failed.stderr
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        == []
    )
    tmdb["calls"].clear()
    resumed = ingest()
    assert resumed.returncode == 0, resumed.stderr
    assert json.loads(resumed.stdout)["accepted"] == 1
    assert tmdb["calls"] == []


def test_retry_limit_and_long_retry_after_preserve_position(client, tmdb):
    tmdb["errors"]["/3/movie/101"] = [(429, "60")]
    failed = ingest()
    assert failed.returncode == 1
    assert "resume later" in failed.stderr
    assert len(tmdb["calls"]) == 2
    tmdb["errors"]["/3/movie/101"] = [(503, None)] * 3
    failed = ingest()
    assert failed.returncode == 1
    assert "retry limit" in failed.stderr
    tmdb["calls"].clear()
    assert ingest().returncode == 0
    assert [p for p, _ in tmdb["calls"]] == ["/3/movie/101"]


def test_unwritable_snapshot_store_does_not_advance_checkpoint(
    client, tmdb, monkeypatch, tmp_path
):
    obstacle = tmp_path / "file"
    obstacle.write_text("not a directory")
    with monkeypatch.context() as env:
        env.setenv("TMDB_SNAPSHOT_DIR", str(obstacle))
        failed = ingest()
    assert failed.returncode == 1
    assert "Traceback" not in failed.stderr
    assert (
        client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "movies"
        ]
        == []
    )
    assert ingest().returncode == 0


@pytest.mark.parametrize(
    "args",
    [
        ("--target", "0"),
        ("--target", "1001"),
        ("--max-requests", "0"),
        ("--max-pages", "501"),
    ],
)
def test_unbounded_command_is_rejected(client, tmdb, args):
    result = ingest(*args)
    assert result.returncode == 2
    assert tmdb["calls"] == []


def test_catalog_copy_and_tmdb_credits_are_visible(client):
    html = client.get("/").text
    assert "This demo searches four fictional films" not in html
    assert (
        "This product uses the TMDB API but is not endorsed or certified by TMDB."
        in html
    )
    assert 'src="/static/tmdb-logo.svg"' in html
    assert "Credits" in html
    assert 'href="https://www.themoviedb.org"' in html
    assert (
        "fictional"
        not in client.post("/api/recommendations", json={"request": "comfort"}).json()[
            "message"
        ]
    )


def test_changed_embedding_provider_requires_reindex_without_tmdb_fetch(
    client, tmdb, monkeypatch, provider_url
):
    assert ingest().returncode == 0
    tmdb["calls"].clear()
    monkeypatch.setenv("OPENAI_BASE_URL", provider_url.replace("/v1", "/alternate"))
    # A restarted app now queries the new provider's embedding space.
    from fastapi.testclient import TestClient

    from cinemood.app import create_app

    with TestClient(create_app()) as restarted:
        assert (
            restarted.post("/api/recommendations", json={"request": "comfort"}).json()[
                "movies"
            ]
            == []
        )
        incompatible = ingest()
        assert incompatible.returncode == 1
        assert "--reindex" in incompatible.stderr
        repaired = ingest("--reindex")
        assert repaired.returncode == 0, repaired.stderr
        assert json.loads(repaired.stdout)["embedded"] == 1
        assert json.loads(repaired.stdout)["requests"] == 0
        assert (
            restarted.post("/api/recommendations", json={"request": "comfort"}).json()[
                "movies"
            ][0]["source_id"]
            == "tmdb:101"
        )
        monkeypatch.delenv("OPENAI_API_KEY")
        assert json.loads(ingest().stdout)["requests"] == 0
    assert tmdb["calls"] == []
