"""UI states through HTTP fixtures; run with Python + Playwright, no live models."""

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".impeccable/review/ui-refinements"
OUT.mkdir(parents=True, exist_ok=True)
fixture = json.loads((ROOT / "fixtures/movies.json").read_text())
movies = []
for index in range(12):
    movie = dict(fixture[index % len(fixture)])
    movie.update(
        id=index + 1,
        source_id=f"tmdb:{90000 + index}",
        title=(movie["title"] if index < 4 else f"{movie['title']} · Test {index + 1}"),
    )
    movies.append(movie)


class Static(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "cinemood/static"), **kwargs)

    def do_GET(self):
        self.path = (
            "/collection.html"
            if self.path == "/collection"
            else self.path.removeprefix("/static")
        )
        super().do_GET()

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Static)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
parsed = dict(
    included_genres=[],
    excluded_genres=[],
    runtime_minutes=None,
    runtime_operator=None,
    year_min=None,
    year_max=None,
    original_languages=[],
    semantic_query="UI verification fixtures",
    unsupported_requirements=[],
    clarification=[],
)
saved = set()
searches = []
preview_calls = []
fail_save = False
fail_preview = False
held_saves = []
hold_save = False


def handle(route):
    global fail_save
    path = urlsplit(route.request.url).path
    if path.endswith("/poster"):
        identity = int(path.split("/")[-2])
        if identity == 3:
            route.fulfill(status=404, content_type="application/json", body="{}")
            return
        colors = ["#a9b6d4", "#b9cba9", "#a1cbd1", "#e3bd85"]
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450">
        <rect width="300" height="450" fill="{colors[identity % 4]}"/>
        <rect x="30" y="110" width="240" height="3" fill="#142338"/>
        <text x="30" y="70" fill="#142338"
          font-family="sans-serif" font-size="18">UI TEST POSTER</text>
        <text x="30" y="350" fill="#142338"
          font-family="sans-serif" font-size="28">Film {identity}</text>
        <text x="30" y="390" fill="#142338" font-family="sans-serif"
          font-size="14">Synthetic fixture artwork</text></svg>'''
        route.fulfill(status=200, content_type="image/svg+xml", body=svg)
    elif path == "/api/catalog-preview":
        query = parse_qs(urlsplit(route.request.url).query)
        excluded = {int(i) for i in query.get("exclude", [])}
        preview_calls.append(excluded)
        if fail_preview:
            route.fulfill(status=503, content_type="application/json", body="{}")
        else:
            batch = [m for m in movies if m["id"] not in excluded][:5]
            route.fulfill(json={"movies": batch, "has_more": True})
    elif path == "/api/collection":
        route.fulfill(json={"movies": [m for m in movies if m["id"] in saved]})
    elif path.startswith("/api/collection/"):
        if hold_save:
            held_saves.append(route)
        elif fail_save:
            route.fulfill(
                status=503, json={"detail": "Unable to save. Please try again."}
            )
        else:
            identity = int(path.rsplit("/", 1)[1])
            saved.add(identity) if route.request.method == "PUT" else saved.discard(
                identity
            )
            route.fulfill(status=204)
    elif path == "/api/recommendations/stream":
        request = route.request.post_data_json["request"]
        searches.append(request)
        count = int(request.split(":")[-1]) if request.startswith("count:") else 5
        chosen = movies[:count]
        events = [
            (
                "result",
                {
                    "movies": chosen,
                    "original_request": request,
                    "interpretation": parsed,
                    "status": "matches" if count else "no_match",
                    "message": "No movies match. Edit your request."
                    if not count
                    else "UI verification fixtures",
                    "suggestions": [],
                },
            )
        ]
        for movie in chosen:
            events.append(
                (
                    "explanation_complete",
                    {
                        "movie_id": movie["id"],
                        "text": (
                            "Shared work brings unlikely friends together, connecting "
                            "the story to a request about friendship and starting over."
                        ),
                    },
                )
            )
        events.append(("complete", {}))
        body = "".join(
            f"event: {name}\ndata: "
            + json.dumps({**data, "request_id": "ux-test", "sequence": i + 1})
            + "\n\n"
            for i, (name, data) in enumerate(events)
        )
        route.fulfill(status=200, content_type="text/event-stream", body=body)
    else:
        route.abort()


try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768}, reduced_motion="reduce"
        )
        context.route("**/api/**", handle)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base, wait_until="networkidle")
        assert page.locator(".preview-film").count() == 5
        first = page.locator(".preview-film").evaluate_all(
            "(els)=>els.map(el=>el.dataset.movieId)"
        )
        page.screenshot(path=str(OUT / "spotlight-desktop.png"), full_page=True)
        page.get_by_role("button", name="Shuffle films").click()
        page.wait_for_function(
            'document.querySelector("#preview-track").getAttribute("aria-busy")==="false"'
        )
        second = page.locator(".preview-film").evaluate_all(
            "(els)=>els.map(el=>el.dataset.movieId)"
        )
        assert set(first).isdisjoint(second)
        fail_preview = True
        page.get_by_role("button", name="Shuffle films").click()
        page.get_by_text("Preview unavailable.", exact=False).wait_for()
        assert second == page.locator(".preview-film").evaluate_all(
            "(els)=>els.map(el=>el.dataset.movieId)"
        )
        fail_preview = False
        page.get_by_role("link", name="My collection", exact=True).click()
        page.get_by_role("link", name="Discover", exact=True).click()
        page.locator(".preview-film").first.wait_for()
        assert set(second).isdisjoint(
            page.locator(".preview-film").evaluate_all(
                "(els)=>els.map(el=>el.dataset.movieId)"
            )
        )
        page.evaluate(
            'window.dispatchEvent(new PageTransitionEvent("pageshow",{persisted:true}))'
        )
        page.wait_for_function(
            'document.querySelector("#preview-track").getAttribute("aria-busy")==="false"'
        )
        assert len(preview_calls) >= 5
        field = page.locator("#request")
        field.fill("First line\nSecond line\nThird line")
        assert field.evaluate("(el)=>el.clientHeight >= el.scrollHeight - 2"), (
            "Multiline requests must grow without hiding entered lines"
        )
        field.fill("UI verification fixtures")
        field.press("Shift+Enter")
        assert field.input_value().endswith("\n") and not searches
        assert (
            page.locator(".request-band").evaluate(
                "(el)=>getComputedStyle(el).outlineStyle"
            )
            == "none"
        )
        assert field.evaluate("(el)=>getComputedStyle(el).outlineStyle") == "none"
        field.press("Enter")
        page.locator("#results .movie").nth(4).wait_for()
        assert searches == ["UI verification fixtures"]
        assert page.locator("#results .movie").count() == 5
        # Mouse submission must exercise the same path as Enter, including retry.
        page.get_by_role("button", name="Find movies", exact=True).click()
        page.wait_for_function(
            'document.querySelector("#results").getAttribute("aria-busy")==="false"'
        )
        assert searches == ["UI verification fixtures"] * 2
        assert page.locator("#results .movie").count() == 5
        assert page.get_by_role("button", name="Find movies", exact=True).is_enabled()
        assert page.locator("#results .movie-actions").evaluate_all(
            "(els)=>els.every(el=>el.getBoundingClientRect().bottom<=innerHeight)"
        )
        page.screenshot(path=str(OUT / "five-desktop.png"), full_page=True)
        xs = page.locator("#results article").evaluate_all(
            "(els)=>els.map(el=>el.getBoundingClientRect().x)"
        )
        page.locator("#results .poster-button").first.click()
        assert page.locator("#results .movie.is-expanded").count() == 1
        link = page.locator("#results .movie.is-expanded .tmdb-link")
        assert link.get_attribute("href") == "https://www.themoviedb.org/movie/90000"
        assert "noopener" in link.get_attribute("rel")
        assert xs == page.locator("#results article").evaluate_all(
            "(els)=>els.map(el=>el.getBoundingClientRect().x)"
        )
        synopsis = page.locator("#results .movie.is-expanded .synopsis")
        synopsis.evaluate(
            "(el)=>el.textContent = 'A long catalog synopsis. '.repeat(80)"
        )
        assert synopsis.evaluate("(el)=>el.scrollHeight > el.clientHeight")
        synopsis.focus()
        page.keyboard.press("End")
        page.wait_for_function(
            'document.querySelector("#results .is-expanded .synopsis").scrollTop > 0'
        )
        page.screenshot(path=str(OUT / "details-desktop.png"), full_page=True)
        page.locator("#results .details-action").nth(1).click()
        assert (
            page.locator("#results .movie.is-expanded").get_attribute("data-movie-id")
            == "2"
        )
        page.keyboard.press("Escape")
        assert page.locator("#results .movie.is-expanded").count() == 0
        assert (
            page.locator("#results .details-action")
            .nth(1)
            .evaluate("(el)=>el===document.activeElement")
        )
        fail_save = True
        save = page.locator("#results .save-action").first
        save.click()
        page.get_by_text("Unable to save. Please try again.", exact=True).wait_for()
        assert not save.is_disabled()
        page.screenshot(path=str(OUT / "save-error.png"), full_page=True)
        fail_save = False
        hold_save = True
        save_width = save.bounding_box()["width"]
        save.click()
        page.get_by_role("button", name="Saving…", exact=True).wait_for()
        assert save.get_attribute("aria-busy") == "true"
        assert abs(save.bounding_box()["width"] - save_width) < 1, (
            "Save must not resize while pending"
        )
        hold_save = False
        saved.add(1)
        held_saves.pop().fulfill(status=204)
        page.get_by_role("button", name="Saved to collection", exact=True).wait_for()
        assert (
            page.locator("#results .save-action").first.get_attribute("aria-pressed")
            == "true"
        )
        for count in [1, 2, 3, 4, 0]:
            field.fill(f"count:{count}")
            field.press("Enter")
            page.wait_for_function(
                '!document.querySelector("#discover button").disabled'
            )
            assert page.locator("#results .movie").count() == count
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if count in [1, 2, 0]:
                page.screenshot(path=str(OUT / f"count-{count}.png"), full_page=True)
        field.fill("UI verification fixtures")
        field.press("Enter")
        page.locator("#results .movie").nth(4).wait_for()
        for width, height in [
            (1280, 720),
            (1024, 768),
            (768, 1024),
            (390, 844),
            (320, 720),
        ]:
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth"
            ), width
            if width == 1280:
                assert page.locator("#results .movie-actions").evaluate_all(
                    "(els)=>els.every(el=>el.getBoundingClientRect().bottom<=innerHeight)"
                )
            if width == 390:
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(OUT / "mobile.png"), full_page=True)
                page.locator("#results .details-action").first.click()
                assert page.locator(
                    "#results .movie.is-expanded .movie-details"
                ).is_visible()
                assert page.locator("dialog").count() == 0
                page.screenshot(path=str(OUT / "details-mobile.png"), full_page=True)
                page.keyboard.press("Escape")
        page.get_by_role("link", name="Discover", exact=True).click()
        page.locator(".preview-film").first.wait_for()
        page.set_viewport_size({"width": 390, "height": 844})
        spotlight = page.locator(".preview-film").first
        spotlight.locator(".poster-button").click()
        assert spotlight.locator(".movie-details").bounding_box()["width"] > 300
        assert spotlight.locator(".save-action").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(OUT / "spotlight-mobile.png"), full_page=True)
        page.emulate_media(reduced_motion="no-preference")
        page.mouse.move(380, 400)
        page.locator("#request").evaluate("el => el.blur()")
        page.evaluate("document.activeElement.blur(); scrollTo(0, 450)")
        page.wait_for_function(
            "document.querySelector('.site-header').getBoundingClientRect().bottom <= 1"
        )
        page.mouse.move(150, 5)
        page.wait_for_function(
            "document.querySelector('.site-header').getBoundingClientRect().top >= 0"
        )
        page.mouse.move(380, 400)
        page.evaluate("scrollTo(0, 650)")
        page.wait_for_function(
            "document.querySelector('.site-header').classList.contains('is-hidden')"
        )
        page.evaluate("scrollTo(0, 550)")
        page.wait_for_function(
            "!document.querySelector('.site-header').classList.contains('is-hidden')"
        )
        page.evaluate("scrollTo(0, 750)")
        page.wait_for_function(
            "document.querySelector('.site-header').classList.contains('is-hidden')"
        )
        page.locator(".brand").focus()
        page.wait_for_function(
            "document.querySelector('.site-header').getBoundingClientRect().top >= 0"
        )
        page.emulate_media(reduced_motion="reduce")
        page.get_by_role("link", name="My collection", exact=True).click()
        page.locator("#collection-results .movie").first.wait_for()
        assert page.locator("#collection-results").get_attribute("data-count") == "1"
        page.locator("#collection-results .details-action").first.click()
        page.evaluate(
            'window.dispatchEvent(new PageTransitionEvent("pageshow",{persisted:true}))'
        )
        page.wait_for_function(
            'document.querySelector("#collection-results").getAttribute("aria-busy")==="false"'
        )
        page.locator("#collection-results .details-action").first.click()
        assert page.locator("#collection-results .movie.is-expanded").count() == 1
        assert not errors, errors
        (OUT / "evidence.json").write_text(
            json.dumps(
                {
                    "passed": True,
                    "javascript_errors": errors,
                    "screenshots": (
                        "Synthetic HTTP fixtures and geometric test posters; "
                        "not live recommendations."
                    ),
                    "spotlight_requests": len(preview_calls),
                    "searches": len(searches),
                },
                indent=2,
            )
            + "\n"
        )
        browser.close()
finally:
    server.shutdown()
    server.server_close()
