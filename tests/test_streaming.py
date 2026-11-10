import json

import pytest


def events(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    result = []
    for frame in response.text.strip().split("\n\n"):
        name, payload = frame.split("\n", 1)
        result.append(
            (name.removeprefix("event: "), json.loads(payload.removeprefix("data: ")))
        )
    return result


def test_cards_precede_progressive_validated_explanations(loaded_client):
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "quiet comfort"}
        )
    )
    names = [name for name, _ in stream]
    assert names[0] == "status"
    assert names[-1] == "complete"
    assert names.index("result") < names.index("explanation_delta")
    cards = next(data["movies"] for name, data in stream if name == "result")
    assert [card["source_id"] for card in cards] == [
        "fixture:lantern",
        "fixture:garden",
        "fixture:river",
    ]
    completed = [data for name, data in stream if name == "explanation_complete"]
    assert [data["movie_id"] for data in completed] == [card["id"] for card in cards]
    for card, final in zip(cards, completed, strict=True):
        chunks = [
            data["text"]
            for name, data in stream
            if name == "explanation_delta" and data["movie_id"] == card["id"]
        ]
        assert len(chunks) >= 2
        assert "".join(chunks) == final["text"]
        expected_evidence = {
            "fixture:lantern": ["A tired cook opens a tiny neighborhood kitchen."],
            "fixture:garden": [
                "Two neighbors exchange letters across a shared garden, "
                "finding friendship and hope after years of loneliness."
            ],
            "fixture:river": [
                "An apprentice and a retired boat builder restore a river ferry, "
                "learning trust as they navigate an unexpected storm."
            ],
        }
        assert final["evidence"] == expected_evidence[card["source_id"]]
    assert [data["sequence"] for _, data in stream] == list(range(1, len(stream) + 1))
    assert len({data["request_id"] for _, data in stream}) == 1
    calls = stream[-1][1]["provider_calls"]
    assert [call["stage"] for call in calls] == [
        "interpretation",
        "query_embedding",
        "explanation",
        "explanation",
        "explanation",
    ]
    assert sum(call["tokens"]["total_tokens"] for call in calls) == 480
    timing = stream[-1][1]["timings_ms"]
    assert (
        0
        <= timing["first_status"]
        <= timing["first_movie"]
        <= timing["first_explanation"]
        <= timing["total"]
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"movie_id": 99999},
        {"evidence_refs": [0]},
        {"evidence_refs": [99999]},
        {"evidence_refs": ["1"]},
        {"evidence_refs": [True]},
        {"evidence_refs": []},
        {"evidence_refs": [1, 1, 1, 1]},
        {"evidence": ["Invented overview fact"]},
        {"evidence": ['"Invented overview fact"']},
        {"evidence": ['" "']},
        {"_finish": "length"},
        {"_finish": "content_filter"},
        {"_raw": '{"explanation":"Tentative incomplete text'},
        {"explanation": ""},
        {"explanation": "x" * 1300},
        {"_raw": "not json"},
        {"_http_status": 503},
    ],
)
def test_invalid_completed_explanation_keeps_cards(
    loaded_client, monkeypatch, overrides
):
    from provider_stub import OpenAIHandler

    monkeypatch.setattr(OpenAIHandler, "explanations", {"quiet comfort": overrides})
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "quiet comfort"}
        )
    )
    assert len(next(data["movies"] for name, data in stream if name == "result")) == 3
    assert len([name for name, _ in stream if name == "explanation_error"]) == 3
    assert not any(name == "explanation_complete" for name, _ in stream)
    assert stream[-1][0] == "complete"


@pytest.mark.parametrize(
    "prompt, override, expected",
    [
        ("contradiction", {"clarification": ["Which genre?"]}, "clarification"),
        ("too short", {"runtime_minutes": 1, "runtime_operator": "lt"}, "no_match"),
        ("bad extraction", {"_finish_reason": "length"}, "clarification"),
    ],
)
def test_nonmatch_streams_terminate_without_explanations(
    loaded_client, extraction, prompt, override, expected
):
    extraction[prompt] = override
    stream = events(
        loaded_client.post("/api/recommendations/stream", json={"request": prompt})
    )
    result = next(data for name, data in stream if name == "result")
    assert result["status"] == expected
    assert result["movies"] == []
    assert not any(name.startswith("explanation_") for name, _ in stream)
    assert stream[-1][1]["timings_ms"]["first_movie"] is None
    assert stream[-1][1]["timings_ms"]["first_explanation"] is None


