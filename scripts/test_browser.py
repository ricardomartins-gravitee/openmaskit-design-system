"""Synthetic browser acceptance; starts a temporary static server on loopback."""

import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=str(ROOT / "web"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    output = ROOT / ".runtime/browser"
    output.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            for engine in [playwright.chromium, playwright.webkit]:
                browser = engine.launch()
                for width in [375, 1024]:
                    page = browser.new_page(
                        viewport={"width": width, "height": 900},
                        reduced_motion="reduce",
                    )
                    errors = []
                    external = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on(
                        "request",
                        lambda request: (
                            external.append(request.url)
                            if not request.url.startswith(
                                f"http://127.0.0.1:{server.server_port}/"
                            )
                            else None
                        ),
                    )
                    page.goto(f"http://127.0.0.1:{server.server_port}/gallery.html")
                    assert page.title() == "OpenMaskit Design System"
                    assert (
                        page.locator("body").evaluate(
                            "el => getComputedStyle(el).backgroundColor"
                        )
                        == "rgb(10, 12, 16)"
                    )
                    assert (
                        page.locator(".om-panel").first.evaluate(
                            "el => getComputedStyle(el).borderRadius"
                        )
                        == "10px"
                    )
                    primary = page.get_by_role("button", name="Set Up OpenMaskit")
                    assert (
                        primary.evaluate("el => getComputedStyle(el).backgroundColor")
                        == "rgb(88, 166, 255)"
                    )
                    primary.hover()
                    assert (
                        primary.evaluate("el => getComputedStyle(el).backgroundColor")
                        == "rgb(121, 184, 255)"
                    )
                    # Real keyboard traversal establishes focus-visible rather than forcing a CSS state.
                    page.locator("body").click(position={"x": 2, "y": 2})
                    # Safari on macOS uses Option-Tab for all controls when the
                    # user's Keyboard Navigation setting is off.
                    key = (
                        "Alt+Tab"
                        if sys.platform == "darwin" and engine.name == "webkit"
                        else "Tab"
                    )
                    page.keyboard.press(key)
                    assert primary.evaluate("el => el === document.activeElement")
                    assert (
                        primary.evaluate("el => getComputedStyle(el).outlineStyle")
                        == "solid"
                    )
                    assert (
                        primary.evaluate(
                            "el => getComputedStyle(el).transitionDuration"
                        )
                        == "0s"
                    )
                    assert page.get_by_role("button", name="Unavailable").is_disabled()
                    assert (
                        page.get_by_role("button", name="Unavailable").evaluate(
                            "el => getComputedStyle(el).opacity"
                        )
                        == "0.42"
                    )
                    page.get_by_label("Name").fill("Synthetic test profile")
                    assert (
                        page.get_by_label("Name").input_value()
                        == "Synthetic test profile"
                    )
                    assert page.get_by_label("Analyser").input_value() == "Presidio"
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    assert not errors, errors
                    assert not external, external
                    page.screenshot(
                        path=str(output / f"{engine.name}-{width}.png"), full_page=True
                    )
                    page.close()
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print(
        "Chromium and WebKit: desktop/mobile layout, theme, keyboard, states and reduced motion passed."
    )


if __name__ == "__main__":
    main()
