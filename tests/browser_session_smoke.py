"""Public session controller in Chromium with controlled HTTP, no database/models."""

import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MOVIE = dict(json.loads((ROOT / "fixtures/movies.json").read_text())[0], id=1)
scenarios = {}
requests = []


def frame(event, sequence, **data):
    payload = dict(request_id="session-test", sequence=sequence, **data)
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def result(sequence=1, **data):
    return frame("result", sequence, movies=[MOVIE], message="Found a film.", **data)


class HTTP(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "cinemood/static"), **kwargs)

    def guess_type(self, path):
        if path.endswith(".js"):
            return "application/javascript; charset=utf-8"
        return super().guess_type(path)

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        requests.append(body)
        scenario = scenarios[body["request"]]
        self.send_response(scenario.get("status", 200))
        self.send_header("Content-Type", scenario.get("type", "text/event-stream"))
        self.end_headers()
        try:
            for chunk in scenario["chunks"]:
                if isinstance(chunk, threading.Event):
                    chunk.wait(10)
                else:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    if scenario.get("fragmented"):
                        time.sleep(0.002)
        except (BrokenPipeError, ConnectionResetError):
            pass


server = ThreadingHTTPServer(("127.0.0.1", 0), HTTP)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/style.css")
        page.add_script_tag(url=base + "/recommendation-session.js")
        page.evaluate("""() => {
            window.outcomes = [];
            window.session = createRecommendationSession(
                outcome => outcomes.push(outcome));
        }""")

        def run(name, stream, **options):
            chunks = [stream.encode()] if isinstance(stream, str) else stream
            scenarios[name] = dict(chunks=chunks, **options)
            page.evaluate("outcomes.length = 0")
            page.evaluate("name => session.start(name)", name)
            return page.evaluate("outcomes")

        outcomes = run(
            "valid",
            result()
            + frame("explanation_delta", 2, movie_id=1, text="Tentative")
            + frame("explanation_complete", 3, movie_id=1, text="Authoritative café 🌙")
            + frame("complete", 4),
        )
        assert [o["phase"] for o in outcomes if o["type"] == "explanation"] == [
            "tentative",
            "complete",
        ]
        assert outcomes[-1] == {"type": "busy", "busy": False}
        assert next(o for o in outcomes if o.get("phase") == "complete")["text"] == (
            "Authoritative café 🌙"
        )

        def final_status(items):
            return [o for o in items if o["type"] == "status"][-1]

        def rejected(name, stream):
            items = run(name, stream)
            assert not final_status(items)["quiet"], name
            assert final_status(items)["message"] != "Found a film.", name
            assert items[-1] == {"type": "busy", "busy": False}, name
            return items

        valid = result() + frame("complete", 2)
        fragmented = (
            result()
            + frame("explanation_delta", 2, movie_id=1, text="café 🌙")
            + frame("explanation_complete", 3, movie_id=1, text="Final café 🌙")
            + frame("complete", 4)
        ).encode()
        outcomes = run("fragmented", [bytes([b]) for b in fragmented], fragmented=True)
        assert next(o for o in outcomes if o.get("phase") == "complete")["text"] == (
            "Final café 🌙"
        )
        # This one HTTP body exceeds the limit but each frame is small.
        many = "".join(frame("status", n, stage="retrieval") for n in range(1, 1500))
        outcomes = run("many frames", many + result(1500) + frame("complete", 1501))
        assert final_status(outcomes)["quiet"]

        status_frame = frame("status", 1, stage="retrieval").rstrip("\n")
        # JSON accepts trailing whitespace. Exactly 65,536 JS characters, no delimiter.
        exact = status_frame + " " * (65536 - len(status_frame))
        outcomes = run(
            "exact frame",
            [exact.encode(), b"\n", b"\n", (result(2) + frame("complete", 3)).encode()],
            fragmented=True,
        )
        assert final_status(outcomes)["quiet"]
        for suffix in ("", "\n\n"):
            rejected("oversized" + repr(suffix), exact + " " + suffix)
        rejected("oversized split", [exact.encode(), b" ", b"\n", b"\n"])

        outcomes = run("terminal whitespace", valid + " \n\n\t\n")
        assert final_status(outcomes)["quiet"], outcomes

        invalid_streams = {
            "duplicate result": result() + result(2) + frame("complete", 3),
            "premature complete": frame("complete", 1),
            "unknown event": frame("unexpected", 1),
            "sequence starts at two": result(2),
            "fractional sequence": result(1.5),
            "string sequence": result("1"),
            "sequence gap": result() + frame("complete", 3),
            "missing request identity": result().replace('"session-test"', '""'),
            "nonstring identity": result().replace('"session-test"', "23"),
            "wrong request": result()
            + frame("complete", 2).replace("session-test", "other"),
            "unknown movie": result()
            + frame("explanation_delta", 2, movie_id=2, text="bad"),
            "string movie": result()
            + frame("explanation_delta", 2, movie_id="1", text="bad"),
            "before result": frame("explanation_delta", 1, movie_id=1, text="bad"),
            "bad text": result() + frame("explanation_delta", 2, movie_id=1, text=None),
            "bad message": frame("error", 1, message=[]),
            "bad stage": frame("status", 1, stage=None),
            "bad result": frame("result", 1, movies={}, message="bad"),
            "bad movie": frame(
                "result", 1, movies=[dict(MOVIE, genres=None)], message="bad"
            ),
            "bad interpretation": result(interpretation={}),
            "bad suggestions": result(suggestions=[{}]),
            "duplicate IDs": frame("result", 1, movies=[MOVIE, MOVIE], message="bad"),
            "after complete": valid + frame("status", 3, stage="retrieval"),
            "after error": frame("error", 1, message="Failed") + result(2),
            "trailing data": valid + "unexpected",
            "truncated frame": result() + "event: complete\ndata: {",
            "truncated EOF": result(),
            "empty EOF": "",
            "malformed JSON": "event: result\ndata: {oops}\n\n",
            "null JSON": "event: result\ndata: null\n\n",
            "bad UTF8": [result().encode(), b"\xff"],
            "truncated UTF8": [result().encode(), b"\xc3"],
        }
        for name, stream in invalid_streams.items():
            rejected(name, stream)

        for terminal_event in ("explanation_complete", "explanation_error"):
            for update in (
                "explanation_delta",
                "explanation_complete",
                "explanation_error",
            ):
                rejected(
                    terminal_event + " then " + update,
                    result()
                    + frame(
                        terminal_event,
                        2,
                        movie_id=1,
                        text="Final",
                        message="Unavailable",
                    )
                    + frame(update, 3, movie_id=1, text="Late", message="Late")
                    + frame("complete", 4),
                )

        two_movies = frame(
            "result", 1, movies=[MOVIE, dict(MOVIE, id=2)], message="Found a film."
        )
        partial = (
            two_movies
            + frame("explanation_complete", 2, movie_id=1, text="Keep this")
            + frame("explanation_delta", 3, movie_id=2, text="Discard this")
        )
        for ending in (
            "",
            frame("error", 4, message="Provider failed"),
            frame("result", 4, movies=[], message="Bad repeat"),
        ):
            outcomes = rejected("retention" + ending, partial + ending)
            assert len([o for o in outcomes if o["type"] == "result"]) == 1
            assert [o["phase"] for o in outcomes if o.get("movieId") == 1] == [
                "complete"
            ]
            assert [o["phase"] for o in outcomes if o.get("movieId") == 2] == [
                "tentative",
                "unavailable",
            ]
            assert [o for o in outcomes if o.get("movieId") == 2][-1]["text"] == ""
        outcomes = run("unfinished on complete", partial + frame("complete", 4))
        assert [o for o in outcomes if o.get("movieId") == 2][-1][
            "phase"
        ] == "unavailable"
        outcomes = run(
            "empty replacement",
            frame("result", 1, movies=[], message="No matches") + frame("complete", 2),
        )
        assert (
            next(o for o in outcomes if o["type"] == "result")["result"]["movies"] == []
        )
        assert final_status(outcomes) == {
            "type": "status",
            "message": "No matches",
            "quiet": False,
        }
        outcomes = run("early error", frame("error", 1, message="Search failed"))
        assert not any(o["type"] == "result" for o in outcomes)
        assert final_status(outcomes)["message"] == "Search failed"
        for code, body, expected in (
            (429, '{"detail":"Try later"}', "Try later"),
            (422, '{"detail":[]}', "Use a request of 1–2,000 characters."),
        ):
            outcomes = run(str(code), body, status=code, type="application/json")
            assert final_status(outcomes)["message"] == expected, outcomes
        outcomes = run("wrong content type", valid, type="text/html")
        assert final_status(outcomes)["message"] == "Invalid recommendation stream."
        page.route("**/api/recommendations/stream", lambda route: route.abort())
        page.evaluate("outcomes.length = 0; session.start('network')")
        assert (
            final_status(page.evaluate("outcomes"))["message"]
            == "Unable to connect. Please try again."
        )
        page.unroute("**/api/recommendations/stream")

        def held(name, prefix):
            gate = threading.Event()
            scenarios[name] = {"chunks": [prefix.encode(), gate]}
            page.evaluate("outcomes.length = 0")
            page.evaluate(
                """name => {
                    window.run = session.start(name, 'opaque-selection');
                }""",
                name,
            )
            page.wait_for_function("outcomes.some(o => o.type === 'result')")
            return gate

        gate = held("cancel", partial)
        count = len(requests)
        page.evaluate(
            "session.start('ignored'); session.cancel(); session.start('also ignored')"
        )
        page.evaluate("run")
        gate.set()
        assert len(requests) == count
        assert final_status(page.evaluate("outcomes"))["message"].startswith(
            "Search cancelled."
        )
        assert requests[-1]["selection"] == "opaque-selection"
        assert final_status(run("retry after cancel", valid))["quiet"]

        page.clock.install()
        gate = held("timeout", partial)
        page.clock.fast_forward(80001)
        page.evaluate("run")
        gate.set()
        assert (
            final_status(page.evaluate("outcomes"))["message"]
            == "Search took too long. Please try again."
        )
        assert final_status(run("retry after timeout", valid))["quiet"]
        # Cleared timeout must not publish a later outcome into a completed run.
        count = page.evaluate("outcomes.length")
        page.clock.fast_forward(80001)
        assert page.evaluate("outcomes.length") == count

        gate = held("dispose", partial)
        page.evaluate("session.dispose()")
        count = page.evaluate("outcomes.length")
        page.evaluate("run")
        gate.set()
        page.evaluate("session.start('disposed'); session.cancel(); session.dispose()")
        assert page.evaluate("outcomes.length") == count
        browser.close()
        print("Session controller browser checks passed")
finally:
    server.shutdown()
    server.server_close()
