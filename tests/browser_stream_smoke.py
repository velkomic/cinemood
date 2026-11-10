"""Manual deterministic browser seam: run with TEST_DATABASE_URL and Playwright."""

import json
import os
import threading
import time
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path

import psycopg
import uvicorn
from conftest import command
from playwright.sync_api import sync_playwright
from provider_stub import OpenAIHandler
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from cinemood.app import create_app

admin = os.environ["TEST_DATABASE_URL"]
database = "cinemood_browser_" + uuid.uuid4().hex
params = conninfo_to_dict(admin)
params["dbname"] = database
provider = ThreadingHTTPServer(("127.0.0.1", 0), OpenAIHandler)
threading.Thread(target=provider.serve_forever, daemon=True).start()
os.environ.update(
    DATABASE_URL=make_conninfo(**params),
    OPENAI_API_KEY="test-only",
    OPENAI_BASE_URL=f"http://127.0.0.1:{provider.server_port}/v1",
)
OpenAIHandler.explanations = {
    "quiet comfort": {
        "explanation": (
            'A café 🌙 <img src=x onerror="window.injected=true"> '
            "may fit because friends reconnect."
        ),
        "_delay": 0.01,
    },
    "invalid evidence": {"evidence": ["invented"]},
    "cancel me": {"_delay": 0.04},
}
OpenAIHandler.interpretations = {
    "under 1": {"runtime_minutes": 1, "runtime_operator": "lt"},
    "English or French drama": {
        "original_languages": ["en", "fr"],
        "included_genres": ["Drama"],
        "excluded_genres": ["Adventure"],
    },
}
with psycopg.connect(admin, autocommit=True) as conn:
    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
app = create_app()


async def fragmented(scope, receive, send):
    async def fragment(message):
        if (
            message["type"] == "http.response.body"
            and scope.get("path") == "/api/recommendations/stream"
        ):
            body = message.get("body", b"")
            # Split in the middle of JSON, event delimiters, and UTF-8 sequences.
            for index in range(0, len(body), 7):
                await send(
                    {
                        "type": "http.response.body",
                        "body": body[index : index + 7],
                        "more_body": True,
                    }
                )
            if not message.get("more_body", False):
                await send(
                    {"type": "http.response.body", "body": b"", "more_body": False}
                )
        else:
            await send(message)

    await app(scope, receive, fragment)


server = uvicorn.Server(
    uvicorn.Config(fragmented, host="127.0.0.1", port=58004, log_level="error")
)
thread = threading.Thread(target=server.run, daemon=True)
try:
    for action in [("migrate",), ("load-fixtures",)]:
        result = command(*action)
        assert result.returncode == 0, result.stderr
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.03)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:58004")

        def search(prompt):
            page.locator("#request").fill(prompt)
            page.get_by_role("button", name="Find movies").click()

        def finished():
            page.wait_for_function(
                "!document.querySelector('#discover button').disabled"
            )

        search("quiet comfort")
        page.locator("#results article").first.wait_for()
        assert (
            page.locator(".explanation-text").all_text_contents()
            != [OpenAIHandler.explanations["quiet comfort"]["explanation"]] * 3
        )
        finished()
        assert page.locator("#results article").count() == 3
        assert (
            page.locator(".explanation-text").all_text_contents()
            == [OpenAIHandler.explanations["quiet comfort"]["explanation"]] * 3
        )
        assert page.locator("#results img").count() == 0
        assert page.evaluate("window.injected === undefined")
        page.screenshot(path="/tmp/cinemood-stream-desktop.png", full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path="/tmp/cinemood-stream-mobile.png", full_page=True)
        search("invalid evidence")
        finished()
        assert page.locator(".explanation-text").all_text_contents() == ["", "", ""]
        assert all(
            "unavailable" in text
            for text in page.locator(".explanation").all_text_contents()
        )
        search("cancel me")
        page.get_by_text(
            "Generating explanation (not yet validated)…", exact=True
        ).first.wait_for()
        page.get_by_role("button", name="Cancel search").click()
        finished()
        assert page.locator("#results article").count() == 3
        assert page.locator(".explanation-text").all_text_contents() == ["", "", ""]
        assert "cancelled" in page.locator("#status").inner_text()
        search("under 1")
        finished()
        assert page.locator("#results article").count() == 0
        page.locator("#suggestions button").first.click()
        finished()
        assert page.locator("#request").input_value() == "under 1"
        assert page.locator("#results article").count() == 1
        assert page.locator("#results h2").inner_text() == "River Workshop"

        search("English or French drama")
        finished()
        assert (
            "Original languages (any): en or fr"
            in page.locator("#interpretation").inner_text()
        )
        assert page.locator("#results h2").all_text_contents() == [
            "The Lantern Kitchen",
            "Garden Letters",
        ]

        # EOF after provisional text must discard it, including when a frame
        # is incomplete. The fixture response is obtained through the API.
        def interrupt(route):
            response = route.fetch()
            body = response.text()
            cut = body.index("event: explanation_complete")
            route.fulfill(
                status=200,
                content_type="text/event-stream",
                body=body[:cut] + "event: comp",
            )

        page.route("**/api/recommendations/stream", interrupt)
        search("quiet comfort")
        finished()
        assert page.locator("#results article").count() == 3
        assert page.locator(".explanation-text").all_text_contents() == ["", "", ""]
        assert "interrupted" in page.locator("#status").inner_text()
        page.unroute("**/api/recommendations/stream")
        search("provider failure")
        finished()
        assert page.locator("#results article").count() == 0
        assert "provider" in page.locator("#status").inner_text().lower()
        assert not errors, errors
        Path("/tmp/cinemood-stream-browser.json").write_text(
            json.dumps({"passed": True, "javascript_errors": errors})
        )
        browser.close()
finally:
    server.should_exit = True
    if thread.is_alive():
        thread.join(timeout=10)
    provider.shutdown()
    provider.server_close()
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
        )