def test_selected_stream_preserves_constraints_and_unchecked_warnings(
    loaded_client, extraction
):
    extraction["short Netflix"] = {
        "runtime_minutes": 1,
        "runtime_operator": "lt",
        "excluded_genres": ["Adventure"],
        "unsupported_requirements": ["Netflix availability"],
    }
    first = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "short Netflix"}
        )
    )
    result = next(data for name, data in first if name == "result")
    selected = events(
        loaded_client.post(
            "/api/recommendations/stream",
            json={
                "request": "short Netflix",
                "selection": result["suggestions"][0]["selection"],
            },
        )
    )
    result = next(data for name, data in selected if name == "result")
    assert [movie["source_id"] for movie in result["movies"]] == ["fixture:lantern"]
    assert result["interpretation"]["excluded_genres"] == ["Adventure"]
    assert result["interpretation"]["unsupported_requirements"] == [
        "Netflix availability"
    ]
    assert result["original_interpretation"]["runtime_minutes"] == 1
    assert selected[-1][0] == "complete"


def test_retrieval_provider_failure_is_terminal_without_cards(loaded_client):
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "provider failure"}
        )
    )
    assert stream[-1][0] == "error"
    assert not any(name == "result" for name, _ in stream)
    assert "test-only" not in json.dumps(stream)


@pytest.mark.parametrize(
    "payload, code",
    [
        ({"request": ""}, 422),
        ({"request": "x" * 2001}, 422),
        ({"request": "ok", "extra": True}, 422),
    ],
)
def test_stream_validates_before_admission(client, payload, code):
    assert client.post("/api/recommendations/stream", json=payload).status_code == code


def test_stream_empty_catalog_skips_generation(client):
    stream = events(
        client.post("/api/recommendations/stream", json={"request": "quiet"})
    )
    assert stream[-1][1]["status"] == "empty"
    assert not any(name.startswith("explanation_") for name, _ in stream)


@pytest.fixture
def live_url(loaded_client):
    import socket
    import threading
    import time

    import uvicorn

    from cinemood.app import create_app

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        server = uvicorn.Server(uvicorn.Config(create_app(), log_level="error"))
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        thread.start()
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.01)
        assert server.started
        try:
            yield url
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive()


def read_frames(response):
    frame = []
    for line in response.iter_lines():
        if not line:
            if frame:
                yield (
                    frame[0].removeprefix("event: "),
                    json.loads(frame[1].removeprefix("data: ")),
                )
                frame = []
        else:
            frame.append(line)


def test_network_cards_arrive_before_generation_and_disconnect_closes_provider(
    live_url, monkeypatch
):
    import time

    import httpx
    from provider_stub import OpenAIHandler

    monkeypatch.setattr(
        OpenAIHandler, "explanations", {"quiet comfort": {"_delay": 0.03}}
    )
    with httpx.stream(
        "POST",
        live_url + "/api/recommendations/stream",
        json={"request": "quiet comfort"},
        timeout=10,
    ) as response:
        received = []
        for name, data in read_frames(response):
            received.append(name)
            if name == "result":
                assert len(data["movies"]) == 3
                assert "explanation_delta" not in received
            if name == "explanation_delta":
                assert "explanation_complete" not in received
                break
    # Observe the external provider connection closing, rather than an internal task.
    for _ in range(100):
        if OpenAIHandler.active_streams == 0:
            break
        time.sleep(0.03)
    assert OpenAIHandler.active_streams == 0
    assert httpx.get(live_url + "/health").status_code == 200


