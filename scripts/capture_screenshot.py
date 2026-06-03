"""Regenerate docs/assets/screenshot-dashboard.png.

Run this after changing html_report.py layout or CSS:

    python scripts/capture_screenshot.py

Requires: pip install playwright && python -m playwright install chromium
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).parent.parent.resolve()
    out_dir = Path(tempfile.mkdtemp())

    print("Generating HTML report from examples/sample-ai-app …")
    subprocess.run(
        [
            sys.executable, "-m", "aibom_guard.cli", "all",
            str(repo_root / "examples" / "sample-ai-app"),
            "--name", "Hiring Assistant",
            "--use-case", "resume screening and candidate ranking with biometric face recognition",
            "--html", "-o", str(out_dir),
        ],
        check=True,
    )

    html_path = out_dir / "compliance_report.html"
    asset_path = repo_root / "docs" / "assets" / "screenshot-dashboard.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Screenshotting {html_path} …")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed. Run: pip install playwright && python -m playwright install chromium")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"file://{html_path.resolve()}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(asset_path), full_page=False)
        browser.close()

    size = asset_path.stat().st_size
    print(f"Saved {asset_path} ({size // 1024} KB)")
    print("Commit the PNG: git add docs/assets/screenshot-dashboard.png")


if __name__ == "__main__":
    main()
