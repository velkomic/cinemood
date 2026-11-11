"""Accepted card/collection seam: real DOM, controlled HTTP, no providers."""

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
movie = dict(json.loads((ROOT / "fixtures/movies.json").read_text())[0], id=1)


class Static(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "cinemood/static"), **kwargs)

    def do_GET(self):
        self.path = self.path.removeprefix("/static")
        super().do_GET()

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Static)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/api/**", lambda route: route.fulfill(status=404))
        held_posters = []
        poster_pattern = "**/api/movies/*/poster"
        page.route(poster_pattern, lambda route: held_posters.append(route))
        page.goto(base + "/style.css")
        page.set_content("""<button id="fallback">Fallback</button>
            <div id="one"></div><div id="two"></div>""")
        page.add_script_tag(url=base + "/ui.js")
        page.evaluate(
            """movie => {
            window.movie = movie;
            const options = {context: 'recommendations',
                onCollectionAction: () => {},
                readCollectionState: () => ({saved: false, pending: false, error: ''}),
                focusFallback: document.querySelector('#fallback')};
            window.one = createMovieCardGroup({...options,
                container: document.querySelector('#one')});
            window.two = createMovieCardGroup({...options,
                container: document.querySelector('#two')});
            window.oldUpdate = one.replace([movie]);
            two.replace([movie]);
        }""",
            movie,
        )
        page.locator("#one .details-action").click()
        page.locator("#two .details-action").click()
        expect(page.locator(".is-expanded")).to_have_count(1)
        page.evaluate("one.replace([movie])")
        expect(page.locator("#two .movie")).to_have_class("movie is-expanded")
        page.locator("#one .details-action").click()
        page.evaluate(
            "one.replace([movie]); oldUpdate(1, {phase: 'complete', text: 'STALE'})"
        )
        expect(page.locator("#fallback")).to_be_focused()
        expect(page.locator(".is-expanded")).to_have_count(0)
        expect(page.locator("#one")).not_to_contain_text("STALE")
        page.evaluate("""() => {
            // A late poster callback must also respect the disposed display.
            window.oldPoster = document.querySelector('#one .poster');
            window.oldImage = document.querySelector('#one img');
        }""")
        page.evaluate("""() => {
            one.setCollectionState(1, {saved: true, pending: false, error: ''});
            one.dispose();
            oldUpdate(1, {phase: 'complete', text: 'DISPOSED'});
        }""")
        expect(page.locator("#one .movie")).to_have_count(0)
        page.evaluate("oldImage.dispatchEvent(new Event('load'))")
        assert not page.evaluate("oldPoster.classList.contains('has-image')")
        page.evaluate("""() => {
            window.update = two.replace([movie, {...movie, id: 2}, {...movie, id: 3}]);
            update(1, {phase: 'tentative', text: '<img src=x onerror=alert(1)>'});
        }""")
        expect(page.locator("#two .explanation-text").first).to_have_text(
            "<img src=x onerror=alert(1)>"
        )
        expect(page.locator("#two .explanation-text img")).to_have_count(0)
        page.locator('#two [data-movie-id="2"] .poster-button').focus()
        page.evaluate("two.remove(2)")
        expect(page.locator('#two [data-movie-id="3"] .poster-button')).to_be_focused()
        page.evaluate("two.remove(3)")
        expect(page.locator('#two [data-movie-id="1"] .poster-button')).to_be_focused()
        page.evaluate("two.remove(1); update(1, {phase: 'complete', text: 'REMOVED'})")
        expect(page.locator("#fallback")).to_be_focused()
        expect(page.locator("#two .movie")).to_have_count(0)
        for route in held_posters:
            route.abort()
        page.unroute(poster_pattern)
        assert not errors, errors
        held_loads = []
        held_mutations = []
        hold_loads = False
        requests = []

        def collection_http(route):
            if route.request.method == "GET":
                if hold_loads:
                    held_loads.append(route)
                else:
                    route.fulfill(json={"movies": []})
            else:
                requests.append(route.request.method)
                held_mutations.append(route)

        page.route("**/api/collection**", collection_http)
        page.goto(base + "/collection.html")
        expect(page.locator("#collection-status")).to_contain_text("empty")
        page.evaluate(
            """movie => {
            window.movie = movie;
            for (const id of ['copies', 'other']) {
                const container = document.createElement('div');
                container.id = id;
                document.body.append(container);
                window[id] = createCollectionCardGroup(container, 'recommendations',
                    document.querySelector('#collection-status'));
                window[id].replace([movie]);
            }
        }""",
            movie,
        )
        page.locator("#copies .save-action").click()
        expect(page.locator("#other .save-action")).to_have_text("Saving…")
        expect(page.locator("#other .save-action")).to_be_disabled()
        page.evaluate("""() => {
            const save = document.querySelector('#other .save-action');
            save.dispatchEvent(new Event('click'));
            copies.dispose();
            window.oldSave = save;
            other.replace([movie]);
        }""")
        expect(page.locator("#copies .movie")).to_have_count(0)
        expect(page.locator("#other .save-action")).to_have_text("Saving…")
        page.wait_for_timeout(100)
        assert requests == ["PUT"], requests
        assert len(held_mutations) == 1
        held_mutations.pop().fulfill(status=204)
        expect(page.locator("#other .save-action")).to_have_text("Saved")
        assert page.evaluate("oldSave.textContent") == "Saving…"

        # An old reload overlapping removal cannot resurrect membership.
        hold_loads = True
        reload = """window.dispatchEvent(
            new PageTransitionEvent('pageshow', {persisted: true}))"""
        page.evaluate(reload)
        page.wait_for_timeout(100)
        assert len(held_loads) == 1
        held_loads.pop().fulfill(json={"movies": [movie]})
        expect(page.locator("#collection-results .movie")).to_have_count(1)
        page.locator("#collection-results .details-action").click()
        page.evaluate(reload)
        page.wait_for_timeout(100)
        assert len(held_loads) == 1
        page.locator("#collection-results .save-action").click()
        expect(page.locator("#other .save-action")).to_have_text("Saving…")
        held_loads.pop().fulfill(json={"movies": [movie]})
        page.locator("#other .details-action").click()
        page.wait_for_timeout(100)
        assert len(held_mutations) == 1
        held_mutations.pop().fulfill(status=204)
        expect(page.locator("#collection-results .movie")).to_have_count(0)
        expect(page.locator("#other .details-action")).to_be_focused()
        expect(page.locator("#other .movie")).to_have_class("movie is-expanded")
        page.wait_for_timeout(100)
        expect(page.locator("#collection-results .movie")).to_have_count(0)
        assert len(held_loads) == 1
        held_loads.pop().fulfill(json={"movies": []})
        expect(page.locator("#collection-status")).to_contain_text("empty")
        expect(page.locator("#other .save-action")).to_have_text("Save")
        page.wait_for_timeout(100)
        assert not held_loads
        # A reload begun during a pending removal must be discarded even when
        # its response arrives after the successful DELETE.
        page.evaluate(reload)
        page.wait_for_timeout(100)
        held_loads.pop().fulfill(json={"movies": [movie]})
        expect(page.locator("#collection-results .movie")).to_have_count(1)
        page.locator("#collection-results .save-action").click()
        page.wait_for_timeout(100)
        assert len(held_mutations) == 1
        page.evaluate("""() => {
            const container = document.createElement('div');
            container.id = 'removal-copy';
            document.body.append(container);
            window.removalCopy = createCollectionCardGroup(container, 'collection',
                document.querySelector('#collection-status'));
            removalCopy.replace([movie]);
            removalCopy.replace([movie]);
        }""")
        expect(page.locator("#removal-copy .save-action")).to_have_text("Removing…")
        page.evaluate(reload)
        page.wait_for_timeout(100)
        assert len(held_loads) == 1
        held_mutations.pop().fulfill(status=204)
        expect(page.locator("#collection-results .movie")).to_have_count(0)
        expect(page.locator("#removal-copy .movie")).to_have_count(0)
        expect(page.locator("#collection-status")).to_be_focused()
        held_loads.pop().fulfill(json={"movies": [movie]})
        page.wait_for_timeout(100)
        expect(page.locator("#collection-results .movie")).to_have_count(0)
        assert len(held_loads) == 1
        held_loads.pop().fulfill(json={"movies": []})
        expect(page.locator("#collection-status")).to_contain_text("empty")

        # Only the latest requested reload may replace the current display.
        page.evaluate(reload)
        page.wait_for_timeout(100)
        page.evaluate(reload)
        held_loads.pop().fulfill(json={"movies": [movie]})
        page.wait_for_timeout(100)
        expect(page.locator("#collection-results .movie")).to_have_count(0)
        assert len(held_loads) == 1  # Web Locks serialized the next GET
        held_loads.pop().fulfill(json={"movies": []})
        expect(page.locator("#collection-status")).to_contain_text("empty")
        page.wait_for_timeout(100)
        assert not held_loads
        assert not errors, errors
        page.evaluate("""() => {
            window.copies = createCollectionCardGroup(
                document.querySelector('#copies'), 'spotlight',
                document.querySelector('#collection-status'));
            copies.replace([movie]);
        }""")
        page.locator("#copies .save-action").click()
        page.wait_for_timeout(100)
        held_mutations.pop().fulfill(status=503, json={"detail": "Try again"})
        expect(page.locator("#copies .save-feedback")).to_have_text("Try again")
        expect(page.locator("#other .save-feedback")).to_have_text("Try again")
        page.locator("#other .save-action").click()
        expect(page.locator("#copies .save-feedback")).to_have_text("")
        page.wait_for_timeout(100)
        held_mutations.pop().fulfill(status=204)
        expect(page.locator("#copies .save-action")).to_have_text("Saved")
        expect(page.locator("#other .save-action")).to_have_text("Saved")
        held_previews = []
        hold_loads = False
        page.route(
            "**/api/catalog-preview?*", lambda route: held_previews.append(route)
        )
        page.goto(base + "/index.html")
        held_previews.pop().fulfill(json={"movies": [movie], "has_more": True})
        expect(page.locator("#preview-track .movie")).to_have_count(1)
        page.evaluate(reload)
        page.wait_for_timeout(100)
        page.locator("#preview-track .poster-button").focus()
        held_previews.pop().fulfill(json={"movies": [movie], "has_more": False})
        expect(page.locator("#request")).to_be_focused()
        held_searches = []
        page.route(
            "**/api/recommendations/stream", lambda route: held_searches.append(route)
        )
        page.locator("#request").fill("A hopeful film")
        page.locator("#request").press("Enter")
        page.locator("#preview-track .details-action").click()
        page.wait_for_timeout(100)
        result = {"movies": [movie], "message": "Matches", "suggestions": []}
        stream = "".join(
            f"event: {event}\ndata: "
            + json.dumps({**data, "sequence": index, "request_id": "cards"})
            + "\n\n"
            for index, (event, data) in enumerate(
                [("result", result), ("complete", {})], 1
            )
        )
        held_searches.pop().fulfill(content_type="text/event-stream", body=stream)
        expect(page.locator("#results .movie")).to_have_count(1)
        expect(page.locator("#request")).to_be_focused()
        expect(page.locator("#preview-track .is-expanded")).to_have_count(0)
        assert not errors, errors
        browser.close()
    print("Card lifecycle browser checks passed")
finally:
    server.shutdown()
    server.server_close()
