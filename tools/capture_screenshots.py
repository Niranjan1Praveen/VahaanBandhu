"""Capture screenshots of the actually-running local application.

Every screenshot comes from a real page load against localhost. Nothing here
constructs an image; if a page fails to render, that is reported rather than
skipped, because a missing screenshot is information.

Console errors and failed network requests are collected per page so visual
regressions and runtime errors surface together.

    python tools/capture_screenshots.py --checkpoint 04-farmer
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "artifacts" / "screenshots"
WEB = "http://localhost:3000"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},    # iPhone 14 class
    "mobile-sm": {"width": 360, "height": 780},  # common budget Android
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}

# (checkpoint, name, path, dev_user, viewports)
PAGES = [
    ("01-landing", "landing", "/", None, ["desktop", "mobile"]),
    # The two-path entry screen: Login with Clerk / Show Demo.
    ("02-auth", "signin", "/signin", None,
     ["desktop", "mobile", "mobile-sm", "tablet"]),
    # The demo role selector reached from Show Demo.
    ("02-auth", "demo-role-selector", "/demo", None,
     ["desktop", "mobile", "mobile-sm", "tablet"]),
    ("03-role", "role-selection", "/app/role", "dev_farmer_01", ["desktop", "mobile"]),
    ("04-farmer", "farmer-dashboard", "/app/farmer", "dev_farmer_01",
     ["desktop", "mobile", "mobile-sm", "tablet"]),
    ("05-trucker", "trucker-dashboard", "/app/trucker", "dev_trucker_01",
     ["desktop", "mobile", "tablet"]),
    ("06-dealer", "dealer-dashboard", "/app/dealer", "dev_dealer_01",
     ["desktop", "mobile", "tablet"]),
    # Map views. Same component, role-appropriate geometry.
    ("07-map", "map-farmer", "/app/map", "dev_farmer_01", ["desktop", "mobile"]),
    ("07-map", "map-trucker", "/app/map", "dev_trucker_01", ["desktop", "mobile"]),
    ("07-map", "map-dealer", "/app/map", "dev_dealer_01", ["desktop", "mobile"]),
]


# Pages captured in both languages, to prove the toggle actually switches
# rather than merely rendering a button.
LANG_VARIANTS = {"landing", "signin", "demo-role-selector", "farmer-dashboard"}


def capture(checkpoint_filter: str | None = None, lang: str | None = None) -> dict:
    SHOTS.mkdir(parents=True, exist_ok=True)
    report: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for checkpoint, name, path, dev_user, viewports in PAGES:
            if checkpoint_filter and checkpoint != checkpoint_filter:
                continue
            out_dir = SHOTS / checkpoint
            out_dir.mkdir(parents=True, exist_ok=True)

            for vp in viewports:
                ctx = browser.new_context(
                    viewport=VIEWPORTS[vp],
                    device_scale_factor=2,
                    locale="hi-IN",
                )
                page = ctx.new_page()

                console_errors: list[str] = []
                failed_requests: list[str] = []
                page.on("console", lambda m: (
                    console_errors.append(m.text) if m.type == "error" else None))
                page.on("requestfailed", lambda r: failed_requests.append(
                    f"{r.method} {r.url} :: {r.failure}"))

                entry = {"checkpoint": checkpoint, "name": name, "path": path,
                         "viewport": vp, "dev_user": dev_user}
                try:
                    # Seed the dev identity before the app boots, so the session
                    # provider picks it up on first render.
                    if dev_user or lang:
                        page.goto(f"{WEB}/", wait_until="domcontentloaded")
                        if dev_user:
                            page.evaluate(
                                "u => localStorage.setItem('vb_dev_user', u)", dev_user)
                        if lang:
                            page.evaluate(
                                "l => localStorage.setItem('vb_lang', l)", lang)

                    page.goto(f"{WEB}{path}", wait_until="networkidle", timeout=45000)
                    # Let client fetches settle; these pages load data on mount.
                    page.wait_for_timeout(6000 if "map" in name else 2500)

                    suffix = f"--{lang}" if lang else ""
                    fname = f"{name}{suffix}--{vp}.png"
                    # Viewport-only on mobile. A full-page capture renders the
                    # `position: fixed` bottom nav at its viewport offset, which
                    # makes it appear stranded mid-page in the image -- a
                    # screenshot artefact, not a layout bug, but a misleading one.
                    full_page = not vp.startswith("mobile")
                    page.screenshot(path=str(out_dir / fname), full_page=full_page)
                    entry.update({
                        "status": "ok",
                        "file": str((out_dir / fname).relative_to(ROOT)),
                        "console_errors": console_errors[:5],
                        "failed_requests": failed_requests[:5],
                        "title": page.title(),
                    })
                    print(f"  ✓ {checkpoint}/{fname}"
                          f"{'  [console errors: %d]' % len(console_errors) if console_errors else ''}")
                except Exception as e:
                    entry.update({"status": "failed", "error": f"{type(e).__name__}: {e}"})
                    print(f"  ✗ {checkpoint}/{name}--{vp}: {e}")
                finally:
                    report.append(entry)
                    ctx.close()
        browser.close()

    index = SHOTS / "index.json"
    index.write_text(json.dumps({
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "web": WEB, "entries": report,
    }, indent=2), encoding="utf-8")
    return {"count": len(report), "index": str(index)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--lang", default=None, choices=["hi", "en"],
                    help="capture in a specific language")
    a = ap.parse_args()
    out = capture(a.checkpoint, a.lang)
    print(f"\n{out['count']} screenshots -> {SHOTS}")


if __name__ == "__main__":
    main()
