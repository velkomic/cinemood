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
    COLLECTION_ORIGIN="http://127.0.0.1:58004",
    COLLECTION_ALLOW_HTTP="true",
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

        # Two initial tabs must share one identity even if the second response
        # arrives after the first tab has saved. Capture real requests so that
        # an initially absent Cookie header cannot be silently repaired later.
        tabs = browser.new_context()
        pending = []
        tabs.route("**/api/collection", lambda route: pending.append(route))
        first_tab = tabs.new_page()
        second_tab = tabs.new_page()
        first_tab.goto(
            "http://127.0.0.1:58004/collection", wait_until="domcontentloaded"
        )
        second_tab.goto(
            "http://127.0.0.1:58004/collection", wait_until="domcontentloaded"
        )
        for _ in range(100):
            if pending:
                break
            first_tab.wait_for_timeout(20)
        assert pending
        initial = pending[0].fetch()
        pending[0].fulfill(response=initial)
        first_tab.get_by_text("Your collection is empty.", exact=False).wait_for()
        for _ in range(100):
            if len(pending) == 2:
                break
            first_tab.wait_for_timeout(20)
        assert len(pending) == 2
        movie = tabs.request.post(
            "http://127.0.0.1:58004/api/recommendations",
            data={"request": "quiet comfort"},
        ).json()["movies"][0]
        assert (
            first_tab.evaluate(
                "async id => (await fetch(`/api/collection/${id}`, "
                "{method: 'PUT'})).status",
                movie["id"],
            )
            == 204
        )
        delayed = pending[1].fetch(
            headers={
                **pending[1].request.all_headers(),
                "cookie": pending[1].request.header_value("cookie") or "",
            }
        )
        pending[1].fulfill(response=delayed)
        second_tab.locator("#collection-results[aria-busy=false]").wait_for(
            state="attached"
        )
        tabs.unroute("**/api/collection")
        first_tab.reload()
        first_tab.locator("#collection-results[aria-busy=false]").wait_for(
            state="attached"
        )
        assert first_tab.locator("#collection-results article").count() == 1
        assert (
            first_tab.locator("#collection-results h2").inner_text() == movie["title"]
        )
        tabs.close()

        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:58004")
        page.locator(".preview-film").first.wait_for()
        assert (
            page.locator(".preview-track").evaluate(
                "(el) => getComputedStyle(el).animationName"
            )
            == "drift"
        )
        page.locator("#request").focus()
        assert (
            page.locator(".preview-track").evaluate(
                "(el) => getComputedStyle(el).animationPlayState"
            )
            == "paused"
        )
        page.emulate_media(reduced_motion="reduce")
        assert (
            page.locator(".preview-track").evaluate(
                "(el) => getComputedStyle(el).animationName"
            )
            == "none"
        )
        page.emulate_media(reduced_motion="no-preference")
        preview_opener = page.locator("#preview-track .poster-button").first
        preview_opener.focus()
        page.keyboard.press("Enter")
        assert page.locator(".preview-film.is-expanded .movie-details").is_visible()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.locator(".preview-film.is-expanded .movie-details").is_visible()
        assert page.locator("dialog").count() == 0
        page.keyboard.press("Escape")
        assert preview_opener.evaluate("(el) => el === document.activeElement")
        page.set_viewport_size({"width": 1280, "height": 1000})
        page.locator("#request").fill("quiet comfort")
        page.locator("#request").press("Shift+Enter")
        assert page.locator("#request").input_value() == "quiet comfort\n"
        assert not page.locator("#discover button").first.is_disabled()

        def search(prompt):
            page.locator("#request").fill(prompt)
            page.locator("#request").press("Enter")

        def finished():
            page.wait_for_function(
                "!document.querySelector('#discover button').disabled"
            )

        search("quiet comfort")
        page.locator("#results article").first.wait_for()
        assert (
            page.locator(".explanation-text").all_text_contents()
            != [OpenAIHandler.explanations["quiet comfort"]["explanation"]] * 4
        )
        finished()
        assert page.locator("#results article").count() == 4
        assert (
            page.locator(".explanation-text").all_text_contents()
            == [OpenAIHandler.explanations["quiet comfort"]["explanation"]] * 4
        )
        assert page.locator("#results img[src=x]").count() == 0
        assert page.evaluate("window.injected === undefined")

        # Details expand only the selected card without moving adjacent columns.
        first_details = page.locator("#results .details-action").first
        neighbor_x = page.locator("#results article").nth(1).bounding_box()["x"]
        first_details.click()
        assert page.locator("#results article.is-expanded").count() == 1
        assert (
            page.locator("#results article")
            .first.locator(".movie-details")
            .is_visible()
        )
        assert page.locator("#results article").nth(1).bounding_box()["x"] == neighbor_x
        page.locator("#results .details-action").nth(1).click()
        assert (
            not page.locator("#results article")
            .first.locator(".movie-details")
            .is_visible()
        )
        assert (
            "Two neighbors exchange letters"
            in page.locator("#results article.is-expanded .synopsis").inner_text()
        )
        assert page.locator("#results article").count() == 4
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path="/tmp/cinemood-details-desktop.png", full_page=True)
        page.keyboard.press("Escape")
        assert page.locator("#results article.is-expanded").count() == 0
        assert (
            page.locator("#results .details-action")
            .nth(1)
            .evaluate("(el) => el === document.activeElement")
        )

        # A pending replacement keeps usable cards and their interpreted context.
        held = []
        page.route("**/api/recommendations/stream", lambda route: held.append(route))
        original_cards = page.locator("#results h2").all_text_contents()
        search("replacement pending")
        page.wait_for_function('document.querySelector("#cancel").hidden === false')
        assert page.locator("#results h2").all_text_contents() == original_cards
        page.locator(".request-context summary").click()
        assert "quiet comfort" in page.locator("#interpretation").inner_text()
        page.locator(".request-context summary").click()
        page.get_by_role("button", name="Cancel search").click()
        finished()
        for route in held:
            route.abort()
        page.unroute("**/api/recommendations/stream")
        assert page.locator("#results h2").all_text_contents() == original_cards
        page.get_by_role("button", name="Save to collection", exact=True).first.click()
        page.get_by_role("button", name="Saved to collection", exact=True).wait_for()
        page.get_by_role("link", name="My collection", exact=True).click()
        page.locator("#collection-results article").wait_for()
        assert (
            page.locator("#collection-results h2").inner_text() == "The Lantern Kitchen"
        )
        page.reload()
        page.locator("#collection-results article").wait_for()
        assert "1 saved movie" in page.locator("#collection-status").inner_text()
        page.screenshot(path="/tmp/cinemood-collection-desktop.png", full_page=True)
        other = browser.new_context()
        other_page = other.new_page()
        other_page.goto("http://127.0.0.1:58004/collection")
        other_page.get_by_text("Your collection is empty.", exact=False).wait_for()
        assert other_page.locator("#collection-results article").count() == 0
        other.close()

        def unavailable(route):
            route.fulfill(
                status=503,
                content_type="application/json",
                body='{"detail":"Collection unavailable. Please try again."}',
            )

        page.route("**/api/collection/*", unavailable)
        page.get_by_role("button", name="Remove", exact=True).click()
        page.get_by_text(
            "Collection unavailable. Please try again.", exact=True
        ).wait_for()
        assert page.locator("#collection-results article").count() == 1
        page.unroute("**/api/collection/*")
        page.get_by_role("button", name="Remove", exact=True).click()
        page.get_by_text("Your collection is empty.", exact=False).wait_for()
        page.route("**/api/collection", unavailable)
        page.reload()
        page.get_by_role("button", name="Try again", exact=True).wait_for()
        assert "unavailable" in page.locator("#collection-status").inner_text()
        page.unroute("**/api/collection")
        page.get_by_role("button", name="Try again", exact=True).click()
        page.get_by_text("Your collection is empty.", exact=False).wait_for()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path="/tmp/cinemood-collection-mobile.png", full_page=True)
        page.get_by_role("link", name="Discover", exact=True).click()
        page.set_viewport_size({"width": 1280, "height": 1000})
        search("quiet comfort")
        finished()
        page.screenshot(path="/tmp/cinemood-stream-desktop.png", full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path="/tmp/cinemood-stream-mobile.png", full_page=True)

        # Inline details keep the same interaction on mobile, without an overlay.
        mobile_action = page.locator("#results .details-action").first
        mobile_action.click()
        assert page.locator("#results article.is-expanded .movie-details").is_visible()
        assert page.locator("dialog").count() == 0
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path="/tmp/cinemood-details-mobile.png", full_page=True)
        page.keyboard.press("Escape")
        assert mobile_action.evaluate("(el) => el === document.activeElement")
        assert page.locator("#results article.is-expanded").count() == 0
        search("invalid evidence")
        finished()
        assert page.locator(".explanation-text").all_text_contents() == ["", "", "", ""]
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
        assert page.locator("#results article").count() == 4
        assert page.locator(".explanation-text").all_text_contents() == ["", "", "", ""]
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
        assert page.locator("#results article").count() == 4
        assert page.locator(".explanation-text").all_text_contents() == ["", "", "", ""]
        assert "interrupted" in page.locator("#status").inner_text()
        page.unroute("**/api/recommendations/stream")
        search("provider failure")
        finished()
        assert page.locator("#results article").count() == 4
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
