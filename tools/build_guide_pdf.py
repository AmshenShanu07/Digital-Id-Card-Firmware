#!/usr/bin/env python3
"""Build docs/Digital-ID-Card-Guide.pdf from docs/guide/guide.html.

Inlines docs/circuit_diagram.svg into the page, then prints it to PDF with
headless Chrome or Edge (must be installed; internet is needed for web fonts).

Usage:
    python tools/build_guide_pdf.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "docs" / "guide" / "guide.html"
SVG = ROOT / "docs" / "circuit_diagram.svg"
PDF = ROOT / "docs" / "Digital-ID-Card-Guide.pdf"

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "microsoft-edge",
]


def find_browser() -> str:
    for candidate in BROWSERS:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit("No Chrome/Edge found. Install one or open guide.html and print it to PDF.")


def main() -> None:
    svg = SVG.read_text()
    html = HTML.read_text().replace("<!--DIAGRAM-->", svg)

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "guide.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                find_browser(),
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={PDF}",
                page.as_uri(),
            ],
            check=True,
        )
    print(f"Wrote {PDF}")


if __name__ == "__main__":
    main()