def test_admission_is_bounded_and_cancelled_slots_are_reusable(
    live_url, monkeypatch, extraction
):
    import time
    from contextlib import ExitStack

    import httpx
    from provider_stub import OpenAIHandler

    monkeypatch.setattr(
        OpenAIHandler, "explanations", {"quiet comfort": {"_delay": 0.1}}
    )
    with ExitStack() as stack:
        readers = []
        for _ in range(4):
            response = stack.enter_context(
                httpx.stream(
                    "POST",
                    live_url + "/api/recommendations/stream",
                    json={"request": "quiet comfort"},
                    timeout=10,
                )
            )
            reader = read_frames(response)
            readers.append(reader)
            for name, _ in reader:
                if name == "explanation_delta":
                    break
        for route in ["/api/recommendations/stream", "/api/recommendations"]:
            response = httpx.post(live_url + route, json={"request": "quiet comfort"})
            assert response.status_code == 429
    extraction["empty restriction"] = {"runtime_minutes": 1, "runtime_operator": "lt"}
    for _ in range(100):
        response = httpx.post(
            live_url + "/api/recommendations/stream",
            json={"request": "empty restriction"},
        )
        if response.status_code != 429:
            break
        time.sleep(0.03)
    assert events(response)[-1][1]["status"] == "no_match"


def test_provider_timeout_discards_explanation_and_terminates(
    live_url, monkeypatch, extraction
):
    import httpx
    from provider_stub import OpenAIHandler

    extraction["timeout"] = {"included_genres": ["Science Fiction"]}
    monkeypatch.setattr(OpenAIHandler, "explanations", {"timeout": {"_delay": 16}})
    stream = events(
        httpx.post(
            live_url + "/api/recommendations/stream",
            json={"request": "timeout"},
            timeout=25,
        )
    )
    assert any(name == "result" for name, _ in stream)
    assert any(name == "explanation_error" for name, _ in stream)
    assert not any(name == "explanation_complete" for name, _ in stream)
    assert stream[-1][0] == "complete"


def test_failed_interpretation_accounting_is_explicit(loaded_client, extraction):
    extraction["truncated extraction"] = {"_finish_reason": "length"}
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "truncated extraction"}
        )
    )
    calls = stream[-1][1]["provider_calls"]
    assert len(calls) == 1
    assert calls[0]["stage"] == "interpretation"
    assert calls[0]["tokens"] is None


@pytest.mark.parametrize("disconnect_at", ["headers", "body"])
@pytest.mark.parametrize("spec_version", ["2.3", "2.4"])
def test_disconnected_response_does_not_leak_admission(
    loaded_client, disconnect_at, spec_version
):
    import asyncio

    from starlette.requests import ClientDisconnect

    from cinemood.app import create_app

    app = create_app()

    async def scenario():
        statuses = []
        body = json.dumps({"request": "quiet comfort"}).encode()
        for _ in range(6):
            delivered = False

            async def receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                await asyncio.Event().wait()

            async def send(message):
                if message["type"] == "http.response.start":
                    statuses.append(message["status"])
                    if disconnect_at == "headers":
                        raise OSError("client disconnected at headers")
                elif message["type"] == "http.response.body":
                    raise OSError("client disconnected during body")

            scope = {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": spec_version},
                "method": "POST",
                "path": "/api/recommendations/stream",
                "raw_path": b"/api/recommendations/stream",
                "query_string": b"",
                "headers": [(b"content-type", b"application/json")],
                "scheme": "http",
                "http_version": "1.1",
                "server": ("test", 80),
                "client": ("test", 123),
            }
            try:
                await app(scope, receive, send)
            except (ClientDisconnect, OSError):
                pass
        assert statuses == [200] * 6

    asyncio.run(scenario())


def test_numbered_catalog_evidence_completes_without_copying_quotes(
    loaded_client, extraction, monkeypatch
):
    from provider_stub import OpenAIHandler

    extraction["quiet comfort"] = {"included_genres": ["Comedy"]}
    monkeypatch.setattr(
        OpenAIHandler,
        "explanations",
        {
            "quiet comfort": {
                "_raw": json.dumps(
                    {
                        "movie_id": 1,
                        "explanation": (
                            "Shared meals and gentle humor help old friends reconnect."
                        ),
                        "evidence_refs": [1, 2],
                    }
                )
            }
        },
    )
    stream = events(
        loaded_client.post(
            "/api/recommendations/stream", json={"request": "quiet comfort"}
        )
    )
    completed = [data for name, data in stream if name == "explanation_complete"]
    assert len(completed) == 1
    assert completed[0]["evidence"] == [
        "A tired cook opens a tiny neighborhood kitchen.",
        "Shared meals and gentle humor help old friends reconnect.",
    ]
    assert not any(name == "explanation_error" for name, _ in stream)
