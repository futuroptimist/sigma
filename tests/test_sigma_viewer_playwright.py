"""End-to-end coverage for the Sigma S1 Three.js viewer using Playwright."""

from __future__ import annotations

import importlib.util
import math
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest

if importlib.util.find_spec("pytest_playwright") is None:  # pragma: no cover
    pytest.skip(
        "pytest-playwright plugin is required for viewer tests",
        allow_module_level=True,
    )

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page, sync_playwright
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    pytest.skip(
        "Playwright is required for viewer tests",
        allow_module_level=True,
    )
else:
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except PlaywrightError as exc:  # pragma: no cover - environment dependent
        message = str(exc)
        if "missing dependencies" in message:
            pytest.skip(
                "Playwright browser dependencies missing; install via "
                "`playwright install-deps`.",
                allow_module_level=True,
            )
        raise

from pytest_playwright.pytest_playwright import (  # isort: skip
    browser_context_args as _playwright_browser_context_args,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWER_PATH = REPO_ROOT / "docs" / "sigma-s1-viewer.html"
VIEWER_HANDLE_SCRIPT = "() => window.__sigmaViewer !== undefined"
VIEWER_READY_SCRIPT = "() => window.__sigmaViewer?.ready === true"
MESH_COUNT_SCRIPT = (
    "() => window.__sigmaViewer.scene.children.filter("  # noqa: E501
    "child => child.type === 'Mesh').length"
)
CAMERA_STATE_SCRIPT = "() => window.__sigmaViewer.getCameraState()"
RENDERER_SIZE_SCRIPT = "() => window.__sigmaViewer.getRendererSize()"


@pytest.fixture(scope="session")
def static_file_server() -> Iterator[str]:
    """Serve the repository over HTTP so the viewer can fetch the STL asset."""

    handler = partial(SimpleHTTPRequestHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture
def browser_context_args(
    pytestconfig: pytest.Config,
    playwright: Any,
    device: str | None,
    base_url: str | None,
    _pw_artifacts_folder: Any,
) -> dict:
    """Allow Playwright to load CDN assets served over HTTPS."""

    base_args = _playwright_browser_context_args.__wrapped__(
        pytestconfig, playwright, device, base_url, _pw_artifacts_folder
    )
    return {**base_args, "ignore_https_errors": True}


@pytest.mark.playwright
@pytest.mark.skipif(
    not VIEWER_PATH.is_file(),
    reason="sigma viewer HTML missing",
)
def test_sigma_viewer_loads_and_interacts(
    page: Page,
    static_file_server: str,
) -> None:
    viewer_url = f"{static_file_server}/docs/sigma-s1-viewer.html"

    console_messages: list[str] = []
    page.on(
        "console",
        lambda msg: console_messages.append(f"{msg.type}: {msg.text}"),
    )

    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(viewer_url)

    page.wait_for_function(VIEWER_HANDLE_SCRIPT, timeout=10_000)
    page.wait_for_function(VIEWER_READY_SCRIPT, timeout=20_000)
    if not page.evaluate("() => window.__sigmaViewer.error === null"):
        message = "Viewer reported an initialization error. "
        message += f"Console: {console_messages}"
        pytest.fail(message)

    mesh_count = page.evaluate(MESH_COUNT_SCRIPT)
    assert mesh_count >= 1

    initial_state = page.evaluate(CAMERA_STATE_SCRIPT)

    page.mouse.move(640, 360)
    page.mouse.down()
    page.mouse.move(740, 420, steps=20)
    page.mouse.up()
    page.wait_for_timeout(150)

    after_orbit = page.evaluate(CAMERA_STATE_SCRIPT)

    position_delta = math.dist(
        initial_state["position"],
        after_orbit["position"],
    )
    if position_delta <= 1.0:
        pytest.fail("Camera position did not change after orbit drag")

    page.mouse.wheel(0, -400)
    page.wait_for_timeout(150)

    after_zoom = page.evaluate(CAMERA_STATE_SCRIPT)
    if after_zoom["distance"] >= after_orbit["distance"]:
        pytest.fail("Zoom scroll did not move camera")

    page.set_viewport_size({"width": 960, "height": 540})
    page.wait_for_timeout(150)
    renderer_size = page.evaluate(RENDERER_SIZE_SCRIPT)
    assert renderer_size == {"width": 960, "height": 540}
